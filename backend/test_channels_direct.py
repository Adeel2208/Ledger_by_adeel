"""Test channels analytics directly without HTTP."""
from app.database import SessionLocal
from app.services.sourcing_service import channel_performance_analytics

def test_direct():
    """Test the function directly to see the error."""
    db = SessionLocal()
    try:
        result = channel_performance_analytics(db)
        print("Success!")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_direct()
