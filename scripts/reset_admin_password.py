#!/usr/bin/env python3
import sys
import os
sys.path.append('/app')

from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://healthstash:changeme@postgres:5432/healthstash')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_admin_password():
    """Reset admin password to admin123"""
    db = SessionLocal()
    try:
        # Hash the new password
        hashed_password = pwd_context.hash("admin123")
        
        # Update admin password
        result = db.execute(
            text("UPDATE users SET hashed_password = :password WHERE username = 'admin' AND role = 'admin'"),
            {"password": hashed_password}
        )
        db.commit()
        
        if result.rowcount > 0:
            print(f"✅ Admin password reset successfully!")
            print(f"   Email: admin@example.com")
            print(f"   Username: admin")  
            print(f"   Password: admin123")
        else:
            print("❌ No admin user found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()