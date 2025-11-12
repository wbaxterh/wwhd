#!/usr/bin/env python3
"""Create a test user for development"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from models import init_db, get_db, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """Create a test user for development"""
    await init_db()

    async for db in get_db():
        # Check if test user already exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "test@example.com"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Test user already exists!")
            print(f"ID: {existing_user.id}")
            print(f"Email: {existing_user.email}")
            print(f"Username: {existing_user.username}")
            return existing_user

        # Hash the password
        hashed_password = pwd_context.hash("testpass123")

        # Create test user
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

        print("Test user created successfully!")
        print(f"ID: {test_user.id}")
        print(f"Email: {test_user.email}")
        print(f"Username: {test_user.username}")
        return test_user

if __name__ == "__main__":
    asyncio.run(create_test_user())