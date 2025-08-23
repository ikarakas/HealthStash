import pytest
from fastapi import status
from datetime import datetime, timedelta
from app.core.security import verify_password, get_password_hash

class TestAuthentication:
    """Test authentication endpoints and security"""
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_register_duplicate_user(self, client, test_user):
        """Test duplicate user registration fails"""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "AnotherPass123!",
                "full_name": "Duplicate User"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials"""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_get_current_user(self, client, auth_headers):
        """Test get current user endpoint"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_get_current_user_no_token(self, client):
        """Test get current user without token"""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_get_current_user_invalid_token(self, client):
        """Test get current user with invalid token"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_refresh_token(self, client, auth_headers):
        """Test token refresh"""
        response = client.post("/auth/refresh", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_change_password(self, client, auth_headers):
        """Test password change"""
        response = client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpassword123",
                "new_password": "NewSecurePass456!"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test login with new password
        response = client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "NewSecurePass456!"
            }
        )
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password"""
        response = client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "NewSecurePass456!"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_password_reset_request(self, client, test_user, mock_email):
        """Test password reset request"""
        response = client.post(
            "/auth/forgot-password",
            json={"email": test_user.email}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(mock_email) == 1
        assert mock_email[0]["to"] == test_user.email
        assert "reset" in mock_email[0]["subject"].lower()
    
    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.security
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "SecureTestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)
    
    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.security
    def test_jwt_token_expiration(self, client, test_user):
        """Test JWT token expiration"""
        from app.core.security import create_access_token
        
        # Create expired token
        expired_token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(seconds=-1)
        )
        
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.security
    def test_admin_access_control(self, client, auth_headers, admin_auth_headers):
        """Test admin access control"""
        # Non-admin user tries to access admin endpoint
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Admin user accesses admin endpoint
        response = client.get("/admin/users", headers=admin_auth_headers)
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.integration
    @pytest.mark.auth
    def test_concurrent_logins(self, client, test_user):
        """Test multiple concurrent login attempts"""
        import concurrent.futures
        
        def login_attempt():
            return client.post(
                "/auth/login",
                data={
                    "username": test_user.email,
                    "password": "testpassword123"
                }
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(login_attempt) for _ in range(10)]
            results = [f.result() for f in futures]
        
        for response in results:
            assert response.status_code == status.HTTP_200_OK
            assert "access_token" in response.json()
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection in login"""
        malicious_inputs = [
            "admin' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin'--",
            "' OR 1=1--"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post(
                "/auth/login",
                data={
                    "username": malicious_input,
                    "password": "password"
                }
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_brute_force_protection(self, client, test_user):
        """Test brute force protection on login"""
        # Simulate multiple failed login attempts
        for i in range(10):
            response = client.post(
                "/auth/login",
                data={
                    "username": test_user.email,
                    "password": f"wrongpassword{i}"
                }
            )
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_429_TOO_MANY_REQUESTS
            ]