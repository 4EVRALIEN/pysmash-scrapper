"""
Pytest configuration and fixtures.
"""
import os
import tempfile
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from scraper.database.repository import SmashUpRepository


@pytest.fixture(scope="session")
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary file for the test database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    # Set environment variable for tests
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    
    yield db_path
    
    # Clean up
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def test_repository(temp_db):
    """Create a test repository with temporary database."""
    return SmashUpRepository(f"sqlite:///{temp_db}")


@pytest.fixture
def test_client(temp_db):
    """Create a test client with temporary database."""
    # Import after setting environment variable
    from scraper.api import app
    
    return TestClient(app)


@pytest.fixture
def mock_web_client():
    """Create a mock web client for testing."""
    client = Mock()
    client.BASE_URL = "https://smashup.fandom.com/wiki/"
    return client