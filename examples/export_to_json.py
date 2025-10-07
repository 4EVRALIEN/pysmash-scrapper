"""
Export example for the PySmash scraper.

This example demonstrates how to:
1. Scrape data from multiple sources
2. Export data to JSON format
3. Handle different data types
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper.database.repository import SmashUpRepository
from scraper.scrapers.set_scraper import SetScraper
from scraper.utils.web_client import SmashUpWebClient


def export_to_json(repository: SmashUpRepository, filename: str = None):
    """
    Export all data from database to JSON format.

    Args:
        repository: Database repository instance
        filename: Output filename (optional)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smashup_export_{timestamp}.json"

    print(f"Exporting data to {filename}...")

    # Get all data
    sets = repository.get_all_sets()

    export_data = {
        "export_info": {
            "timestamp": datetime.utcnow().isoformat(),
            "total_sets": len(sets),
            "version": "1.0.0",
        },
        "sets": [],
    }

    for set_data in sets:
        set_info = {
            "set_id": set_data["set_id"],
            "set_name": set_data["set_name"],
            "set_url": set_data["set_url"],
            "created_at": set_data["created_at"],
            "factions": repository.get_factions_by_set(set_data["set_id"]),
        }
        export_data["sets"].append(set_info)

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Exported {len(sets)} sets to {filename}")
    return filename


def main():
    """Demonstrate data export functionality."""
    # Initialize database
    print("Initializing database...")
    repository = SmashUpRepository("sqlite:///export_example.db")

    # Check if we have data, if not scrape some
    sets = repository.get_all_sets()

    if not sets:
        print("No data found, scraping some example data...")

        with SmashUpWebClient() as web_client:
            set_scraper = SetScraper(web_client)

            # Scrape a test set
            result = set_scraper.scrape("Core_Set")

            if result.success:
                print(f"✅ {result.message}")
            else:
                print(f"❌ Scraping failed: {result.message}")
                return

        # Refresh sets data
        sets = repository.get_all_sets()

    if sets:
        # Export to JSON
        filename = export_to_json(repository)

        # Show some statistics
        print(f"\n📊 Export Statistics:")
        print(f"  - Total sets: {len(sets)}")

        total_factions = sum(
            len(repository.get_factions_by_set(s["set_id"])) for s in sets
        )
        print(f"  - Total factions: {total_factions}")
        print(f"  - Output file: {filename}")

        # Show sample of the data
        print(f"\n📋 Sample Data:")
        for set_data in sets[:2]:  # Show first 2 sets
            print(f"  Set: {set_data['set_name']}")
            factions = repository.get_factions_by_set(set_data["set_id"])
            for faction in factions[:3]:  # Show first 3 factions
                print(f"    - {faction['faction_name']}")
            if len(factions) > 3:
                print(f"    ... and {len(factions) - 3} more")
    else:
        print("❌ No data available to export")


if __name__ == "__main__":
    main()
