#!/usr/bin/env python3
"""
Startup script for WWHD backend
Handles database initialization and user creation
"""
import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def startup_sequence():
    """Run startup sequence for the backend"""
    print("🚀 Starting WWHD Backend initialization...")

    # Import after setting up path
    from models import init_db, get_db, User
    from api.auth import get_password_hash
    from config import settings

    print(f"📊 Database URL: {settings.database_url}")

    # Create database directory if it doesn't exist
    if settings.sqlite_path.startswith('/data/'):
        os.makedirs('/data', exist_ok=True)
        print("📁 Ensured /data directory exists")

    # Initialize database schema
    try:
        print("🗄️ Initializing database schema...")
        await init_db()
        print("✅ Database schema initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

    # Create test user if none exist
    try:
        async for db in get_db():
            # Check if any users exist
            from sqlalchemy import func
            result = await db.execute(select(func.count(User.id)))
            user_count = result.scalar()

            if user_count == 0:
                print("👤 Creating default test user...")

                hashed_password = get_password_hash("testpass123")
                test_user = User(
                    username="testuser",
                    email="test@example.com",
                    hashed_password=hashed_password,
                    is_active=True,
                    is_admin=False
                )

                db.add(test_user)
                await db.commit()
                await db.refresh(test_user)

                print(f"✅ Test user created:")
                print(f"   ID: {test_user.id}")
                print(f"   Username: testuser")
                print(f"   Email: test@example.com")
                print(f"   Password: testpass123")
            else:
                print(f"ℹ️ Database already has {user_count} users")

            break

    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False

    # No automatic database seeding or syncing for fresh deployment
    print("ℹ️ Database seeding and syncing disabled for fresh deployment")

    print("🎉 Backend initialization completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(startup_sequence())
    exit(0 if success else 1)