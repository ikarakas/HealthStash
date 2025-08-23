import pytest
from fastapi import status
from datetime import datetime, timedelta
import io
import json

class TestHealthRecords:
    """Test health records endpoints"""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_create_health_record(self, client, auth_headers):
        """Test creating a health record"""
        response = client.post(
            "/health-records/",
            headers=auth_headers,
            json={
                "record_type": "lab_result",
                "record_date": datetime.now().isoformat(),
                "title": "Blood Test",
                "description": "Annual blood work",
                "category": "laboratory",
                "metadata": {"test_type": "CBC"}
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Blood Test"
        assert data["record_type"] == "lab_result"
        assert data["category"] == "laboratory"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_health_records(self, client, auth_headers, sample_health_record):
        """Test getting user's health records"""
        response = client.get("/health-records/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(r["id"] == sample_health_record.id for r in data)
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_health_record_by_id(self, client, auth_headers, sample_health_record):
        """Test getting specific health record"""
        response = client.get(
            f"/health-records/{sample_health_record.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_health_record.id
        assert data["title"] == sample_health_record.title
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_update_health_record(self, client, auth_headers, sample_health_record):
        """Test updating a health record"""
        response = client.put(
            f"/health-records/{sample_health_record.id}",
            headers=auth_headers,
            json={
                "title": "Updated Blood Test",
                "description": "Updated description"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Blood Test"
        assert data["description"] == "Updated description"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_delete_health_record(self, client, auth_headers, sample_health_record):
        """Test deleting a health record"""
        response = client.delete(
            f"/health-records/{sample_health_record.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        response = client.get(
            f"/health-records/{sample_health_record.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_filter_health_records_by_type(self, client, auth_headers, test_user, test_db):
        """Test filtering health records by type"""
        # Create multiple records
        record_types = ["lab_result", "prescription", "imaging", "consultation"]
        for record_type in record_types:
            response = client.post(
                "/health-records/",
                headers=auth_headers,
                json={
                    "record_type": record_type,
                    "record_date": datetime.now().isoformat(),
                    "title": f"{record_type} test",
                    "category": "test"
                }
            )
            assert response.status_code == status.HTTP_201_CREATED
        
        # Filter by type
        response = client.get(
            "/health-records/?record_type=lab_result",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(r["record_type"] == "lab_result" for r in data)
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_filter_health_records_by_date_range(self, client, auth_headers):
        """Test filtering health records by date range"""
        # Create records with different dates
        dates = [
            datetime.now() - timedelta(days=30),
            datetime.now() - timedelta(days=15),
            datetime.now(),
            datetime.now() + timedelta(days=15)
        ]
        
        for date in dates:
            response = client.post(
                "/health-records/",
                headers=auth_headers,
                json={
                    "record_type": "test",
                    "record_date": date.isoformat(),
                    "title": f"Record on {date.date()}",
                    "category": "test"
                }
            )
            assert response.status_code == status.HTTP_201_CREATED
        
        # Filter by date range
        start_date = (datetime.now() - timedelta(days=20)).date()
        end_date = (datetime.now() + timedelta(days=5)).date()
        
        response = client.get(
            f"/health-records/?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_search_health_records(self, client, auth_headers):
        """Test searching health records"""
        # Create records with searchable content
        records = [
            {"title": "Diabetes Test", "description": "Blood glucose levels"},
            {"title": "Heart Checkup", "description": "ECG and blood pressure"},
            {"title": "Eye Exam", "description": "Vision test and retinal scan"}
        ]
        
        for record in records:
            response = client.post(
                "/health-records/",
                headers=auth_headers,
                json={
                    "record_type": "test",
                    "record_date": datetime.now().isoformat(),
                    "title": record["title"],
                    "description": record["description"],
                    "category": "test"
                }
            )
            assert response.status_code == status.HTTP_201_CREATED
        
        # Search for specific term
        response = client.get(
            "/health-records/search?query=blood",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
        assert all("blood" in r["description"].lower() for r in data)
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.storage
    def test_upload_file_to_health_record(self, client, auth_headers, sample_health_record, temp_file):
        """Test uploading file to health record"""
        with open(temp_file, 'rb') as f:
            response = client.post(
                f"/health-records/{sample_health_record.id}/upload",
                headers=auth_headers,
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "file_url" in data
        assert data["file_name"] == "test.pdf"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_health_record_statistics(self, client, auth_headers):
        """Test getting health record statistics"""
        response = client.get("/health-records/statistics", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_records" in data
        assert "records_by_type" in data
        assert "records_by_category" in data
        assert "recent_records" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_export_health_records(self, client, auth_headers):
        """Test exporting health records"""
        response = client.get(
            "/health-records/export?format=json",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        
        # Test CSV export
        response = client.get(
            "/health-records/export?format=csv",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert "text/csv" in response.headers["content-type"]
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_bulk_create_health_records(self, client, auth_headers):
        """Test bulk creation of health records"""
        records = [
            {
                "record_type": "lab_result",
                "record_date": datetime.now().isoformat(),
                "title": f"Test {i}",
                "category": "test"
            }
            for i in range(5)
        ]
        
        response = client.post(
            "/health-records/bulk",
            headers=auth_headers,
            json=records
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 5
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_share_health_record(self, client, auth_headers, sample_health_record, test_db):
        """Test sharing health record with another user"""
        # Create another user
        response = client.post(
            "/auth/register",
            json={
                "email": "doctor@example.com",
                "password": "DoctorPass123!",
                "full_name": "Dr. Smith"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        doctor_id = response.json()["id"]
        
        # Share record
        response = client.post(
            f"/health-records/{sample_health_record.id}/share",
            headers=auth_headers,
            json={
                "user_id": doctor_id,
                "permission": "read",
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["shared_with_id"] == doctor_id
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_health_record_pagination(self, client, auth_headers):
        """Test pagination of health records"""
        # Create many records
        for i in range(25):
            response = client.post(
                "/health-records/",
                headers=auth_headers,
                json={
                    "record_type": "test",
                    "record_date": datetime.now().isoformat(),
                    "title": f"Record {i}",
                    "category": "test"
                }
            )
            assert response.status_code == status.HTTP_201_CREATED
        
        # Test pagination
        response = client.get(
            "/health-records/?skip=0&limit=10",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 10
        
        # Get next page
        response = client.get(
            "/health-records/?skip=10&limit=10",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 10
    
    @pytest.mark.security
    @pytest.mark.api
    def test_unauthorized_access_to_records(self, client, sample_health_record):
        """Test unauthorized access to health records"""
        # Try to access without authentication
        response = client.get(f"/health-records/{sample_health_record.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try to delete without authentication
        response = client.delete(f"/health-records/{sample_health_record.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.security
    @pytest.mark.api
    def test_access_other_users_records(self, client, auth_headers, test_db):
        """Test that users cannot access other users' records"""
        # Create another user and their record
        other_user_response = client.post(
            "/auth/register",
            json={
                "email": "other@example.com",
                "password": "OtherPass123!",
                "full_name": "Other User"
            }
        )
        assert other_user_response.status_code == status.HTTP_201_CREATED
        
        # Login as other user
        other_login = client.post(
            "/auth/login",
            data={
                "username": "other@example.com",
                "password": "OtherPass123!"
            }
        )
        other_token = other_login.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        # Create record as other user
        other_record_response = client.post(
            "/health-records/",
            headers=other_headers,
            json={
                "record_type": "private",
                "record_date": datetime.now().isoformat(),
                "title": "Private Record",
                "category": "test"
            }
        )
        other_record_id = other_record_response.json()["id"]
        
        # Try to access other user's record with first user's token
        response = client.get(
            f"/health-records/{other_record_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN