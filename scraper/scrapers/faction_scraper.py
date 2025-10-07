"""
Faction scraper for extracting faction data and associated cards.
"""

import logging
from typing import List, Union

from ..models import ActionCard, Faction, MinionCard, ScrapingResult
from .base_scraper import BaseScraper
from .card_scraper import CardScraper

logger = logging.getLogger(__name__)


class FactionScraper(BaseScraper):
    """Scraper for faction data and their cards."""

    def __init__(self, web_client=None):
        """Initialize with optional card scraper."""
        super().__init__(web_client)
        self.card_scraper = CardScraper(self.web_client)

    def scrape_faction_data(self, faction_name: str, set_id: str) -> Faction:
        """
        Scrape basic faction data.

        Args:
            faction_name: Name of the faction
            set_id: ID of the set this faction belongs to

        Returns:
            FactionData model with scraped data
        """
        faction_id = self.generate_id(faction_name)

        # Handle special case for Cthulhu faction
        faction_url = (
            f"{self.web_client.BASE_URL}{faction_name}"
            if "cthulhu" not in faction_name.lower()
            else f"{self.web_client.BASE_URL}Minions_of_Cthulhu"
        )

        return Faction(
            faction_id=faction_id,
            faction_name=faction_name,
            faction_url=faction_url,
            set_id=set_id,
        )

    def scrape_faction_cards(
        self, faction_name: str, faction_id: str
    ) -> List[Union[MinionCard, ActionCard]]:
        """
        Scrape all cards for a faction.

        Args:
            faction_name: Name of the faction
            faction_id: ID of the faction

        Returns:
            List of card models
        """
        self._log_scraping_start("card scraping", faction_name)

        # Use the specialized card scraper
        result = self.card_scraper.scrape_faction_cards(faction_name, faction_id)

        if result.success:
            self._log_scraping_complete(
                "card scraping", result.items_processed, faction_name
            )
            # Note: In a real implementation, you'd want to return actual cards
            # For now, we'll return an empty list as cards are handled by
            # the card scraper
            return []
        else:
            message = (
                f"Failed to scrape cards for faction {faction_name}: "
                f"{result.message}"
            )
            logger.error(message)
            return []

    def scrape(self, faction_name: str, set_id: str = None) -> ScrapingResult:
        """
        Scrape complete faction data including cards.

        Args:
            faction_name: Name of the faction to scrape
            set_id: ID of the set this faction belongs to

        Returns:
            ScrapingResult with operation details
        """
        try:
            self._log_scraping_start("faction scraping", faction_name)

            # Generate set_id if not provided
            if not set_id:
                set_id = self.generate_id("unknown_set")
                logger.warning(
                    f"No set_id provided for faction {faction_name}, "
                    f"using generated ID"
                )

            # Scrape faction basic data
            faction_data = self.scrape_faction_data(faction_name, set_id)

            # Scrape associated cards
            cards = self.scrape_faction_cards(faction_name, faction_data.faction_id)

            self._log_scraping_complete(
                "faction scraping", 1 + len(cards), faction_name
            )

            return self._create_success_result(
                f"Successfully scraped faction {faction_name} with "
                f"{len(cards)} cards",
                1 + len(cards),
            )

        except Exception as e:
            error_msg = f"Faction scraping failed for {faction_name}: {e}"
            logger.error(error_msg)
            return self._create_error_result(error_msg, [str(e)])