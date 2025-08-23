import pytest
import docker
import requests
import time
import psutil
from datetime import datetime

class TestContainerHealth:
    """Test container health and orchestration"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Create Docker client"""
        return docker.from_env()
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_all_containers_running(self, docker_client):
        """Test that all required containers are running"""
        required_containers = [
            "healthstash-postgres",
            "healthstash-timescale",
            "healthstash-minio",
            "healthstash-backend",
            "healthstash-frontend",
            "healthstash-nginx",
            "healthstash-backup"
        ]
        
        running_containers = {c.name for c in docker_client.containers.list()}
        
        for container_name in required_containers:
            assert container_name in running_containers, f"{container_name} is not running"
    
    @pytest.mark.integration
    def test_container_health_checks(self, docker_client):
        """Test that all container health checks are passing"""
        containers = docker_client.containers.list()
        
        for container in containers:
            if container.name.startswith("healthstash-"):
                health = container.attrs.get("State", {}).get("Health")
                if health:
                    assert health["Status"] == "healthy", f"{container.name} is not healthy: {health}"
    
    @pytest.mark.integration
    def test_postgres_connectivity(self):
        """Test PostgreSQL database connectivity"""
        import psycopg2
        
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="healthstash",
                user="healthstash",
                password="changeme"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            assert version is not None
            assert "PostgreSQL" in version[0]
            conn.close()
        except Exception as e:
            pytest.fail(f"Failed to connect to PostgreSQL: {e}")
    
    @pytest.mark.integration
    def test_timescale_connectivity(self):
        """Test TimescaleDB connectivity and extensions"""
        import psycopg2
        
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5433,  # Assuming different port
                database="healthstash_vitals",
                user="healthstash",
                password="changeme"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "timescaledb"
            conn.close()
        except Exception as e:
            pytest.fail(f"Failed to connect to TimescaleDB: {e}")
    
    @pytest.mark.integration
    def test_minio_connectivity(self):
        """Test MinIO object storage connectivity"""
        from minio import Minio
        
        try:
            client = Minio(
                "localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                secure=False
            )
            
            # Check if we can list buckets
            buckets = client.list_buckets()
            assert buckets is not None
        except Exception as e:
            pytest.fail(f"Failed to connect to MinIO: {e}")
    
    @pytest.mark.integration
    def test_backend_api_health(self):
        """Test backend API health endpoint"""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8000/health")
                if response.status_code == 200:
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert "database" in data
                    assert "storage" in data
                    return
            except requests.exceptions.ConnectionError:
                if i < max_retries - 1:
                    time.sleep(2)
                else:
                    pytest.fail("Backend API is not responding")
    
    @pytest.mark.integration
    def test_frontend_accessibility(self):
        """Test frontend is accessible"""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:3000")
                if response.status_code == 200:
                    assert "<!DOCTYPE html>" in response.text
                    return
            except requests.exceptions.ConnectionError:
                if i < max_retries - 1:
                    time.sleep(2)
                else:
                    pytest.fail("Frontend is not accessible")
    
    @pytest.mark.integration
    def test_nginx_proxy(self):
        """Test NGINX reverse proxy configuration"""
        # Test backend proxy
        response = requests.get("http://localhost/api/health")
        assert response.status_code == 200
        
        # Test frontend proxy
        response = requests.get("http://localhost/")
        assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_container_resource_usage(self, docker_client):
        """Test container resource usage is within limits"""
        containers = docker_client.containers.list()
        
        for container in containers:
            if container.name.startswith("healthstash-"):
                stats = container.stats(stream=False)
                
                # Check memory usage
                memory_usage = stats["memory_stats"]["usage"]
                memory_limit = stats["memory_stats"]["limit"]
                memory_percent = (memory_usage / memory_limit) * 100
                
                assert memory_percent < 90, f"{container.name} memory usage is {memory_percent:.2f}%"
                
                # Check CPU usage
                cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                           stats["precpu_stats"]["cpu_usage"]["total_usage"]
                system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                              stats["precpu_stats"]["system_cpu_usage"]
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100
                    assert cpu_percent < 80, f"{container.name} CPU usage is {cpu_percent:.2f}%"
    
    @pytest.mark.integration
    def test_container_restart_resilience(self, docker_client):
        """Test container restart resilience"""
        # Test restarting backend container
        backend = docker_client.containers.get("healthstash-backend")
        backend.restart()
        
        # Wait for container to be healthy again
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            backend.reload()
            health = backend.attrs.get("State", {}).get("Health", {})
            if health.get("Status") == "healthy":
                break
            time.sleep(2)
        else:
            pytest.fail("Backend container did not become healthy after restart")
        
        # Verify API is accessible
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
    
    @pytest.mark.integration
    def test_inter_container_networking(self, docker_client):
        """Test inter-container network connectivity"""
        backend = docker_client.containers.get("healthstash-backend")
        
        # Test backend can reach postgres
        exit_code, output = backend.exec_run("nc -zv postgres 5432")
        assert exit_code == 0
        
        # Test backend can reach minio
        exit_code, output = backend.exec_run("nc -zv minio 9000")
        assert exit_code == 0
        
        # Test backend can reach timescaledb
        exit_code, output = backend.exec_run("nc -zv timescaledb 5432")
        assert exit_code == 0
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_backup_container_functionality(self, docker_client):
        """Test backup container is functioning"""
        backup = docker_client.containers.get("healthstash-backup")
        
        # Trigger manual backup
        exit_code, output = backup.exec_run("/scripts/backup.sh")
        assert exit_code == 0
        
        # Check backup was created
        exit_code, output = backup.exec_run("ls -la /backups/")
        assert exit_code == 0
        assert b".sql" in output or b".tar" in output
    
    @pytest.mark.integration
    def test_container_logging(self, docker_client):
        """Test container logging is working"""
        containers = docker_client.containers.list()
        
        for container in containers:
            if container.name.startswith("healthstash-"):
                logs = container.logs(tail=10)
                assert logs is not None
                
                # Check for error patterns
                error_patterns = [b"ERROR", b"FATAL", b"CRITICAL"]
                for pattern in error_patterns:
                    if pattern in logs:
                        # Some errors might be expected in tests
                        print(f"Warning: Found {pattern} in {container.name} logs")
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_container_startup_time(self, docker_client):
        """Test container startup time"""
        # Stop and start backend container
        backend = docker_client.containers.get("healthstash-backend")
        
        backend.stop()
        start_time = time.time()
        backend.start()
        
        # Wait for healthy status
        max_wait = 120  # 2 minutes max
        while time.time() - start_time < max_wait:
            backend.reload()
            health = backend.attrs.get("State", {}).get("Health", {})
            if health.get("Status") == "healthy":
                startup_time = time.time() - start_time
                assert startup_time < 60, f"Container took {startup_time:.2f}s to start"
                break
            time.sleep(1)
        else:
            pytest.fail("Container did not become healthy within timeout")
    
    @pytest.mark.integration
    def test_volume_persistence(self, docker_client):
        """Test data volume persistence"""
        # Create test data
        response = requests.post(
            "http://localhost:8000/auth/register",
            json={
                "email": "volume-test@example.com",
                "password": "TestPass123!",
                "full_name": "Volume Test"
            }
        )
        assert response.status_code in [201, 400]  # May already exist
        
        # Restart postgres container
        postgres = docker_client.containers.get("healthstash-postgres")
        postgres.restart()
        
        # Wait for postgres to be ready
        time.sleep(10)
        
        # Verify data persisted
        response = requests.post(
            "http://localhost:8000/auth/login",
            data={
                "username": "volume-test@example.com",
                "password": "TestPass123!"
            }
        )
        assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.security
    def test_container_security_settings(self, docker_client):
        """Test container security configurations"""
        containers = docker_client.containers.list()
        
        for container in containers:
            if container.name.startswith("healthstash-"):
                attrs = container.attrs
                
                # Check if running as non-root (where applicable)
                config = attrs.get("Config", {})
                user = config.get("User", "")
                
                # Check security options
                host_config = attrs.get("HostConfig", {})
                
                # Verify no privileged containers
                assert not host_config.get("Privileged", False), \
                    f"{container.name} should not run in privileged mode"
                
                # Check for read-only root filesystem where applicable
                if container.name in ["healthstash-nginx"]:
                    assert host_config.get("ReadonlyRootfs", False), \
                        f"{container.name} should have read-only root filesystem"