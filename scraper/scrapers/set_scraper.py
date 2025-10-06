"""
Set scraper for extracting set/expansion data.
"""

import logging
from typing import List
from typing import Set as TypeSet

from bs4 import BeautifulSoup

from ..models import ScrapingResult, Set
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SetScraper(BaseScraper):
    """Scraper for set/expansion data."""

    # Known sets - could be made dynamic in the future
    KNOWN_SETS = [
        "Core_Set",
        "The_Big_Geeky_Box",
        "The_Obligatory_Cthulhu_Set",
        "Pretty_Pretty_Smash_Up",
        "Awesome_Level_9000",
        "Science_Fiction_Double_Feature",
        "Monster_Smash",
    ]

    def get_available_sets(self) -> List[str]:
        """
        Get list of available sets.

        Returns:
            List of set names
        """
        # TODO: Make this dynamic by scraping from a sets listing page
        logger.info(f"Retrieved {len(self.KNOWN_SETS)} known sets")
        return self.KNOWN_SETS.copy()

    def scrape_set_factions(self, set_name: str) -> TypeSet[str]:
        """
        Scrape faction names from a set page.

        Args:
            set_name: Name of the set to scrape

        Returns:
            Set of faction names
        """
        self._log_scraping_start("faction scraping", set_name)

        soup = self.get_soup(set_name)
        if not soup:
            logger.warning(f"Could not fetch page for set: {set_name}")
            return set()

        factions = set()
        gallery = soup.find(id="gallery-0")

        if not gallery:
            logger.warning(f"No gallery found for set: {set_name}")
            return factions

        # Extract faction names from image alt text
        images = gallery.find_all("img")
        for img in images:
            alt_text = img.get("alt")
            if alt_text and alt_text.strip():
                factions.add(alt_text.strip())

        self._log_scraping_complete("faction scraping", len(factions), set_name)
        return factions

    def scrape_set_data(self, set_name: str) -> Set:
        """
        Scrape complete data for a set including basic info.

        Args:
            set_name: Name of the set to scrape

        Returns:
            Set model with scraped data
        """
        set_id = self.generate_id(set_name)
        set_url = f"{self.web_client.BASE_URL}{set_name}"

        return Set(
            set_id=set_id,
            set_name=set_name,
            set_url=set_url,
            factions=None,  # Factions are scraped separately
        )

    def scrape(self, set_name: str = None) -> ScrapingResult:
        """
        Scrape set data.

        Args:
            set_name: Specific set to scrape, or None for all sets

        Returns:
            ScrapingResult with operation details
        """
        try:
            if set_name:
                # Scrape specific set
                sets_to_process = [set_name]
            else:
                # Scrape all known sets
                sets_to_process = self.get_available_sets()

            scraped_sets = []
            errors = []

            for set_name in sets_to_process:
                try:
                    set_data = self.scrape_set_data(set_name)
                    scraped_sets.append(set_data)
                    logger.debug(f"Successfully scraped set: {set_name}")
                except Exception as e:
                    error_msg = f"Failed to scrape set {set_name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            if scraped_sets:
                return self._create_success_result(
                    f"Successfully scraped {len(scraped_sets)} sets", len(scraped_sets)
                )
            else:
                return self._create_error_result(
                    "No sets were successfully scraped", errors
                )

        except Exception as e:
            error_msg = f"Set scraping failed: {e}"
            logger.error(error_msg)
            return self._create_error_result(error_msg, [str(e)])
