"""
Pytest configuration and fixtures for FastAPI tests.
Automatically loads test data before running tests.
"""
import os
import sys
import subprocess
import time
import pytest
import requests
from pathlib import Path

# Add server directory to Python path so tests can import local code
server_dir = Path(__file__).parent.parent.parent / "server"
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))


def load_test_data():
    """Load test data using the existing restore-db script."""
    # Get the path to test-data.sql
    test_data_path = Path(__file__).parent.parent / "test-data.sql"
    
    if not test_data_path.exists():
        pytest.skip(f"Test data file not found: {test_data_path}")
    
    # Get the path to restore-db script
    restore_script = Path(__file__).parent.parent.parent / "gwtm-helm" / "restore-db"
    
    if not restore_script.exists():
        pytest.skip(f"restore-db script not found: {restore_script}")
    
    try:
        # Run the restore-db script with proper environment and stdin
        print(f"Loading test data from {test_data_path}")
        print(f"Running: {restore_script} {test_data_path}")
        
        # Try with a shorter timeout first to see what happens
        result = subprocess.run(
            [str(restore_script), str(test_data_path)],
            capture_output=True,
            text=True,
            timeout=10,  # Short timeout to debug
            cwd=Path(__file__).parent.parent.parent,  # Run from project root
            stdin=subprocess.DEVNULL,  # Prevent hanging on input
            env=os.environ.copy()  # Pass through environment
        )
        
        if result.returncode != 0:
            print(f"restore-db failed with return code {result.returncode}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            pytest.skip("Failed to load test data")
        
        print("Test data loaded successfully")
        print(f"stdout: {result.stdout}")
        
    except subprocess.TimeoutExpired as e:
        print(f"Test data loading timed out after 10 seconds")
        print(f"Command: {e.cmd}")
        # Try to get partial output
        if hasattr(e, 'stdout') and e.stdout:
            print(f"Partial stdout: {e.stdout}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Partial stderr: {e.stderr}")
        pytest.skip("Test data loading timed out - check kubectl access")
    except Exception as e:
        print(f"Error loading test data: {e}")
        pytest.skip(f"Error loading test data: {e}")


def wait_for_api():
    """Wait for the FastAPI server to be ready."""
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    health_url = f"{api_url}/health"
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print(f"API is ready at {api_url}")
                return
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            print(f"Waiting for API to be ready... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
    
    pytest.skip(f"API not ready after {max_attempts} attempts")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Session-level fixture that runs once before all tests.
    Waits for API to be ready and loads test data.
    """
    print("Setting up test environment...")
    
    # Wait for API to be ready
    wait_for_api()
    
    # Load test data
    load_test_data()
    
    print("Test environment setup complete")


@pytest.fixture(scope="function")
def api_base_url():
    """Provide the API base URL for tests."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="function") 
def api_headers():
    """Provide common API headers."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


@pytest.fixture(scope="function")
def test_tokens():
    """Provide test API tokens from test data."""
    return {
        "admin": "test_token_admin_001",
        "user": "test_token_user_002", 
        "scientist": "test_token_sci_003",
        "invalid": "invalid_token_123"
    }


@pytest.fixture(scope="function")
def test_graceids():
    """Provide known GraceIDs from test data."""
    return ['S190425z', 'S190426c', 'MS230101a', 'GW190521', 'MS190425a']