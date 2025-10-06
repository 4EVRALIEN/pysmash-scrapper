"""
Base scraper class with common functionality for all scrapers.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from bs4 import BeautifulSoup

from ..models import ScrapingResult
from ..utils.web_client import SmashUpWebClient

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    Provides common functionality and interface.
    """

    def __init__(self, web_client: Optional[SmashUpWebClient] = None):
        """
        Initialize the scraper.

        Args:
            web_client: Web client instance. If None, creates a new one.
        """
        self.web_client = web_client or SmashUpWebClient()
        self._owns_client = web_client is None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._owns_client:
            self.web_client.close()

    @staticmethod
    def generate_id(text: str) -> str:
        """
        Generate a consistent ID from text using MD5 hash.

        Args:
            text: Text to hash

        Returns:
            MD5 hash as hexadecimal string
        """
        return hashlib.md5(text.encode()).hexdigest()

    def get_soup(self, endpoint: str) -> Optional[BeautifulSoup]:
        """
        Get BeautifulSoup object for a given endpoint.

        Args:
            endpoint: Wiki endpoint to fetch

        Returns:
            BeautifulSoup object or None if fetch fails
        """
        response = self.web_client.get_page(endpoint)
        if response:
            return BeautifulSoup(response.content, "html.parser")
        return None

    @abstractmethod
    def scrape(self, *args, **kwargs) -> ScrapingResult:
        """
        Abstract method that all scrapers must implement.

        Returns:
            ScrapingResult with operation details
        """
        pass

    def _create_success_result(
        self, message: str, items_processed: int = 0
    ) -> ScrapingResult:
        """
        Create a successful scraping result.

        Args:
            message: Success message
            items_processed: Number of items processed

        Returns:
            ScrapingResult indicating success
        """
        return ScrapingResult(
            success=True, message=message, items_processed=items_processed, errors=[]
        )

    def _create_error_result(
        self, message: str, errors: List[str] = None
    ) -> ScrapingResult:
        """
        Create a failed scraping result.

        Args:
            message: Error message
            errors: List of specific errors

        Returns:
            ScrapingResult indicating failure
        """
        return ScrapingResult(
            success=False, message=message, items_processed=0, errors=errors or []
        )

    def _log_scraping_start(self, operation: str, target: str = None):
        """
        Log the start of a scraping operation.

        Args:
            operation: Description of the operation
            target: Optional target being scraped
        """
        target_str = f" for {target}" if target else ""
        logger.info(f"Starting {operation}{target_str}")

    def _log_scraping_complete(self, operation: str, count: int, target: str = None):
        """
        Log the completion of a scraping operation.

        Args:
            operation: Description of the operation
            count: Number of items processed
            target: Optional target that was scraped
        """
        target_str = f" for {target}" if target else ""
        logger.info(f"Completed {operation}{target_str}: {count} items processed")
