"""
Card scraper for extracting individual card data from faction pages.
"""

import logging
from typing import Optional, Union

from ..models import ActionCard, MinionCard, ScrapingResult
from ..utils.text_parsing import (
    extract_card_description,
    extract_power_from_text,
    is_minion_card_text,
)
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CardScraper(BaseScraper):
    """Scraper for individual card data."""

    def scrape_faction_cards(
        self, faction_name: str, faction_id: str
    ) -> ScrapingResult:
        """
        Scrape all cards for a specific faction.

        Args:
            faction_name: Name of the faction
            faction_id: ID of the faction

        Returns:
            ScrapingResult with scraped cards
        """
        try:
            self._log_scraping_start("card scraping", faction_name)

            # Get faction page using special handling
            response = self.web_client.get_faction_page(faction_name)
            if not response:
                return self._create_error_result(
                    f"Could not fetch faction page for {faction_name}"
                )

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            # Find all paragraphs that might contain card data
            paragraphs = soup.find_all("p")

            cards = []
            errors = []

            for paragraph in paragraphs:
                span = paragraph.find("span")
                if not span or not span.get("id"):
                    continue

                try:
                    card_name = span["id"]
                    card_text = paragraph.text

                    # Parse the card based on its text
                    card = self._parse_card_from_text(
                        card_text, card_name, faction_name, faction_id
                    )

                    if card:
                        cards.append(card)
                        logger.debug(f"Successfully parsed card: {card_name}")
                    else:
                        logger.warning(f"Could not parse card: {card_name}")

                except Exception as e:
                    error_msg = f"Error parsing card {span.get('id', 'unknown')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            self._log_scraping_complete("card scraping", len(cards), faction_name)

            if cards:
                message = f"Successfully scraped {len(cards)} cards from {faction_name}"
                return ScrapingResult(
                    success=True,
                    message=message,
                    items_processed=len(cards),
                    errors=errors,
                )
            else:
                return self._create_error_result(
                    f"No cards found for faction {faction_name}", errors
                )

        except Exception as e:
            error_msg = f"Card scraping failed for faction {faction_name}: {e}"
            logger.error(error_msg)
            return self._create_error_result(error_msg, [str(e)])

    def _parse_card_from_text(
        self, text: str, card_name: str, faction_name: str, faction_id: str
    ) -> Optional[Union[MinionCard, ActionCard]]:
        """
        Parse a card from scraped text.

        Args:
            text: Raw card text from the wiki
            card_name: Name of the card
            faction_name: Name of the faction
            faction_id: ID of the faction

        Returns:
            Parsed card model or None if parsing fails
        """
        try:
            # Determine if this is a minion or action card
            if is_minion_card_text(text):
                return self._parse_minion_card(
                    text, card_name, faction_name, faction_id
                )
            else:
                return self._parse_action_card(
                    text, card_name, faction_name, faction_id
                )

        except Exception as e:
            logger.error(f"Error parsing card {card_name}: {e}")
            return None

    def _parse_minion_card(
        self, text: str, card_name: str, faction_name: str, faction_id: str
    ) -> Optional[MinionCard]:
        """Parse a minion card from text."""
        power = extract_power_from_text(text)
        if power is None:
            logger.warning(f"Could not extract power for minion {card_name}")
            return None

        description = extract_card_description(text, "minion")
        if not description:
            logger.warning(f"Could not extract description for minion {card_name}")
            return None

        return MinionCard(
            card_id=self.generate_id(card_name),
            name=card_name,
            description=description,
            faction_name=faction_name,
            faction_id=faction_id,
            power=power,
        )

    def _parse_action_card(
        self, text: str, card_name: str, faction_name: str, faction_id: str
    ) -> Optional[ActionCard]:
        """Parse an action card from text."""
        description = extract_card_description(text, "action")
        if not description:
            logger.warning(f"Could not extract description for action {card_name}")
            return None

        return ActionCard(
            card_id=self.generate_id(card_name),
            name=card_name,
            description=description,
            faction_name=faction_name,
            faction_id=faction_id,
        )

    def scrape(self, faction_name: str, faction_id: str = None) -> ScrapingResult:
        """
        Scrape cards for a faction.

        Args:
            faction_name: Name of the faction
            faction_id: ID of the faction (generated if not provided)

        Returns:
            ScrapingResult with operation details
        """
        if not faction_id:
            faction_id = self.generate_id(faction_name)

        return self.scrape_faction_cards(faction_name, faction_id)
