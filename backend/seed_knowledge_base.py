#!/usr/bin/env python3
"""
Seed script to add Herman's key teachings to the knowledge base
This bypasses the corrupted Qdrant data by creating fresh content
"""
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import get_db, Document, User
from services.qdrant_service import QdrantService
from config import settings
import uuid

# Herman's core teachings
HERMAN_TEACHINGS = [
    {
        "title": "The Three Words You Should Never Say",
        "content": """The three words you should never say are "hope," "try," and "can't." These words can act as barriers to your growth and potential, limiting your mindset and actions.

When you say "hope," you place your dreams in a passive state, suggesting that they may not come to fruition unless some external force intervenes. Instead, embrace a more proactive approach by stating your intentions clearly. For instance, rather than saying, "I hope to improve my health," you could say, "I am committed to improving my health through daily exercise and mindful eating." This shift in language empowers you to take control of your destiny.

Similarly, "try" implies a lack of commitment, as if you are not fully invested in the outcome. Instead of saying, "I will try to meditate," declare, "I will meditate daily." This simple yet profound switch reflects the discipline of martial arts, where commitment to practice leads to mastery.

Lastly, "can't" is a self-imposed limitation. By eliminating this word from your vocabulary, you open yourself to possibilities. For instance, instead of saying, "I can't achieve my goals," remind yourself, "I am learning how to achieve my goals." Remember, words are tools; use them wisely to forge the path you desire.""",
        "namespace": "general"
    },
    {
        "title": "The Power of Discipline and Routine",
        "content": """Discipline is the bridge between goals and accomplishment. It's not about perfection, but about consistency in your daily actions. Every morning you wake up, you have a choice: to move forward or to remain stagnant.

The path of martial arts teaches us that mastery comes through repetition and dedication. Just as a warrior trains daily to perfect their technique, you must train your mind and body to achieve your highest potential.

Create routines that serve your growth. Whether it's meditation at dawn, physical exercise, or study, make these practices non-negotiable. The compound effect of small, consistent actions will transform your life in ways you cannot yet imagine.""",
        "namespace": "general"
    },
    {
        "title": "Overcoming Mediocrity",
        "content": """Mediocrity is not a lack of ability, but a lack of commitment to excellence. It's the comfortable zone where most people choose to remain, avoiding the discomfort that comes with growth.

To overcome mediocrity, you must be willing to be uncomfortable. You must be willing to fail, to be criticized, to stand alone in your convictions. The majority will always choose the easy path, but those who achieve greatness walk a different road.

Ask yourself: What would happen if you gave 100% to everything you do? What if you approached each task, each relationship, each moment with complete presence and dedication? This is how you escape the trap of average.""",
        "namespace": "general"
    }
]

async def seed_knowledge_base():
    """Seed the knowledge base with Herman's core teachings"""
    print("🌱 Starting knowledge base seeding...")

    # Get a user to assign as uploader
    async for db in get_db():
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            print("❌ No users found in database. Please create a user first.")
            return

        uploader_id = user.id
        print(f"📝 Using user {user.username} (ID: {uploader_id}) as document uploader")

        # Initialize Qdrant service
        qdrant_service = QdrantService()

        added_count = 0

        for teaching in HERMAN_TEACHINGS:
            try:
                # Check if document already exists
                existing = await db.execute(
                    select(Document).where(Document.title == teaching["title"])
                )
                if existing.scalar_one_or_none():
                    print(f"   📄 Document '{teaching['title']}' already exists, skipping")
                    continue

                # Create unique vector ID
                vector_id = str(uuid.uuid4())

                # Create document record in SQLite
                new_doc = Document(
                    namespace=teaching["namespace"],
                    title=teaching["title"],
                    content=teaching["content"],
                    vector_id=vector_id,
                    embedding_model=settings.model_embed,
                    uploaded_by=uploader_id,
                    created_at=datetime.utcnow()
                )

                db.add(new_doc)
                await db.flush()  # Get the ID

                # Store in Qdrant
                await qdrant_service.add_document(
                    namespace=teaching["namespace"],
                    document_id=vector_id,
                    content=teaching["content"],
                    metadata={
                        "document_id": str(new_doc.id),
                        "title": teaching["title"],
                        "namespace": teaching["namespace"]
                    }
                )

                await db.commit()
                added_count += 1

                print(f"   ✅ Added: {teaching['title']}")

            except Exception as e:
                await db.rollback()
                print(f"   ❌ Failed to add '{teaching['title']}': {e}")
                continue

        print(f"\n🎉 Seeding completed! Added {added_count} documents")
        break  # Exit the async for loop

if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())