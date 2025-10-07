"""
Basic usage example for the PySmash scraper.

This example demonstrates how to:
1. Initialize the scraper components
2. Scrape basic faction data
3. Store results in the database
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper.database.repository import SmashUpRepository
from scraper.scrapers.faction_scraper import FactionScraper
from scraper.utils.web_client import SmashUpWebClient


def main():
    """Demonstrate basic scraping functionality."""
    # Initialize database
    print("Initializing database...")
    repository = SmashUpRepository("sqlite:///example_data.db")

    # Initialize web client and scraper
    print("Setting up scrapers...")
    with SmashUpWebClient() as web_client:
        faction_scraper = FactionScraper(web_client)

        # Example: Scrape a single faction
        print("Scraping Robots faction...")
        result = faction_scraper.scrape("Robots", "core_set")

        if result.success:
            print(f"✅ {result.message}")
            print(f"Items processed: {result.items_processed}")
        else:
            print(f"❌ Scraping failed: {result.message}")
            for error in result.errors:
                print(f"  - {error}")

    # Query some data
    print("\nQuerying database...")
    sets = repository.get_all_sets()
    print(f"Found {len(sets)} sets in database")

    for set_data in sets:
        print(f"- {set_data['set_name']} (ID: {set_data['set_id']})")

        factions = repository.get_factions_by_set(set_data["set_id"])
        for faction in factions:
            print(f"  └── {faction['faction_name']}")


if __name__ == "__main__":
    main()
