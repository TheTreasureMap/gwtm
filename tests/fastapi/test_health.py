"""
Test health check endpoints with real requests to the FastAPI application.
"""
import os
import requests
import json
import datetime
import pytest
from fastapi import status


# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class TestHealthEndpoints:
    """Test class for health check API endpoints."""

    def get_url(self, endpoint):
        """Get full URL for an endpoint."""
        return f"{API_BASE_URL}{endpoint}"

    def test_health_endpoint(self):
        """Test the basic health check endpoint."""
        response = requests.get(self.get_url("/health"))
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "time" in data
        
        # Verify time is recent (within last minute)
        time_str = data["time"]
        time = datetime.datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        difference = now - time.astimezone(datetime.timezone.utc)
        assert difference.total_seconds() < 60  # Within the last minute

    def test_service_status_endpoint(self):
        """Test the detailed service status endpoint."""
        response = requests.get(self.get_url("/service-status"))
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check that the response has the expected structure
        assert "database_status" in data
        assert "redis_status" in data
        assert "details" in data
        assert "database" in data["details"]
        assert "redis" in data["details"]
        
        # Check database details
        database = data["details"]["database"]
        assert "host" in database
        assert "port" in database
        assert "name" in database
        
        # Check redis details
        redis = data["details"]["redis"]
        assert "host" in redis
        assert "port" in redis
        assert "url" in redis
        
        # If database connection is successful, status should be "connected"
        # If not, there should be an error message
        if data["database_status"] == "connected":
            assert data["database_status"] == "connected"
        else:
            assert "error" in database
        
        # Similarly for Redis
        if data["redis_status"] == "connected":
            assert data["redis_status"] == "connected"
        else:
            assert "error" in redis


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
