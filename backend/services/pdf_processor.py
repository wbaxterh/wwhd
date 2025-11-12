"""PDF processing service for extracting text from uploaded PDFs"""
import io
import logging
from typing import Union

logger = logging.getLogger(__name__)

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available. PDF processing will not work.")


def process_pdf(pdf_data: Union[bytes, io.BytesIO]) -> str:
    """
    Extract text from PDF data

    Args:
        pdf_data: PDF file data as bytes or BytesIO

    Returns:
        Extracted text as string

    Raises:
        RuntimeError: If PyPDF2 is not available
        ValueError: If PDF processing fails
    """

    if not PDF_AVAILABLE:
        raise RuntimeError("PDF processing not available. Install PyPDF2: pip install PyPDF2")

    try:
        # Convert bytes to BytesIO if needed
        if isinstance(pdf_data, bytes):
            pdf_file = io.BytesIO(pdf_data)
        else:
            pdf_file = pdf_data

        # Create PDF reader
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        if len(pdf_reader.pages) == 0:
            raise ValueError("PDF contains no pages")

        # Extract text from all pages
        text_content = []

        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(page_text)
                else:
                    logger.warning(f"No text extracted from page {page_num + 1}")
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                continue

        if not text_content:
            raise ValueError("No text could be extracted from the PDF")

        # Join all pages with double newline
        full_text = "\n\n".join(text_content)

        # Clean up the text
        full_text = clean_extracted_text(full_text)

        logger.info(f"Successfully extracted {len(full_text)} characters from {len(pdf_reader.pages)} pages")

        return full_text

    except Exception as e:
        logger.error(f"PDF processing failed: {e}")
        raise ValueError(f"Failed to process PDF: {str(e)}")


def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """

    if not text:
        return ""

    # Normalize whitespace
    lines = []
    for line in text.split('\n'):
        # Remove excessive whitespace but preserve intentional line breaks
        cleaned_line = ' '.join(line.split())
        if cleaned_line:  # Only keep non-empty lines
            lines.append(cleaned_line)

    # Join lines with single newlines
    cleaned_text = '\n'.join(lines)

    # Remove excessive newlines (more than 2 consecutive)
    import re
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

    return cleaned_text.strip()


def get_pdf_metadata(pdf_data: Union[bytes, io.BytesIO]) -> dict:
    """
    Extract metadata from PDF

    Args:
        pdf_data: PDF file data as bytes or BytesIO

    Returns:
        Dictionary with PDF metadata
    """

    if not PDF_AVAILABLE:
        return {}

    try:
        # Convert bytes to BytesIO if needed
        if isinstance(pdf_data, bytes):
            pdf_file = io.BytesIO(pdf_data)
        else:
            pdf_file = pdf_data

        # Create PDF reader
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        metadata = {}

        # Basic info
        metadata['page_count'] = len(pdf_reader.pages)

        # Document info if available
        if pdf_reader.metadata:
            doc_info = pdf_reader.metadata

            # Map common metadata fields
            field_mapping = {
                '/Title': 'title',
                '/Author': 'author',
                '/Subject': 'subject',
                '/Creator': 'creator',
                '/Producer': 'producer',
                '/CreationDate': 'creation_date',
                '/ModDate': 'modification_date'
            }

            for pdf_key, clean_key in field_mapping.items():
                if pdf_key in doc_info and doc_info[pdf_key]:
                    metadata[clean_key] = str(doc_info[pdf_key])

        return metadata

    except Exception as e:
        logger.warning(f"Failed to extract PDF metadata: {e}")
        return {}


def validate_pdf(pdf_data: Union[bytes, io.BytesIO]) -> bool:
    """
    Validate that the data is a valid PDF

    Args:
        pdf_data: PDF file data as bytes or BytesIO

    Returns:
        True if valid PDF, False otherwise
    """

    if not PDF_AVAILABLE:
        return False

    try:
        # Convert bytes to BytesIO if needed
        if isinstance(pdf_data, bytes):
            pdf_file = io.BytesIO(pdf_data)
        else:
            pdf_file = pdf_data

        # Try to create PDF reader
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Check if it has pages
        return len(pdf_reader.pages) > 0

    except Exception:
        return False