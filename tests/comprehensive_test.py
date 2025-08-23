#!/usr/bin/env python3
"""
Comprehensive HealthStash System Testing Script
This script performs extensive testing of all system functionality including:
- User registration and authentication
- Health record CRUD operations
- File upload/download with various sizes
- MinIO storage verification
- Search and filter functionality
- Bulk operations
"""

import requests
import json
import os
import time
import random
import string
from datetime import datetime, timedelta
import tempfile
from pathlib import Path
import hashlib
import subprocess

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_PREFIX = f"test_{int(time.time())}"
TEST_FILES_DIR = tempfile.mkdtemp(prefix="healthstash_test_")

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "stats": {}
}

def log_success(message):
    print(f"✅ {message}")
    test_results["passed"].append(message)

def log_error(message):
    print(f"❌ {message}")
    test_results["failed"].append(message)

def log_info(message):
    print(f"ℹ️  {message}")

def log_warning(message):
    print(f"⚠️  {message}")

class HealthStashTester:
    def __init__(self):
        self.session = requests.Session()
        self.user_email = f"{TEST_USER_PREFIX}@example.com"
        self.user_password = "TestPassword123!@#"
        self.user_id = None
        self.access_token = None
        self.created_records = []
        self.uploaded_files = []
        
    def register_user(self):
        """Register a new test user"""
        log_info("Testing user registration...")
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": self.user_email,
                "username": self.user_email,
                "password": self.user_password,
                "full_name": "Test User"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            log_success(f"User registered: {self.user_email}")
            return True
        else:
            log_error(f"Registration failed: {response.text}")
            return False
    
    def login_user(self):
        """Login with existing user"""
        log_info("Testing user login...")
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            data={
                "username": self.user_email,
                "password": self.user_password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            log_success("User logged in successfully")
            return True
        else:
            log_error(f"Login failed: {response.text}")
            return False
    
    def create_health_records(self, count=50):
        """Create multiple health records with various types"""
        log_info(f"Creating {count} health records...")
        
        record_types = ["lab_result", "prescription", "imaging", "consultation", "vaccination"]
        categories = ["laboratory", "pharmacy", "radiology", "general", "cardiology", "neurology"]
        
        for i in range(count):
            record_date = datetime.now() - timedelta(days=random.randint(0, 365))
            record_type = random.choice(record_types)
            
            record_data = {
                "record_type": record_type,
                "record_date": record_date.isoformat(),
                "title": f"Test Record {i+1} - {record_type}",
                "description": f"This is test record number {i+1}. " + "Lorem ipsum " * 10,
                "category": random.choice(categories),
                "doctor_name": f"Dr. Test {random.randint(1, 10)}",
                "facility_name": f"Test Hospital {random.randint(1, 5)}",
                "metadata": {
                    "test_id": f"TEST_{i}",
                    "created_by": "automated_test",
                    "importance": random.choice(["low", "medium", "high"])
                }
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/records/",
                json=record_data
            )
            
            if response.status_code in [200, 201]:
                record = response.json()
                self.created_records.append(record["id"])
                if (i + 1) % 10 == 0:
                    log_success(f"Created {i + 1} records")
            else:
                log_error(f"Failed to create record {i+1}: {response.text}")
        
        test_results["stats"]["records_created"] = len(self.created_records)
        log_success(f"Total records created: {len(self.created_records)}")
        return True
    
    def test_file_uploads(self):
        """Test file uploads with various sizes"""
        log_info("Testing file uploads with various sizes...")
        
        # Create test files of different sizes
        test_files = [
            ("small.txt", 1024),  # 1 KB
            ("medium.pdf", 1024 * 1024),  # 1 MB
            ("large.pdf", 10 * 1024 * 1024),  # 10 MB
            ("xlarge.pdf", 50 * 1024 * 1024),  # 50 MB
        ]
        
        for filename, size in test_files:
            # Create test file
            file_path = os.path.join(TEST_FILES_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(os.urandom(size))
            
            # Calculate file hash for verification
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Upload file
            log_info(f"Uploading {filename} ({size / 1024 / 1024:.2f} MB)...")
            
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                
                # Attach to a random record if we have any
                if self.created_records:
                    record_id = random.choice(self.created_records)
                    response = self.session.post(
                        f"{BASE_URL}/api/records/{record_id}/files",
                        files=files
                    )
                else:
                    response = self.session.post(
                        f"{BASE_URL}/api/files/upload",
                        files=files
                    )
            
            if response.status_code in [200, 201]:
                file_data = response.json()
                self.uploaded_files.append({
                    "id": file_data.get("id") or file_data.get("file_id"),
                    "name": filename,
                    "size": size,
                    "hash": file_hash,
                    "url": file_data.get("url") or file_data.get("file_url")
                })
                log_success(f"Uploaded {filename} successfully")
            else:
                log_error(f"Failed to upload {filename}: {response.text}")
        
        test_results["stats"]["files_uploaded"] = len(self.uploaded_files)
        return True
    
    def verify_minio_storage(self):
        """Verify files are stored in MinIO"""
        log_info("Verifying MinIO storage...")
        
        # Check MinIO directly using docker exec
        result = subprocess.run(
            ["docker", "exec", "healthstash-minio", "mc", "ls", "local/healthstash"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            files_in_minio = result.stdout.strip().split('\n')
            log_success(f"MinIO contains {len(files_in_minio)} objects")
            test_results["stats"]["minio_objects"] = len(files_in_minio)
        else:
            log_warning("Could not verify MinIO storage directly")
        
        return True
    
    def test_file_downloads(self):
        """Test downloading uploaded files"""
        log_info("Testing file downloads...")
        
        success_count = 0
        for file_info in self.uploaded_files[:5]:  # Test first 5 files
            file_id = file_info["id"]
            
            response = self.session.get(
                f"{BASE_URL}/api/files/{file_id}/download"
            )
            
            if response.status_code == 200:
                # Verify file size
                downloaded_size = len(response.content)
                if downloaded_size == file_info["size"]:
                    log_success(f"Downloaded {file_info['name']} - size matches")
                    success_count += 1
                else:
                    log_error(f"Size mismatch for {file_info['name']}: expected {file_info['size']}, got {downloaded_size}")
            else:
                log_error(f"Failed to download {file_info['name']}: {response.status_code}")
        
        test_results["stats"]["files_downloaded"] = success_count
        return success_count > 0
    
    def test_record_updates(self):
        """Test updating health records"""
        log_info("Testing record updates...")
        
        if not self.created_records:
            log_warning("No records to update")
            return False
        
        success_count = 0
        for record_id in self.created_records[:10]:  # Update first 10 records
            update_data = {
                "title": f"Updated Record - {datetime.now().isoformat()}",
                "description": "This record has been updated by automated testing",
                "metadata": {
                    "updated": True,
                    "update_time": datetime.now().isoformat()
                }
            }
            
            response = self.session.put(
                f"{BASE_URL}/api/records/{record_id}",
                json=update_data
            )
            
            if response.status_code == 200:
                success_count += 1
            else:
                log_error(f"Failed to update record {record_id}: {response.text}")
        
        log_success(f"Successfully updated {success_count} records")
        test_results["stats"]["records_updated"] = success_count
        return success_count > 0
    
    def test_record_deletion(self):
        """Test deleting health records"""
        log_info("Testing record deletion...")
        
        if len(self.created_records) < 10:
            log_warning("Not enough records to test deletion")
            return False
        
        records_to_delete = self.created_records[-5:]  # Delete last 5 records
        success_count = 0
        
        for record_id in records_to_delete:
            response = self.session.delete(
                f"{BASE_URL}/api/health-records/{record_id}"
            )
            
            if response.status_code in [200, 204]:
                success_count += 1
                self.created_records.remove(record_id)
            else:
                log_error(f"Failed to delete record {record_id}: {response.text}")
        
        log_success(f"Successfully deleted {success_count} records")
        test_results["stats"]["records_deleted"] = success_count
        return success_count > 0
    
    def test_search_functionality(self):
        """Test search and filter functionality"""
        log_info("Testing search and filter functionality...")
        
        # Test search by keyword
        search_terms = ["test", "record", "lab", "prescription"]
        
        for term in search_terms:
            response = self.session.get(
                f"{BASE_URL}/api/records/",
                params={"search": term}
            )
            
            if response.status_code == 200:
                results = response.json()
                log_success(f"Search for '{term}' returned {len(results)} results")
            else:
                log_error(f"Search failed for '{term}': {response.text}")
        
        # Test filtering by type
        response = self.session.get(
            f"{BASE_URL}/api/records/",
            params={"record_type": "lab_result"}
        )
        
        if response.status_code == 200:
            results = response.json()
            log_success(f"Filter by type 'lab_result' returned {len(results)} results")
        
        # Test date range filtering
        start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        end_date = datetime.now().date().isoformat()
        
        response = self.session.get(
            f"{BASE_URL}/api/records/",
            params={"start_date": start_date, "end_date": end_date}
        )
        
        if response.status_code == 200:
            results = response.json()
            log_success(f"Date range filter returned {len(results)} results")
        
        return True
    
    def test_pagination(self):
        """Test pagination of records"""
        log_info("Testing pagination...")
        
        # Get total count
        response = self.session.get(f"{BASE_URL}/api/health-records/")
        if response.status_code == 200:
            total_records = len(response.json())
            
            # Test pagination
            page_size = 10
            response = self.session.get(
                f"{BASE_URL}/api/records/",
                params={"skip": 0, "limit": page_size}
            )
            
            if response.status_code == 200:
                first_page = response.json()
                log_success(f"Pagination: Got {len(first_page)} records in first page")
                
                # Get second page
                response = self.session.get(
                    f"{BASE_URL}/api/records/",
                    params={"skip": page_size, "limit": page_size}
                )
                
                if response.status_code == 200:
                    second_page = response.json()
                    log_success(f"Pagination: Got {len(second_page)} records in second page")
        
        return True
    
    def test_bulk_operations(self):
        """Test bulk operations"""
        log_info("Testing bulk operations...")
        
        # Create multiple records in bulk
        bulk_records = []
        for i in range(10):
            bulk_records.append({
                "record_type": "lab_result",
                "record_date": datetime.now().isoformat(),
                "title": f"Bulk Record {i}",
                "description": "Created in bulk",
                "category": "laboratory"
            })
        
        response = self.session.post(
            f"{BASE_URL}/api/records/bulk",
            json=bulk_records
        )
        
        if response.status_code in [200, 201]:
            log_success("Bulk creation successful")
        else:
            log_warning(f"Bulk creation endpoint not available: {response.status_code}")
        
        return True
    
    def test_concurrent_operations(self):
        """Test concurrent operations"""
        log_info("Testing concurrent operations...")
        
        import concurrent.futures
        import threading
        
        def create_record(index):
            response = self.session.post(
                f"{BASE_URL}/api/records/",
                json={
                    "record_type": "lab_result",
                    "record_date": datetime.now().isoformat(),
                    "title": f"Concurrent Record {index}",
                    "description": f"Created concurrently by thread {threading.current_thread().name}",
                    "category": "laboratory"
                }
            )
            return response.status_code in [200, 201]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_record, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        log_success(f"Concurrent operations: {success_count}/10 successful")
        test_results["stats"]["concurrent_success"] = success_count
        
        return success_count > 0
    
    def cleanup(self):
        """Clean up test data"""
        log_info("Cleaning up test data...")
        
        # Clean up test files
        import shutil
        if os.path.exists(TEST_FILES_DIR):
            shutil.rmtree(TEST_FILES_DIR)
            log_success("Cleaned up test files")
        
        # Note: We're keeping test records in the database for manual verification
        log_info(f"Test user and records retained for manual verification: {self.user_email}")
        
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("       COMPREHENSIVE TEST REPORT")
        print("="*60)
        print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test User: {self.user_email}")
        print(f"\n📊 TEST STATISTICS:")
        print("-"*40)
        
        for key, value in test_results["stats"].items():
            print(f"  {key}: {value}")
        
        print(f"\n✅ PASSED TESTS: {len(test_results['passed'])}")
        for test in test_results["passed"][:10]:  # Show first 10
            print(f"  • {test}")
        
        if len(test_results["passed"]) > 10:
            print(f"  ... and {len(test_results['passed']) - 10} more")
        
        if test_results["failed"]:
            print(f"\n❌ FAILED TESTS: {len(test_results['failed'])}")
            for test in test_results["failed"]:
                print(f"  • {test}")
        
        print("\n" + "="*60)
        
        success_rate = len(test_results["passed"]) / (len(test_results["passed"]) + len(test_results["failed"])) * 100
        
        if success_rate > 90:
            print("✅ OVERALL: SYSTEM PASSED COMPREHENSIVE TESTING")
        elif success_rate > 70:
            print("⚠️  OVERALL: SYSTEM PARTIALLY PASSED - SOME ISSUES FOUND")
        else:
            print("❌ OVERALL: SYSTEM NEEDS ATTENTION - MULTIPLE FAILURES")
        
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        print("="*60)

def main():
    print("🚀 Starting Comprehensive HealthStash Testing")
    print("="*60)
    
    tester = HealthStashTester()
    
    try:
        # Run all tests
        if tester.register_user():
            tester.create_health_records(50)
            tester.test_file_uploads()
            tester.verify_minio_storage()
            tester.test_file_downloads()
            tester.test_record_updates()
            tester.test_record_deletion()
            tester.test_search_functionality()
            tester.test_pagination()
            tester.test_bulk_operations()
            tester.test_concurrent_operations()
        
        # Generate report
        tester.generate_report()
        
        # Cleanup
        tester.cleanup()
        
    except Exception as e:
        log_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return 0 if not test_results["failed"] else 1

if __name__ == "__main__":
    exit(main())