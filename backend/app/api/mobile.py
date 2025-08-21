from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import uuid
import secrets
import socket
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.core.config import settings

router = APIRouter()

# Store active upload tokens (in production, use Redis)
upload_tokens = {}

@router.post("/generate-token")
async def generate_upload_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a temporary token for mobile upload"""
    token = secrets.token_urlsafe(8)[:8].upper()  # 8 character token
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    # Store token with user ID and expiry
    upload_tokens[token] = {
        "user_id": current_user.id,
        "expires_at": expires_at,
        "created_at": datetime.utcnow()
    }
    
    # Clean up expired tokens
    now = datetime.utcnow()
    expired = [k for k, v in upload_tokens.items() if v["expires_at"] < now]
    for k in expired:
        del upload_tokens[k]
    
    # Get the server's actual accessible URL for mobile access
    import os
    
    # First, check for an environment variable with the public URL
    public_url = os.getenv('PUBLIC_URL', '')
    
    if public_url:
        upload_url = f"{public_url}/m/{token}"
    else:
        # Always use HOST_IP if it's set (this is for local network access)
        host_ip = os.getenv('HOST_IP', '')
        
        if host_ip and host_ip != 'host.docker.internal':
            # Use the configured HOST_IP for mobile access
            port = os.getenv('HTTP_PORT', '80')
            if port != '80' and port != '443':
                upload_url = f"http://{host_ip}:{port}/m/{token}"
            else:
                upload_url = f"http://{host_ip}/m/{token}"
        else:
            # Fallback to request headers only if HOST_IP is not set
            host = request.headers.get('x-forwarded-host') or request.headers.get('host')
            protocol = request.headers.get('x-forwarded-proto', 'http')
            
            # If the host is localhost or 127.0.0.1, try to detect the actual IP
            if host and (host.startswith('localhost') or host.startswith('127.0.0.1')):
                # Try to get a better IP address
                import subprocess
                try:
                    # This command works in most Linux environments to get the primary IP
                    result = subprocess.run(
                        ["sh", "-c", "hostname -I | awk '{print $1}'"],
                        capture_output=True, text=True, timeout=2
                    )
                    detected_ip = result.stdout.strip()
                    
                    # If we got a valid non-Docker IP, use it
                    if detected_ip and not detected_ip.startswith('172.'):
                        upload_url = f"http://{detected_ip}/m/{token}"
                    else:
                        # Last resort - use a common local network pattern
                        upload_url = f"http://192.168.1.100/m/{token}"
                except:
                    # If detection fails, use the original host
                    upload_url = f"{protocol}://{host}/m/{token}"
            else:
                # Use the host from headers if it's not localhost
                upload_url = f"{protocol}://{host}/m/{token}"
    
    return {
        "token": token,
        "expires_in": 900,  # 15 minutes in seconds
        "upload_url": upload_url
    }

class VerifyTokenRequest(BaseModel):
    token: str

@router.post("/verify-token")
async def verify_upload_token(request: VerifyTokenRequest):
    """Verify if a mobile upload token is valid"""
    token = request.token
    if token not in upload_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    token_data = upload_tokens[token]
    if datetime.utcnow() > token_data["expires_at"]:
        del upload_tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    return {"valid": True, "user_id": token_data["user_id"]}

@router.post("/upload/{token}")
async def mobile_upload_file(
    token: str,
    file: UploadFile = File(...),
    category: str = "other",
    db: Session = Depends(get_db),
    request: Request = None
):
    """Upload file using mobile token"""
    # Verify token
    if token not in upload_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    token_data = upload_tokens[token]
    if datetime.utcnow() > token_data["expires_at"]:
        del upload_tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    # Get user
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Process upload (delegate to files API)
    from app.api.files import upload_file as process_upload
    result = await process_upload(
        file=file,
        category=category,
        title=f"Mobile Upload - {file.filename}",
        current_user=user,
        db=db
    )
    
    # Track mobile upload (store in memory for now, in production use Redis/DB)
    if "mobile_uploads" not in globals():
        global mobile_uploads
        mobile_uploads = []
    
    # Get device info from user agent if available
    user_agent = request.headers.get("user-agent", "Unknown Device") if request else "Unknown Device"
    device = "Mobile Device"
    if "iPhone" in user_agent:
        device = "iPhone"
    elif "Android" in user_agent:
        device = "Android"
    elif "iPad" in user_agent:
        device = "iPad"
    
    mobile_uploads.insert(0, {
        "id": result.get("id"),
        "name": file.filename,
        "timestamp": datetime.utcnow().isoformat(),
        "device": device,
        "user_id": user.id
    })
    
    # Keep only last 50 uploads per user
    user_uploads = [u for u in mobile_uploads if u["user_id"] == user.id]
    if len(user_uploads) > 50:
        mobile_uploads = [u for u in mobile_uploads if u["user_id"] != user.id or u in user_uploads[:50]]
    
    return result

@router.get("/recent-uploads")
async def get_recent_mobile_uploads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent mobile uploads for the current user"""
    # Initialize mobile_uploads if it doesn't exist
    if "mobile_uploads" not in globals():
        global mobile_uploads
        mobile_uploads = []
    
    # Filter uploads for current user (last 10)
    user_uploads = [u for u in mobile_uploads if u["user_id"] == current_user.id][:10]
    
    return {
        "uploads": user_uploads
    }