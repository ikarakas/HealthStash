from minio import Minio
from minio.error import S3Error
import io
from typing import Optional

from app.core.config import settings

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    async def upload_file(self, content: bytes, object_name: str) -> bool:
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(content),
                len(content)
            )
            return True
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False
    
    async def download_file(self, object_name: str) -> Optional[bytes]:
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            content = response.read()
            response.close()
            response.release_conn()
            return content
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return None
    
    async def delete_file(self, object_name: str) -> bool:
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False
    
    async def list_files(self, prefix: str) -> list:
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing files: {e}")
            return []

storage_service = StorageService()