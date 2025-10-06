"""
Web client utilities for making HTTP requests with proper error handling.
"""

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SmashUpWebClient:
    """
    HTTP client configured specifically for scraping Smash Up wiki data.
    """

    BASE_URL = "https://smashup.fandom.com/wiki/"

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the web client with retry strategy.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set user agent
        self.session.headers.update(
            {"User-Agent": "PySmash-Scraper/1.0.0 (Educational/Research Tool)"}
        )

    def get_page(self, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """
        Get a page from the Smash Up wiki.

        Args:
            endpoint: Wiki page endpoint (will be joined with BASE_URL)
            **kwargs: Additional requests parameters

        Returns:
            Response object or None if request fails
        """
        url = urljoin(self.BASE_URL, endpoint)

        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()

            # Be respectful - add small delay between requests
            time.sleep(0.5)

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_faction_page(self, faction_name: str) -> Optional[requests.Response]:
        """
        Get a specific faction page, handling special cases.

        Args:
            faction_name: Name of the faction

        Returns:
            Response object or None if request fails
        """
        # Handle special case for Cthulhu faction
        endpoint = (
            faction_name
            if "cthulhu" not in faction_name.lower()
            else "Minions_of_Cthulhu"
        )

        return self.get_page(endpoint)

    def get_set_page(self, set_name: str) -> Optional[requests.Response]:
        """
        Get a specific set page.

        Args:
            set_name: Name of the set

        Returns:
            Response object or None if request fails
        """
        return self.get_page(set_name)

    def get_bases_page(self) -> Optional[requests.Response]:
        """
        Get the bases listing page.

        Returns:
            Response object or None if request fails
        """
        return self.get_page("Bases")

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_web_client(**kwargs) -> SmashUpWebClient:
    """
    Factory function to create a configured web client.

    Args:
        **kwargs: Configuration options for the client

    Returns:
        Configured SmashUpWebClient instance
    """
    return SmashUpWebClient(**kwargs)
