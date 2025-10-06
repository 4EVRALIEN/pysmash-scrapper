"""
Tests for the FastAPI application.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from scraper.api import app
from scraper.models import HealthCheck


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check(self, client):
        """Test that health endpoint returns correct response."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestSetsEndpoint:
    """Test the sets-related endpoints."""
    
    @patch('scraper.api.repository')
    def test_get_sets_success(self, mock_repository, client):
        """Test successful retrieval of sets."""
        # Mock repository response
        mock_sets = [
            {
                "set_id": "test_id_1",
                "set_name": "Core Set",
                "set_url": "https://smashup.fandom.com/wiki/Core_Set",
                "created_at": "2023-01-01T00:00:00"
            }
        ]
        mock_repository.get_all_sets.return_value = mock_sets
        
        response = client.get("/sets")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["set_name"] == "Core Set"
    
    @patch('scraper.api.repository')
    def test_get_sets_error(self, mock_repository, client):
        """Test error handling when getting sets fails."""
        mock_repository.get_all_sets.side_effect = Exception("Database error")
        
        response = client.get("/sets")
        
        assert response.status_code == 500
        assert "Failed to retrieve sets" in response.json()["detail"]


class TestFactionsEndpoint:
    """Test the factions-related endpoints."""
    
    @patch('scraper.api.repository')
    def test_get_factions_by_set_success(self, mock_repository, client):
        """Test successful retrieval of factions for a set."""
        # Mock repository response
        mock_factions = [
            {
                "faction_id": "test_faction_id",
                "faction_name": "Robots",
                "faction_url": "https://smashup.fandom.com/wiki/Robots",
                "set_id": "test_set_id",
                "created_at": "2023-01-01T00:00:00"
            }
        ]
        mock_repository.get_factions_by_set.return_value = mock_factions
        
        response = client.get("/sets/test_set_id/factions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["faction_name"] == "Robots"
    
    @patch('scraper.api.repository')
    def test_get_factions_by_set_not_found(self, mock_repository, client):
        """Test when no factions are found for a set."""
        mock_repository.get_factions_by_set.return_value = []
        
        response = client.get("/sets/nonexistent_set/factions")
        
        assert response.status_code == 404
        assert "Set not found" in response.json()["detail"]


class TestScrapingEndpoints:
    """Test the scraping trigger endpoints."""
    
    def test_scrape_faction_success(self, client):
        """Test successful faction scraping trigger."""
        response = client.post("/scrape/faction/Robots")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "started in background" in data["message"]
    
    def test_scrape_set_success(self, client):
        """Test successful set scraping trigger."""
        response = client.post("/scrape/set/Core_Set")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "started in background" in data["message"]
    
    def test_scrape_all_success(self, client):
        """Test successful full scraping trigger."""
        response = client.post("/scrape/all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "started in background" in data["message"]


class TestDatabaseEndpoints:
    """Test database management endpoints."""
    
    @patch('scraper.api.repository')
    def test_clear_database_success(self, mock_repository, client):
        """Test successful database clearing."""
        mock_repository.clear_all_data.return_value = True
        
        response = client.delete("/data/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert "cleared successfully" in data["message"]
    
    @patch('scraper.api.repository')
    def test_clear_database_failure(self, mock_repository, client):
        """Test database clearing failure."""
        mock_repository.clear_all_data.return_value = False
        
        response = client.delete("/data/clear")
        
        assert response.status_code == 500
        assert "Failed to clear database" in response.json()["detail"]
