from app.core.database import SessionLocal
from app.models.user import User
import traceback
import uuid

def test_db():
    db = SessionLocal()
    try:
        new_user = User(
            supabase_uid=str(uuid.uuid4()),
            email="test@test.com",
            name="Test User",
            preferred_language="en",
            home_port="Test Port",
            vessel_id="Test Vessel"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print("Successfully created User:", new_user)
        # Clean up
        db.delete(new_user)
        db.commit()
    except Exception as e:
        print("Database error occurred:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_db()
