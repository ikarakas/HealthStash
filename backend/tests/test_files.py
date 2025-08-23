import pytest
from fastapi import status
import io
import os
from PIL import Image
import PyPDF2
import tempfile

class TestFileOperations:
    """Test file upload and management endpoints"""
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.storage
    def test_upload_pdf_file(self, client, auth_headers):
        """Test uploading PDF file"""
        pdf_content = b"%PDF-1.4\n%Test PDF content"
        
        response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "file_id" in data
        assert data["file_name"] == "test.pdf"
        assert data["file_type"] == "application/pdf"
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.storage
    def test_upload_image_file(self, client, auth_headers):
        """Test uploading image file with thumbnail generation"""
        # Create test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("test.png", img_bytes, "image/png")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "file_id" in data
        assert "thumbnail_url" in data
        assert data["file_type"] == "image/png"
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.storage
    def test_upload_dicom_file(self, client, auth_headers):
        """Test uploading DICOM medical image"""
        # Create minimal DICOM file structure
        dicom_content = b"DICM"  # Simplified DICOM header
        
        response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("scan.dcm", io.BytesIO(dicom_content), "application/dicom")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_name"] == "scan.dcm"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_upload_file_size_limit(self, client, auth_headers):
        """Test file size limit enforcement"""
        # Create large file (over limit)
        large_content = b"x" * (501 * 1024 * 1024)  # 501 MB
        
        response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("large.bin", io.BytesIO(large_content), "application/octet-stream")}
        )
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.security
    def test_upload_malicious_file_type(self, client, auth_headers):
        """Test rejection of potentially malicious file types"""
        malicious_types = [
            ("test.exe", "application/x-msdownload"),
            ("test.bat", "application/x-bat"),
            ("test.sh", "application/x-sh"),
            ("test.js", "text/javascript")
        ]
        
        for filename, mime_type in malicious_types:
            response = client.post(
                "/files/upload",
                headers=auth_headers,
                files={"file": (filename, b"malicious content", mime_type)}
            )
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ]
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_file_metadata(self, client, auth_headers):
        """Test getting file metadata"""
        # Upload file first
        upload_response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        file_id = upload_response.json()["file_id"]
        
        # Get metadata
        response = client.get(f"/files/{file_id}/metadata", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_name"] == "test.txt"
        assert data["file_size"] > 0
        assert data["mime_type"] == "text/plain"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_download_file(self, client, auth_headers):
        """Test file download"""
        # Upload file
        content = b"download test content"
        upload_response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("download.txt", content, "text/plain")}
        )
        file_id = upload_response.json()["file_id"]
        
        # Download file
        response = client.get(f"/files/{file_id}/download", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.content == content
        assert response.headers["content-disposition"] == 'attachment; filename="download.txt"'
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_delete_file(self, client, auth_headers):
        """Test file deletion"""
        # Upload file
        upload_response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("delete.txt", b"delete me", "text/plain")}
        )
        file_id = upload_response.json()["file_id"]
        
        # Delete file
        response = client.delete(f"/files/{file_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        response = client.get(f"/files/{file_id}/download", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_list_user_files(self, client, auth_headers):
        """Test listing user's files"""
        # Upload multiple files
        for i in range(3):
            client.post(
                "/files/upload",
                headers=auth_headers,
                files={"file": (f"file{i}.txt", f"content{i}".encode(), "text/plain")}
            )
        
        # List files
        response = client.get("/files/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 3
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.storage
    def test_file_encryption(self, client, auth_headers):
        """Test file encryption at rest"""
        sensitive_content = b"Sensitive medical data: SSN 123-45-6789"
        
        response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("sensitive.txt", sensitive_content, "text/plain")},
            data={"encrypt": "true"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get("encrypted") is True
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_batch_file_upload(self, client, auth_headers):
        """Test uploading multiple files at once"""
        files = [
            ("files", ("file1.txt", b"content1", "text/plain")),
            ("files", ("file2.txt", b"content2", "text/plain")),
            ("files", ("file3.txt", b"content3", "text/plain"))
        ]
        
        response = client.post(
            "/files/batch-upload",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["uploaded_files"]) == 3
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_file_versioning(self, client, auth_headers):
        """Test file versioning"""
        # Upload original file
        response1 = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("versioned.txt", b"version 1", "text/plain")}
        )
        file_id = response1.json()["file_id"]
        
        # Upload new version
        response2 = client.post(
            f"/files/{file_id}/new-version",
            headers=auth_headers,
            files={"file": ("versioned.txt", b"version 2", "text/plain")}
        )
        assert response2.status_code == status.HTTP_200_OK
        
        # Get file versions
        response3 = client.get(f"/files/{file_id}/versions", headers=auth_headers)
        assert response3.status_code == status.HTTP_200_OK
        versions = response3.json()
        assert len(versions) == 2
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.storage
    def test_file_compression(self, client, auth_headers):
        """Test file compression for storage optimization"""
        # Create compressible content
        content = b"AAAAAAAAAA" * 1000  # Highly compressible
        
        response = client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("compress.txt", content, "text/plain")},
            data={"compress": "true"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["original_size"] > data.get("compressed_size", data["file_size"])
    
    @pytest.mark.integration
    @pytest.mark.storage
    def test_concurrent_file_uploads(self, client, auth_headers):
        """Test concurrent file uploads"""
        import concurrent.futures
        
        def upload_file(index):
            return client.post(
                "/files/upload",
                headers=auth_headers,
                files={"file": (f"concurrent{index}.txt", f"content{index}".encode(), "text/plain")}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(10)]
            results = [f.result() for f in futures]
        
        for response in results:
            assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.security
    @pytest.mark.api
    def test_path_traversal_prevention(self, client, auth_headers):
        """Test prevention of path traversal attacks"""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../etc/shadow",
            "test/../../sensitive.txt"
        ]
        
        for filename in malicious_filenames:
            response = client.post(
                "/files/upload",
                headers=auth_headers,
                files={"file": (filename, b"content", "text/plain")}
            )
            # Should either reject or sanitize the filename
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                assert ".." not in data["file_name"]
                assert "/" not in data["file_name"]
                assert "\\" not in data["file_name"]
    
    @pytest.mark.performance
    @pytest.mark.storage
    def test_large_file_streaming(self, client, auth_headers):
        """Test streaming upload/download of large files"""
        # Create large file (100MB)
        large_size = 100 * 1024 * 1024
        
        def generate_content():
            chunk_size = 1024 * 1024  # 1MB chunks
            for _ in range(large_size // chunk_size):
                yield b"X" * chunk_size
        
        # Note: This would need actual streaming implementation
        # This is a placeholder for the test structure
        pass