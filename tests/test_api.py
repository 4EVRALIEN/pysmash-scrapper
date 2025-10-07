"""
Tests for the FastAPI application.
"""

import json
from unittest.mock import patch

import pytest


def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_get_sets_empty(test_client):
    """Test getting sets when database is empty."""
    response = test_client.get("/sets")
    assert response.status_code == 200
    assert response.json() == []


def test_get_factions_by_set_not_found(test_client):
    """Test getting factions for non-existent set."""
    response = test_client.get("/sets/nonexistent/factions")
    assert response.status_code == 404


@patch("scraper.api._background_scrape_faction")
def test_scrape_faction(mock_background_task, test_client):
    """Test triggering faction scraping."""
    response = test_client.post("/scrape/faction/Robots")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "Robots" in data["message"]
    assert data["items_processed"] == 0


@patch("scraper.api._background_scrape_set")
def test_scrape_set(mock_background_task, test_client):
    """Test triggering set scraping."""
    response = test_client.post("/scrape/set/Core_Set")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "Core_Set" in data["message"]


@patch("scraper.api._background_scrape_all")
def test_scrape_all(mock_background_task, test_client):
    """Test triggering full scraping."""
    response = test_client.post("/scrape/all")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "scraping started" in data["message"]


def test_clear_database(test_client):
    """Test clearing the database."""
    response = test_client.delete("/data/clear")
    assert response.status_code == 200

    data = response.json()
    assert "cleared successfully" in data["message"]
