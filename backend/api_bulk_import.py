#!/usr/bin/env python3
"""
API-based bulk import script for Herman Siu's W.W.H.D. content
Uses the existing document upload API to ensure consistency

Usage Examples:
  # Local development import
  python api_bulk_import.py --pdf-folder ./data/pdfs --metadata-file ./data/metadata.json

  # Production remote import
  python api_bulk_import.py \
    --pdf-folder ./herman_content/pdfs \
    --metadata-file ./herman_content/metadata.json \
    --api-url https://api.weshuber.com \
    --namespace general

  # With custom authentication token
  python api_bulk_import.py \
    --pdf-folder ./pdfs \
    --metadata-file ./metadata.json \
    --api-url https://api.weshuber.com \
    --api-token your_jwt_token_here
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp
import aiofiles
import logging
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIBulkImporter:
    def __init__(self, pdf_folder: str, metadata_file: str, api_base_url: str = "http://localhost:8000", api_token: str = None):
        """
        Initialize the API-based bulk importer

        Args:
            pdf_folder: Path to folder containing PDF files
            metadata_file: Path to JSON file with metadata
            api_base_url: Base URL for the API (default: localhost:8000)
            api_token: Authentication token (if None, will attempt to create one)
        """
        self.pdf_folder = Path(pdf_folder)
        self.metadata_file = Path(metadata_file)
        self.api_base_url = api_base_url.rstrip('/')
        self.api_token = api_token

        # Load metadata
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load metadata from JSON file"""
        if not self.metadata_file.exists():
            logger.warning(f"Metadata file not found: {self.metadata_file}")
            return {}

        with open(self.metadata_file, 'r') as f:
            data = json.load(f)

        # Create lookup by filename
        metadata_lookup = {}
        for item in data.get('videos', []):
            filename = item.get('filename', '')
            if filename:
                metadata_lookup[filename] = item
                # Also store without extension for matching
                name_without_ext = Path(filename).stem
                metadata_lookup[name_without_ext] = item

        return metadata_lookup

    def _get_file_metadata(self, pdf_file: Path) -> Dict:
        """Get metadata for a PDF file"""
        metadata = {}

        # Try exact filename match
        if pdf_file.name in self.metadata:
            metadata = self.metadata[pdf_file.name]
        # Try stem (filename without extension)
        elif pdf_file.stem in self.metadata:
            metadata = self.metadata[pdf_file.stem]
        else:
            # Try to extract from filename
            filename = pdf_file.stem
            if "Ep." in filename or "Ep " in filename:
                metadata = {
                    'title': filename,
                    'youtube_url': '',
                    'author': 'Herman Siu',
                    'is_transcript': True
                }
            else:
                metadata = {
                    'title': filename,
                    'youtube_url': '',
                    'author': 'Herman Siu'
                }

        return metadata

    async def _authenticate(self, session: aiohttp.ClientSession) -> str:
        """
        Authenticate with the API and get a token
        """
        if self.api_token:
            return self.api_token

        # Try to create a test user and get token
        try:
            # First, try to register a test user
            register_data = {
                "username": "test",
                "email": "test@example.com",
                "password": "testpassword",
                "full_name": "Test User"
            }

            async with session.post(f"{self.api_base_url}/api/v1/auth/register", json=register_data) as response:
                if response.status in [200, 201]:
                    logger.info("Successfully registered test user")
                elif response.status == 400:
                    # User might already exist, that's fine
                    logger.info("Test user already exists")
                else:
                    logger.warning(f"Registration response: {response.status}")

            # Now try to login using OAuth2 form data format
            login_data = aiohttp.FormData()
            login_data.add_field('username', 'bulk_import')
            login_data.add_field('password', 'bulk123')

            async with session.post(f"{self.api_base_url}/api/v1/auth/token", data=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get('access_token')
                    logger.info("Successfully authenticated and got token")
                    return token
                else:
                    error_text = await response.text()
                    logger.error(f"Login failed: {response.status} - {error_text}")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")

        # Fallback - return None to indicate failure
        logger.error("Could not authenticate with API")
        return None

    async def _upload_document(self, session: aiohttp.ClientSession, pdf_file: Path, metadata: Dict, namespace: str) -> bool:
        """
        Upload a single document using the API endpoint
        """
        headers = {
            'Authorization': f'Bearer {self.api_token}'
        }

        # Debug metadata
        logger.info(f"Metadata for {pdf_file.name}: {metadata}")

        # Prepare form data
        data = aiohttp.FormData()

        # Add file
        async with aiofiles.open(pdf_file, 'rb') as f:
            file_content = await f.read()
            data.add_field('file', file_content, filename=pdf_file.name, content_type='application/pdf')

        # Add metadata
        data.add_field('namespace', namespace)
        data.add_field('title', metadata.get('title', pdf_file.stem))

        if metadata.get('youtube_url'):
            data.add_field('youtube_url', metadata['youtube_url'])
            logger.info(f"Adding YouTube URL: {metadata['youtube_url']}")

        try:
            async with session.post(f"{self.api_base_url}/api/v1/documents/upload", data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✓ Uploaded via API: {pdf_file.name}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"✗ API upload failed for {pdf_file.name}: {response.status} - {error_text}")
                    return False

        except Exception as e:
            logger.error(f"✗ Exception uploading {pdf_file.name}: {e}")
            return False

    async def import_all(self, namespace: str = "general"):
        """Import all PDFs using the API"""
        logger.info(f"Starting API-based bulk import from {self.pdf_folder}")
        logger.info(f"Found {len(self.metadata)} metadata entries")
        logger.info(f"Target API: {self.api_base_url}")

        # Get all PDF files
        pdf_files = list(self.pdf_folder.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to import")

        # Track statistics
        success_count = 0
        error_count = 0

        async with aiohttp.ClientSession() as session:
            # Authenticate
            self.api_token = await self._authenticate(session)

            if not self.api_token:
                logger.error("Failed to authenticate with API")
                return

            # Process each PDF
            for pdf_file in pdf_files:
                try:
                    # Get metadata for this file
                    file_metadata = self._get_file_metadata(pdf_file)

                    # Upload via API
                    success = await self._upload_document(session, pdf_file, file_metadata, namespace)

                    if success:
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"✗ Failed to process {pdf_file.name}: {e}")
                    continue

        logger.info(f"""
API Import Complete!
===================
✓ Success: {success_count} documents
✗ Errors: {error_count} documents
Total processed: {len(pdf_files)} files
        """)

        # Verify the import by checking the API
        await self._verify_import(namespace)

    async def _verify_import(self, namespace: str):
        """Verify the import by querying the API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.api_token}'}

                async with session.get(f"{self.api_base_url}/api/v1/documents/?namespace={namespace}", headers=headers) as response:
                    if response.status == 200:
                        documents = await response.json()
                        logger.info(f"✓ API verification: {len(documents)} documents found in namespace '{namespace}'")
                    else:
                        logger.warning(f"Could not verify via API: {response.status}")

        except Exception as e:
            logger.error(f"API verification failed: {e}")


async def main():
    """Main function to run the API import"""
    import argparse

    parser = argparse.ArgumentParser(description='Bulk import PDFs via API to W.W.H.D. knowledge base')
    parser.add_argument('--pdf-folder', required=True, help='Folder containing PDF files')
    parser.add_argument('--metadata-file', required=True, help='JSON file with metadata')
    parser.add_argument('--namespace', default='general', help='Namespace for documents')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--api-token', help='API authentication token')

    args = parser.parse_args()

    # Create importer and run
    importer = APIBulkImporter(
        pdf_folder=args.pdf_folder,
        metadata_file=args.metadata_file,
        api_base_url=args.api_url,
        api_token=args.api_token
    )

    await importer.import_all(namespace=args.namespace)


if __name__ == "__main__":
    asyncio.run(main())