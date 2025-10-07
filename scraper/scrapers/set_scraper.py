"""
Set scraper for extracting set data and faction listings.
"""

import logging
from typing import List

import bs4

from ..models import Set
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SetScraper(BaseScraper):
    """Scraper for set data and faction listings."""

    def get_available_sets(self) -> List[str]:
        """
        Get list of all available sets from the wiki.

        Returns:
            List of set names
        """
        self._log_scraping_start("available sets discovery", "wiki")

        try:
            response = self.web_client.get_page("Category:Sets")
            soup = bs4.BeautifulSoup(response.content, "html.parser")

            # Find set links in category page - they are in unordered lists
            sets = []
            ul_tags = soup.find_all("ul")
            
            for ul in ul_tags:
                links = ul.find_all("a")
                for link in links:
                    href = link.get("href", "")
                    if (href.startswith("/wiki/") and 
                        not href.startswith("/wiki/Category:") and
                        not href.startswith("/wiki/Special:") and
                        not href.startswith("/wiki/File:")):
                        set_name = href.split("/wiki/")[-1]
                        # Additional filter to avoid non-set pages
                        if (set_name and 
                            not set_name.startswith("User:") and
                            not set_name.endswith("_Wiki") and
                            set_name != "Main_Page"):
                            sets.append(set_name)

            # Remove duplicates while preserving order
            unique_sets = []
            seen = set()
            for set_name in sets:
                if set_name not in seen:
                    unique_sets.append(set_name)
                    seen.add(set_name)

            self._log_scraping_complete("available sets discovery", len(unique_sets), "wiki")
            return unique_sets

        except Exception as e:
            logger.error(f"Failed to get available sets: {e}")
            return []

    def scrape_set_data(self, set_name: str) -> Set:
        """
        Scrape complete data for a set including basic info.

        Args:
            set_name: Name of the set to scrape

        Returns:
            SetData model with scraped data
        """
        set_id = self.generate_id(set_name)
        set_url = f"{self.web_client.BASE_URL}{set_name}"

        return Set(
            set_id=set_id,
            set_name=set_name,
            set_url=set_url,
            factions=[],  # Changed from None to empty list
        )

    def scrape_set_factions(self, set_name: str) -> List[str]:
        """
        Scrape faction names from a set page.

        Args:
            set_name: Name of the set to scrape factions from

        Returns:
            List of faction names in the set
        """
        self._log_scraping_start("set factions", set_name)

        try:
            response = self.web_client.get_page(set_name)
            soup = bs4.BeautifulSoup(response.content, "html.parser")

            # Look for faction gallery
            gallery = soup.find("div", class_="wikia-gallery")
            if not gallery:
                logger.warning(f"No faction gallery found for set {set_name}")
                return []

            factions = []
            faction_links = gallery.find_all("a", href=True)

            for link in faction_links:
                href = link.get("href", "")
                if "/wiki/" in href and not any(
                    exclude in href.lower()
                    for exclude in ["file:", "category:", "template:"]
                ):
                    faction_name = href.split("/wiki/")[-1]
                    factions.append(faction_name)

            self._log_scraping_complete("set factions", len(factions), set_name)
            return factions

        except Exception as e:
            error_msg = f"Failed to scrape factions for set {set_name}: {e}"
            logger.error(error_msg)
            return []

    def scrape(self, set_name: str):
        """
        Scrape complete set data.

        Args:
            set_name: Name of the set to scrape

        Returns:
            ScrapingResult with operation details
        """
        try:
            self._log_scraping_start("set scraping", set_name)

            # Scrape basic set data
            set_data = self.scrape_set_data(set_name)

            # Scrape faction list
            factions = self.scrape_set_factions(set_name)

            self._log_scraping_complete("set scraping", 1 + len(factions), set_name)

            return self._create_success_result(
                f"Successfully scraped set {set_name} with "
                f"{len(factions)} factions",
                1 + len(factions),
            )

        except Exception as e:
            error_msg = f"Set scraping failed for {set_name}: {e}"
            logger.error(error_msg)
            return self._create_error_result(error_msg, [str(e)])
