from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
import json
import random
import string
import time
from datetime import datetime

class HealthStashUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.user_email = None
        self.user_id = None
        self.record_ids = []
        self.file_ids = []
    
    def on_start(self):
        """Called when a user starts"""
        self.register_and_login()
    
    def on_stop(self):
        """Called when a user stops"""
        if self.token:
            self.logout()
    
    def register_and_login(self):
        """Register a new user and login"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.user_email = f"load_test_{random_suffix}@example.com"
        
        # Register
        register_response = self.client.post(
            "/auth/register",
            json={
                "email": self.user_email,
                "password": "LoadTest123!",
                "full_name": f"Load Test User {random_suffix}"
            }
        )
        
        if register_response.status_code == 201:
            self.user_id = register_response.json()["id"]
            
            # Login
            login_response = self.client.post(
                "/auth/login",
                data={
                    "username": self.user_email,
                    "password": "LoadTest123!"
                }
            )
            
            if login_response.status_code == 200:
                self.token = login_response.json()["access_token"]
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def logout(self):
        """Logout the user"""
        self.client.post("/auth/logout")
    
    @task(10)
    def view_dashboard(self):
        """View dashboard - high frequency task"""
        self.client.get("/api/dashboard/stats")
        self.client.get("/api/dashboard/recent-activity")
    
    @task(8)
    def list_health_records(self):
        """List health records - high frequency task"""
        response = self.client.get("/health-records/")
        if response.status_code == 200:
            records = response.json()
            if records:
                self.record_ids = [r["id"] for r in records[:10]]
    
    @task(5)
    def view_health_record(self):
        """View specific health record - medium frequency"""
        if self.record_ids:
            record_id = random.choice(self.record_ids)
            self.client.get(f"/health-records/{record_id}")
    
    @task(3)
    def create_health_record(self):
        """Create new health record - medium frequency"""
        record_types = ["lab_result", "prescription", "imaging", "consultation"]
        categories = ["laboratory", "pharmacy", "radiology", "general"]
        
        response = self.client.post(
            "/health-records/",
            json={
                "record_type": random.choice(record_types),
                "record_date": datetime.now().isoformat(),
                "title": f"Load Test Record {random.randint(1000, 9999)}",
                "description": "Automated load testing record",
                "category": random.choice(categories),
                "metadata": {
                    "test": True,
                    "timestamp": time.time()
                }
            }
        )
        
        if response.status_code == 201:
            self.record_ids.append(response.json()["id"])
    
    @task(2)
    def upload_file(self):
        """Upload a file - lower frequency"""
        file_content = b"Load test file content " * 100
        
        response = self.client.post(
            "/files/upload",
            files={"file": ("test.txt", file_content, "text/plain")}
        )
        
        if response.status_code == 200:
            self.file_ids.append(response.json()["file_id"])
    
    @task(4)
    def search_records(self):
        """Search health records"""
        search_terms = ["test", "blood", "x-ray", "prescription", "checkup"]
        query = random.choice(search_terms)
        self.client.get(f"/health-records/search?query={query}")
    
    @task(2)
    def filter_records(self):
        """Filter health records by type and date"""
        record_types = ["lab_result", "prescription", "imaging", "consultation"]
        record_type = random.choice(record_types)
        self.client.get(f"/health-records/?record_type={record_type}")
    
    @task(1)
    def update_health_record(self):
        """Update existing health record - low frequency"""
        if self.record_ids:
            record_id = random.choice(self.record_ids)
            self.client.put(
                f"/health-records/{record_id}",
                json={
                    "title": f"Updated Record {random.randint(1000, 9999)}",
                    "description": "Updated via load testing"
                }
            )
    
    @task(1)
    def delete_health_record(self):
        """Delete health record - low frequency"""
        if len(self.record_ids) > 5:  # Keep at least 5 records
            record_id = self.record_ids.pop(0)
            self.client.delete(f"/health-records/{record_id}")
    
    @task(3)
    def get_vitals(self):
        """Get vital signs data"""
        self.client.get("/vitals/")
        self.client.get("/vitals/latest")
    
    @task(2)
    def record_vitals(self):
        """Record new vital signs"""
        self.client.post(
            "/vitals/",
            json={
                "blood_pressure_systolic": random.randint(110, 130),
                "blood_pressure_diastolic": random.randint(70, 85),
                "heart_rate": random.randint(60, 100),
                "temperature": round(random.uniform(36.5, 37.5), 1),
                "weight": round(random.uniform(60, 90), 1),
                "recorded_at": datetime.now().isoformat()
            }
        )
    
    @task(1)
    def download_file(self):
        """Download a file - low frequency"""
        if self.file_ids:
            file_id = random.choice(self.file_ids)
            self.client.get(f"/files/{file_id}/download")
    
    @task(2)
    def get_statistics(self):
        """Get user statistics"""
        self.client.get("/health-records/statistics")
        self.client.get("/files/storage-info")

class AdminUser(HttpUser):
    """Admin user with different behavior patterns"""
    wait_time = between(2, 5)
    host = "http://localhost:8000"
    weight = 1  # Lower weight - fewer admin users
    
    def on_start(self):
        """Login as admin"""
        self.client.post(
            "/auth/login",
            data={
                "username": "admin@example.com",
                "password": "AdminPass123!"
            }
        )
    
    @task(5)
    def view_admin_dashboard(self):
        """View admin dashboard"""
        self.client.get("/admin/dashboard")
        self.client.get("/admin/statistics")
    
    @task(3)
    def list_users(self):
        """List all users"""
        self.client.get("/admin/users")
    
    @task(2)
    def view_system_health(self):
        """Check system health"""
        self.client.get("/health")
        self.client.get("/admin/system-status")
    
    @task(1)
    def backup_operations(self):
        """Trigger backup operations"""
        self.client.post("/admin/backup/trigger")
        self.client.get("/admin/backup/status")

class MobileUser(HttpUser):
    """Mobile user with different access patterns"""
    wait_time = between(3, 7)
    host = "http://localhost:8000"
    weight = 2  # Medium weight - some mobile users
    
    def on_start(self):
        """Mobile user registration and token generation"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        # Register
        register_response = self.client.post(
            "/auth/register",
            json={
                "email": f"mobile_{random_suffix}@example.com",
                "password": "MobileTest123!",
                "full_name": f"Mobile User {random_suffix}"
            }
        )
        
        if register_response.status_code == 201:
            # Generate mobile token
            self.client.post("/mobile/generate-token")
    
    @task(10)
    def quick_upload(self):
        """Mobile quick upload"""
        file_content = b"Mobile upload content"
        self.client.post(
            "/mobile/upload",
            files={"file": ("mobile.jpg", file_content, "image/jpeg")}
        )
    
    @task(5)
    def sync_data(self):
        """Sync mobile data"""
        self.client.get("/mobile/sync")
    
    @task(3)
    def check_notifications(self):
        """Check for notifications"""
        self.client.get("/mobile/notifications")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("Load test starting...")
    print(f"Target host: {environment.host}")
    print(f"Total users: {environment.parsed_options.num_users}")
    print(f"Spawn rate: {environment.parsed_options.spawn_rate}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\nLoad test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed requests: {environment.stats.total.num_failures}")
    print(f"Median response time: {environment.stats.total.median_response_time}ms")
    print(f"Average response time: {environment.stats.total.avg_response_time}ms")

# Custom test scenarios
class StressTestUser(HealthStashUser):
    """User for stress testing - aggressive behavior"""
    wait_time = between(0.1, 0.5)  # Very short wait times
    weight = 0  # Disabled by default, enable for stress tests
    
    @task(20)
    def aggressive_file_upload(self):
        """Upload large files rapidly"""
        file_size = random.randint(1, 10) * 1024 * 1024  # 1-10 MB
        file_content = b"X" * file_size
        
        self.client.post(
            "/files/upload",
            files={"file": (f"stress_{random.randint(1000, 9999)}.bin", file_content, "application/octet-stream")}
        )
    
    @task(10)
    def concurrent_updates(self):
        """Perform concurrent updates to test race conditions"""
        if self.record_ids:
            record_id = random.choice(self.record_ids)
            for _ in range(5):
                self.client.put(
                    f"/health-records/{record_id}",
                    json={"title": f"Concurrent Update {time.time()}"}
                )

class SpikeTestUser(HealthStashUser):
    """User for spike testing - sudden burst behavior"""
    weight = 0  # Disabled by default, enable for spike tests
    
    def on_start(self):
        """Burst registration"""
        super().on_start()
        # Immediately perform multiple operations
        for _ in range(10):
            self.create_health_record()
            self.upload_file()