#!/usr/bin/env python3
"""
Script to create the bulk_import user for remote API-based data import
Run this manually after deployment to prepare for data import
"""

import asyncio
import os
import sys
from sqlalchemy import select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def create_bulk_import_user():
    """Create the bulk_import user for API-based data import"""

    from models import init_db, get_db, User
    from api.auth import get_password_hash

    print("🔧 Creating bulk_import user for remote data import...")

    await init_db()

    async for db in get_db():
        try:
            # Check if bulk_import user already exists
            result = await db.execute(
                select(User).where(User.username == "bulk_import")
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("ℹ️ bulk_import user already exists")
                print(f"   Username: bulk_import")
                print(f"   Password: bulk123")
                return

            # Create bulk_import user
            hashed_password = get_password_hash("bulk123")
            bulk_user = User(
                username="bulk_import",
                email="bulk_import@wwhd.local",
                hashed_password=hashed_password,
                is_active=True,
                is_admin=True  # Admin privileges needed for document upload
            )

            db.add(bulk_user)
            await db.commit()
            await db.refresh(bulk_user)

            print("✅ bulk_import user created successfully!")
            print(f"   ID: {bulk_user.id}")
            print(f"   Username: bulk_import")
            print(f"   Password: bulk123")
            print("   Admin: True")
            print("")
            print("🔗 Use these credentials for remote API import:")
            print("   username: bulk_import")
            print("   password: bulk123")

        except Exception as e:
            print(f"❌ Failed to create bulk_import user: {e}")
            await db.rollback()
            return

        break

if __name__ == "__main__":
    asyncio.run(create_bulk_import_user())