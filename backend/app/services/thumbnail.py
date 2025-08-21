from PIL import Image
import io
import base64
from typing import Optional
import PyPDF2
import logging

from app.services.storage import storage_service
from app.core.security import decrypt_file_content, derive_key_from_password
from app.core.config import settings

logger = logging.getLogger(__name__)

async def generate_thumbnail(record) -> Optional[str]:
    """Generate a thumbnail for a health record file"""
    try:
        # Get the encrypted file from storage
        encrypted_content = await storage_service.download_file(record.minio_object_name)
        if not encrypted_content:
            return None
        
        # Decrypt the file
        user_key = derive_key_from_password(
            f"{record.user_id}:{record.user.hashed_password}:{settings.ENCRYPTION_KEY}",
            record.user.encryption_salt
        )
        decrypted_content = decrypt_file_content(encrypted_content, user_key)
        
        # Generate thumbnail based on file type
        if record.file_type and record.file_type.startswith('image/'):
            return generate_image_thumbnail(decrypted_content)
        elif record.file_type == 'application/pdf':
            return generate_pdf_thumbnail(decrypted_content)
        else:
            return generate_document_icon(record.file_type)
            
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}")
        return None

def generate_image_thumbnail(image_data: bytes, size=(200, 200)) -> str:
    """Generate thumbnail for image files"""
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Generate thumbnail
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        thumbnail_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/jpeg;base64,{thumbnail_data}"
        
    except Exception as e:
        logger.error(f"Failed to generate image thumbnail: {e}")
        return None

def generate_pdf_thumbnail(pdf_data: bytes) -> str:
    """Generate thumbnail for PDF files - creates an icon with page count"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
        page_count = len(pdf_reader.pages)
        
        # For now, return a simple SVG icon with page count
        svg = f'''
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="200" fill="#f8f9fa"/>
            <rect x="40" y="30" width="120" height="140" fill="#dc3545" rx="4"/>
            <rect x="50" y="40" width="100" height="120" fill="white" rx="2"/>
            <text x="100" y="90" text-anchor="middle" font-family="Arial" font-size="14" fill="#333">PDF</text>
            <text x="100" y="110" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">{page_count} pages</text>
        </svg>
        '''
        
        encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded}"
        
    except Exception as e:
        logger.error(f"Failed to generate PDF thumbnail: {e}")
        return generate_document_icon('application/pdf')

def generate_document_icon(file_type: str) -> str:
    """Generate a generic document icon based on file type"""
    
    # Determine icon color and label based on file type
    if 'word' in file_type or 'doc' in file_type:
        color = '#2b5797'
        label = 'DOC'
    elif 'excel' in file_type or 'spreadsheet' in file_type:
        color = '#207245'
        label = 'XLS'
    elif 'text' in file_type:
        color = '#666666'
        label = 'TXT'
    elif 'csv' in file_type:
        color = '#207245'
        label = 'CSV'
    else:
        color = '#6c757d'
        label = 'FILE'
    
    svg = f'''
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="#f8f9fa"/>
        <rect x="40" y="30" width="120" height="140" fill="{color}" rx="4"/>
        <rect x="50" y="40" width="100" height="120" fill="white" rx="2"/>
        <text x="100" y="100" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="{color}">{label}</text>
    </svg>
    '''
    
    encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"