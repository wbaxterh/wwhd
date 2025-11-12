#!/usr/bin/env python3
"""
Simple user creation script that can be run manually
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def create_test_user():
    """Create test user manually"""
    from models import init_db, get_db, User
    from api.auth import get_password_hash

    try:
        print("Initializing database...")
        await init_db()

        print("Creating test user...")
        async for db in get_db():
            # Check if user already exists
            result = await db.execute(select(User).where(User.username == "testuser"))
            existing = result.scalar_one_or_none()

            if existing:
                print(f"✅ User 'testuser' already exists (ID: {existing.id})")
                return existing

            # Create new user
            hashed_password = get_password_hash("testpass123")
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=hashed_password,
                is_active=True
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            print(f"✅ Created test user:")
            print(f"   ID: {user.id}")
            print(f"   Username: testuser")
            print(f"   Email: test@example.com")
            print(f"   Password: testpass123")
            return user

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(create_test_user())
    sys.exit(0 if result else 1)