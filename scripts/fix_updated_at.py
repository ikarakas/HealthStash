#!/usr/bin/env python3
"""
Fix updated_at field for existing users in the database.
"""

import os
import sys
from datetime import datetime, timezone

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings

def fix_updated_at():
    """Fix NULL or missing updated_at values for all users."""
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        updated_count = 0
        
        for user in users:
            # If updated_at is None or equals created_at, set it to now
            if user.updated_at is None:
                user.updated_at = user.created_at or datetime.now(timezone.utc)
                updated_count += 1
                print(f"Fixed updated_at for user: {user.username} (ID: {user.id})")
        
        # Commit changes
        if updated_count > 0:
            db.commit()
            print(f"\nSuccessfully updated {updated_count} user(s)")
        else:
            print("No users needed updating")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Fixing updated_at field for existing users...")
    fix_updated_at()
    print("Done!")