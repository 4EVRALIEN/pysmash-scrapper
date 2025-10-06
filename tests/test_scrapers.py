"""
Tests for the scraper modules.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from bs4 import BeautifulSoup

from scraper.models import ScrapingResult
from scraper.scrapers.base_scraper import BaseScraper
from scraper.scrapers.card_scraper import CardScraper
from scraper.scrapers.faction_scraper import FactionScraper
from scraper.scrapers.set_scraper import SetScraper
from scraper.utils.web_client import SmashUpWebClient


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

    def test_context_manager(self):
        """Test that scraper works as context manager."""
        with patch("scraper.utils.web_client.SmashUpWebClient") as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance

            with BaseScraper() as scraper:
                assert scraper is not None

            # Should close client when exiting context
            mock_instance.close.assert_called_once()


class TestSetScraper:
    """Test the set scraper functionality."""

    @pytest.fixture
    def mock_web_client(self):
        """Mock web client for testing."""
        client = Mock(spec=SmashUpWebClient)
        client.BASE_URL = "https://smashup.fandom.com/wiki/"
        return client

    @pytest.fixture
    def set_scraper(self, mock_web_client):
        """Set scraper with mocked web client."""
        return SetScraper(mock_web_client)

    def test_get_available_sets(self, set_scraper):
        """Test getting available sets."""
        sets = set_scraper.get_available_sets()

        assert isinstance(sets, list)
        assert len(sets) > 0
        assert "Core_Set" in sets

    def test_scrape_set_data(self, set_scraper):
        """Test scraping basic set data."""
        set_name = "Core_Set"
        set_data = set_scraper.scrape_set_data(set_name)

        assert set_data.set_name == set_name
        assert set_data.set_id is not None
        assert set_data.set_url.endswith(set_name)

    @patch("scraper.scrapers.set_scraper.BeautifulSoup")
    def test_scrape_set_factions_success(self, mock_soup, set_scraper):
        """Test successful faction scraping from set page."""
        # Mock HTML structure
        mock_img1 = Mock()
        mock_img1.get.return_value = "Robots"
        mock_img2 = Mock()
        mock_img2.get.return_value = "Dinosaurs"

        mock_gallery = Mock()
        mock_gallery.find_all.return_value = [mock_img1, mock_img2]

        mock_soup_instance = Mock()
        mock_soup_instance.find.return_value = mock_gallery
        mock_soup.return_value = mock_soup_instance

        # Mock web client response
        mock_response = Mock()
        mock_response.content = "<html></html>"
        set_scraper.web_client.get_page.return_value = mock_response

        factions = set_scraper.scrape_set_factions("Core_Set")

        assert "Robots" in factions
        assert "Dinosaurs" in factions
        assert len(factions) == 2

    def test_scrape_set_factions_no_gallery(self, set_scraper):
        """Test faction scraping when no gallery is found."""
        # Mock web client to return response but soup finds no gallery
        mock_response = Mock()
        mock_response.content = "<html></html>"
        set_scraper.web_client.get_page.return_value = mock_response

        with patch("scraper.scrapers.set_scraper.BeautifulSoup") as mock_soup:
            mock_soup_instance = Mock()
            mock_soup_instance.find.return_value = None  # No gallery
            mock_soup.return_value = mock_soup_instance

            factions = set_scraper.scrape_set_factions("Test_Set")

            assert len(factions) == 0


class TestFactionScraper:
    """Test the faction scraper functionality."""

    @pytest.fixture
    def mock_web_client(self):
        """Mock web client for testing."""
        client = Mock(spec=SmashUpWebClient)
        client.BASE_URL = "https://smashup.fandom.com/wiki/"
        return client

    @pytest.fixture
    def faction_scraper(self, mock_web_client):
        """Faction scraper with mocked web client."""
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
        """Test special URL handling for Cthulhu faction."""
        faction_name = "Cthulhu"
        set_id = "test_set_id"

        faction_data = faction_scraper.scrape_faction_data(faction_name, set_id)

        assert "Minions_of_Cthulhu" in faction_data.faction_url


class TestCardScraper:
    """Test the card scraper functionality."""

    @pytest.fixture
    def mock_web_client(self):
        """Mock web client for testing."""
        client = Mock(spec=SmashUpWebClient)
        return client

    @pytest.fixture
    def card_scraper(self, mock_web_client):
        """Card scraper with mocked web client."""
        return CardScraper(mock_web_client)

    def test_parse_minion_card(self, card_scraper):
        """Test parsing a minion card from text."""
        text = "Robot Walker - power 3 - Move a minion to another base."
        card_name = "Robot Walker"
        faction_name = "Robots"
        faction_id = "test_faction_id"

        card = card_scraper._parse_card_from_text(
            text, card_name, faction_name, faction_id
        )

        assert card is not None
        assert hasattr(card, "power")  # Should be a MinionCard
        assert card.power == 3
        assert card.name == card_name
        assert card.faction_name == faction_name
        assert card.faction_id == faction_id

    def test_parse_action_card(self, card_scraper):
        """Test parsing an action card from text."""
        text = "Laser Blast - Destroy a minion with power 3 or less."
        card_name = "Laser Blast"
        faction_name = "Robots"
        faction_id = "test_faction_id"

        card = card_scraper._parse_card_from_text(
            text, card_name, faction_name, faction_id
        )

        assert card is not None
        assert not hasattr(card, "power")  # Should be an ActionCard
        assert card.name == card_name
        assert card.faction_name == faction_name
        assert card.faction_id == faction_id

    @patch("scraper.scrapers.card_scraper.BeautifulSoup")
    def test_scrape_faction_cards_success(self, mock_soup, card_scraper):
        """Test successful card scraping from faction page."""
        # Mock HTML structure with card data
        mock_span1 = Mock()
        mock_span1.get.return_value = "Robot Walker"
        mock_p1 = Mock()
        mock_p1.find.return_value = mock_span1
        mock_p1.text = "Robot Walker - power 3 - Move a minion to another base."

        mock_span2 = Mock()
        mock_span2.get.return_value = "Laser Blast"
        mock_p2 = Mock()
        mock_p2.find.return_value = mock_span2
        mock_p2.text = "Laser Blast - Destroy a minion with power 3 or less."

        mock_soup_instance = Mock()
        mock_soup_instance.find_all.return_value = [mock_p1, mock_p2]
        mock_soup.return_value = mock_soup_instance

        # Mock web client response
        mock_response = Mock()
        mock_response.content = "<html></html>"
        card_scraper.web_client.get_faction_page.return_value = mock_response

        result = card_scraper.scrape_faction_cards("Robots", "test_faction_id")

        assert result.success
        assert result.items_processed == 2
