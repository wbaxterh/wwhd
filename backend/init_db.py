#!/usr/bin/env python3
"""
Database initialization script for WWHD backend
This ensures clean database setup on each deployment
"""
import asyncio
import os
from pathlib import Path

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from passlib.context import CryptContext
    from models import init_db, get_db, User, Document
    from config import settings

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False

async def reset_and_init_db():
    """Reset and initialize database with clean schema"""

    if not DEPENDENCIES_AVAILABLE:
        print("Dependencies not available, skipping database initialization")
        return

    # Remove existing database if it exists (for clean start)
    db_path = "./wwhd.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    # Ensure /data directory exists (for production)
    data_dir = Path("/data")
    if data_dir.exists():
        db_path = "/data/wwhd.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing production database: {db_path}")

    # Initialize fresh database
    print("Initializing fresh database...")
    await init_db()

    # Create default test user
    async for db in get_db():
        # Check if any users exist
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(User.id)))
        user_count = result.scalar()

        if user_count == 0:
            print("Creating default test user...")

            # Create test user
            hashed_password = pwd_context.hash("testpass123")
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password=hashed_password,
                is_active=True,
                is_admin=False
            )

            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)

            print(f"✅ Test user created:")
            print(f"   Username: testuser")
            print(f"   Email: test@example.com")
            print(f"   Password: testpass123")
            print(f"   ID: {test_user.id}")
        else:
            print(f"Database already has {user_count} users")

        break

    print("✅ Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(reset_and_init_db())