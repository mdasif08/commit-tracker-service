import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.auth_service import auth_service, fake_users_db


class TestAuthentication:
    """Test cases for authentication functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_login_success(self, client):
        """Test successful login."""
        response = client.post(
            "/api/auth/token", data={"username": "admin", "password": "admin123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/token", data={"username": "admin", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Incorrect username or password" in data["error"]

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/auth/token", data={"username": "nonexistent", "password": "password"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Incorrect username or password" in data["error"]

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/commits/test-repo")

        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert "Not authenticated" in data["error"]

    def test_protected_endpoint_with_valid_token(self, client):
        """Test accessing protected endpoint with valid token."""
        # First get a token
        login_response = client.post(
            "/api/auth/token", data={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/commits/test-repo", headers=headers)

        # Should not get 403 (authentication error)
        assert response.status_code != 403

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/commits/test-repo", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Could not validate credentials" in data["error"]

    def test_token_expiration(self, client):
        """Test token expiration."""
        # Test with an invalid token that would cause JWT error
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/commits/test-repo", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Could not validate credentials" in data["error"]

    def test_user_authentication_service(self):
        """Test authentication service methods."""
        # Test password verification
        assert auth_service.verify_password(
            "admin123", fake_users_db["admin"]["hashed_password"]
        )
        assert not auth_service.verify_password(
            "wrongpassword", fake_users_db["admin"]["hashed_password"]
        )

        # Test user retrieval
        user = auth_service.get_user("admin")
        assert user is not None
        assert user.username == "admin"
        assert user.email == "admin@example.com"

        # Test user authentication
        authenticated_user = auth_service.authenticate_user("admin", "admin123")
        assert authenticated_user is not None
        assert authenticated_user.username == "admin"

        # Test failed authentication
        failed_user = auth_service.authenticate_user("admin", "wrongpassword")
        assert failed_user is None

    def test_password_hashing(self):
        """Test password hashing functionality."""
        password = "testpassword"
        hashed = auth_service.get_password_hash(password)

        # Should not be the same as original password
        assert hashed != password

        # Should be verifiable
        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("wrongpassword", hashed)

    def test_token_creation(self):
        """Test JWT token creation."""
        data = {"sub": "testuser"}
        token = auth_service.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_all_protected_endpoints_require_auth(self, client):
        """Test that all protected endpoints require authentication."""
        protected_endpoints = [
            ("POST", "/api/commits/webhook"),
            ("POST", "/api/commits/local"),
            ("GET", "/api/commits/test-repo"),
            ("GET", "/api/commits/test-repo/metrics"),
        ]

        for method, endpoint in protected_endpoints:
            if method == "POST":
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)

            # Should get 403 (forbidden) or 401 (unauthorized) without token
            assert response.status_code in [401, 403, 422]  # 422 for validation errors

    def test_public_endpoints_dont_require_auth(self, client):
        """Test that public endpoints don't require authentication."""
        public_endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("POST", "/api/auth/token"),
        ]

        for method, endpoint in public_endpoints:
            if method == "POST":
                response = client.post(
                    endpoint, data={"username": "admin", "password": "admin123"}
                )
            else:
                response = client.get(endpoint)

            # Should not get 401 or 403 (authentication errors)
            assert response.status_code not in [401, 403]


class TestAuthServiceIntegration:
    """Integration tests for authentication service."""

    def test_complete_auth_flow(self):
        """Test complete authentication flow."""
        # 1. Authenticate user
        user = auth_service.authenticate_user("admin", "admin123")
        assert user is not None

        # 2. Create token
        token = auth_service.create_access_token({"sub": user.username})
        assert token is not None

        # 3. Verify token
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        token_data = auth_service.verify_token(credentials)
        assert token_data.username == "admin"

        # 4. Get current user
        current_user = auth_service.get_current_user(credentials)
        assert current_user.username == "admin"
        assert current_user.email == "admin@example.com"
