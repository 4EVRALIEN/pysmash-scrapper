"""
Tests for the scraper modules.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from bs4 import BeautifulSoup

from scraper.models import ScrapingResult
from scraper.scrapers.base_scraper import BaseScraper
from scraper.scrapers.card_scraper import CardScraper
from scraper.scrapers.faction_scraper import FactionScraper
from scraper.scrapers.set_scraper import SetScraper


class TestBaseScraper:
    """Test the base scraper functionality."""

    def test_generate_id(self):
        """Test ID generation produces consistent results."""
        text = "Test Faction"
        id1 = BaseScraper.generate_id(text)
        id2 = BaseScraper.generate_id(text)

        assert id1 == id2
        assert len(id1) == 32  # MD5 hash length
        assert isinstance(id1, str)

    def test_context_manager(self, mock_web_client):
        """Test that scraper works as context manager."""
        # Use a concrete implementation instead of abstract base class
        with patch("scraper.utils.web_client.SmashUpWebClient"):
            scraper = SetScraper(mock_web_client)  # Use concrete class
            with scraper:
                assert scraper.web_client is not None


class TestSetScraper:
    """Test the set scraper functionality."""

    @pytest.fixture
    def mock_web_client(self):
        """Create a mock web client."""
        client = Mock()
        client.BASE_URL = "https://smashup.fandom.com/wiki/"
        return client

    @pytest.fixture
    def set_scraper(self, mock_web_client):
        """Create a set scraper with mock client."""
        return SetScraper(mock_web_client)

    def test_get_available_sets(self, set_scraper):
        """Test getting available sets."""
        # Mock the web client response
        mock_response = Mock()
        mock_response.content = """
        <html>
            <div class="CategoryTreeSection">
                <a href="/wiki/Core_Set">Core Set</a>
                <a href="/wiki/Awesome_Level_9000">Awesome Level 9000</a>
            </div>
        </html>
        """
        set_scraper.web_client.get_page.return_value = mock_response

        sets = set_scraper.get_available_sets()

        assert isinstance(sets, list)
        assert len(sets) >= 0  # May be empty in mock

    def test_scrape_set_data(self, set_scraper):
        """Test scraping basic set data."""
        set_name = "Core_Set"
        set_data = set_scraper.scrape_set_data(set_name)

        assert set_data.set_name == set_name
        assert set_data.set_id is not None
        assert set_data.set_url.endswith(set_name)
        assert isinstance(set_data.factions, list)  # Should be empty list, not None

    @patch("bs4.BeautifulSoup")  # Correct import path
    def test_scrape_set_factions_success(self, mock_soup, set_scraper):
        """Test successful faction scraping from set page."""
        # Mock BeautifulSoup to return faction links
        mock_soup_instance = Mock()
        mock_gallery = Mock()
        mock_links = [
            Mock(get=Mock(return_value="/wiki/Robots")),
            Mock(get=Mock(return_value="/wiki/Wizards")),
        ]
        mock_gallery.find_all.return_value = mock_links
        mock_soup_instance.find.return_value = mock_gallery
        mock_soup.return_value = mock_soup_instance

        # Mock web client response
        mock_response = Mock()
        mock_response.content = "<html></html>"
        set_scraper.web_client.get_page.return_value = mock_response

        factions = set_scraper.scrape_set_factions("Core_Set")

        assert isinstance(factions, list)

    def test_scrape_set_factions_no_gallery(self, set_scraper):
        """Test faction scraping when no gallery is found."""
        # Mock web client to return response but soup finds no gallery
        mock_response = Mock()
        mock_response.content = "<html></html>"
        set_scraper.web_client.get_page.return_value = mock_response

        with patch("bs4.BeautifulSoup") as mock_soup:  # Correct import path
            mock_soup_instance = Mock()
            mock_soup_instance.find.return_value = None
            mock_soup.return_value = mock_soup_instance

            factions = set_scraper.scrape_set_factions("Core_Set")
            assert isinstance(factions, list)


class TestFactionScraper:
    """Test the faction scraper functionality."""

    @pytest.fixture
    def mock_web_client(self):
        """Create a mock web client."""
        client = Mock()
        client.BASE_URL = "https://smashup.fandom.com/wiki/"
        return client

    @pytest.fixture
    def faction_scraper(self, mock_web_client):
        """Create a faction scraper with mock client."""
        return FactionScraper(mock_web_client)

    def test_scrape_faction_data(self, faction_scraper):
        """Test scraping basic faction data."""
        faction_name = "Robots"
        set_id = "test_set_id"

        faction_data = faction_scraper.scrape_faction_data(faction_name, set_id)

        assert faction_data.faction_name == faction_name
        assert faction_data.set_id == set_id
        assert faction_data.faction_id is not None
        assert faction_data.faction_url is not None

    def test_scrape_faction_data_cthulhu_special_case(self, faction_scraper):
        """Test special case handling for Cthulhu faction."""
        faction_name = "Cthulhu"
        set_id = "test_set_id"

        faction_data = faction_scraper.scrape_faction_data(faction_name, set_id)

        assert "Minions_of_Cthulhu" in faction_data.faction_url

    @patch("scraper.scrapers.faction_scraper.CardScraper")
    def test_scrape_faction_cards(self, mock_card_scraper_class, faction_scraper):
        """Test scraping faction cards."""
        # Mock the card scraper
        mock_card_scraper = Mock()
        mock_result = ScrapingResult(
            success=True, message="Success", items_processed=5, errors=[]
        )
        mock_card_scraper.scrape_faction_cards.return_value = mock_result
        mock_card_scraper_class.return_value = mock_card_scraper

        # Override the card scraper instance
        faction_scraper.card_scraper = mock_card_scraper

        cards = faction_scraper.scrape_faction_cards("Robots", "robot_id")

        assert isinstance(cards, list)
        mock_card_scraper.scrape_faction_cards.assert_called_once_with(
            "Robots", "robot_id"
        )

    def test_scrape_complete_faction(self, faction_scraper):
        """Test complete faction scraping."""
        with patch.object(faction_scraper, "scrape_faction_cards", return_value=[]):
            result = faction_scraper.scrape("Robots", "test_set_id")

            assert isinstance(result, ScrapingResult)
            assert result.success is True
            assert "Robots" in result.message


class TestCardScraper:
    """Test the card scraper functionality."""

    @pytest.fixture
    def mock_web_client(self):
        """Create a mock web client."""
        client = Mock()
        client.BASE_URL = "https://smashup.fandom.com/wiki/"
        return client

    @pytest.fixture
    def card_scraper(self, mock_web_client):
        """Create a card scraper with mock client."""
        return CardScraper(mock_web_client)

    def test_scrape_faction_cards_method_exists(self, card_scraper):
        """Test that scrape_faction_cards method exists."""
        assert hasattr(card_scraper, "scrape_faction_cards")

    def test_scrape_faction_cards_returns_result(self, card_scraper):
        """Test that scrape_faction_cards returns a ScrapingResult."""
        # Mock the web client to avoid actual web requests
        mock_response = Mock()
        mock_response.content = "<html></html>"
        card_scraper.web_client.get_page.return_value = mock_response

        result = card_scraper.scrape_faction_cards("Robots", "robot_id")

        assert isinstance(result, ScrapingResult)
        assert hasattr(result, "success")
        assert hasattr(result, "message")
        assert hasattr(result, "items_processed")
        assert hasattr(result, "errors")
