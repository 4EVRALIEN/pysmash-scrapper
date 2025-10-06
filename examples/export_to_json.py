"""
Example of exporting scraped data to JSON format.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from scraper.database.repository import SmashUpRepository
from scraper.scrapers.set_scraper import SetScraper
from scraper.utils.web_client import SmashUpWebClient


def export_database_to_json(output_file: str = "smashup_data.json"):
    """
    Export all database data to a JSON file.

    Args:
        output_file: Path to the output JSON file
    """
    print(f"📤 Exporting database to {output_file}...")

    repository = SmashUpRepository()

    # Collect all data
    export_data = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "sets": [],
        "total_sets": 0,
        "total_factions": 0,
    }

    # Get all sets
    sets = repository.get_all_sets()
    export_data["total_sets"] = len(sets)

    for set_data in sets:
        # Get factions for this set
        factions = repository.get_factions_by_set(set_data["set_id"])
        export_data["total_factions"] += len(factions)

        set_export = {
            "set_id": set_data["set_id"],
            "set_name": set_data["set_name"],
            "set_url": set_data["set_url"],
            "created_at": set_data["created_at"],
            "factions": factions,
            "faction_count": len(factions),
        }

        export_data["sets"].append(set_export)

    # Write to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Export completed:")
    print(f"  📦 {export_data['total_sets']} sets")
    print(f"  🏛️ {export_data['total_factions']} factions")
    print(f"  💾 Saved to {output_file}")


def scrape_and_export_sample_data():
    """Scrape sample data and export it to JSON."""
    print("🎯 Scraping sample data for export...")

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    repository = SmashUpRepository()

    with SmashUpWebClient() as web_client:
        set_scraper = SetScraper(web_client)

        # Scrape first 2 sets as sample
        sets = set_scraper.get_available_sets()[:2]

        for set_name in sets:
            print(f"📦 Processing set: {set_name}")

            try:
                # Scrape and insert set
                set_data = set_scraper.scrape_set_data(set_name)
                repository.insert_set(set_data)

                # Scrape and insert factions (limit to 2 per set for demo)
                factions = set_scraper.scrape_set_factions(set_name)
                limited_factions = list(factions)[:2]

                for faction_name in limited_factions:
                    if faction_name.strip():
                        from scraper.scrapers.faction_scraper import FactionScraper

                        faction_scraper = FactionScraper(web_client)

                        faction_data = faction_scraper.scrape_faction_data(
                            faction_name, set_data.set_id
                        )
                        repository.insert_faction(faction_data)
                        print(f"  🏛️ Added faction: {faction_name}")

            except Exception as e:
                print(f"  ❌ Error processing {set_name}: {e}")

    print("✅ Sample data scraping completed")


def create_formatted_export():
    """Create a nicely formatted export with additional metadata."""
    print("📋 Creating formatted export...")

    repository = SmashUpRepository()
    sets = repository.get_all_sets()

    # Create a more structured export
    formatted_data = {
        "metadata": {
            "export_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "tool": "PySmash Scraper",
            "version": "1.0.0",
            "description": "Smash Up! card game data scraped from the official wiki",
        },
        "summary": {"total_sets": len(sets), "total_factions": 0},
        "data": {},
    }

    for set_data in sets:
        factions = repository.get_factions_by_set(set_data["set_id"])
        formatted_data["summary"]["total_factions"] += len(factions)

        # Group by set for better organization
        formatted_data["data"][set_data["set_name"]] = {
            "set_info": {
                "id": set_data["set_id"],
                "name": set_data["set_name"],
                "url": set_data["set_url"],
                "scraped_at": set_data["created_at"],
            },
            "factions": [
                {
                    "name": f["faction_name"],
                    "id": f["faction_id"],
                    "url": f["faction_url"],
                }
                for f in factions
            ],
        }

    # Save formatted export
    output_file = "smashup_formatted_export.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Formatted export saved to {output_file}")
    return formatted_data


def main():
    """Main function demonstrating JSON export capabilities."""
    print("🚀 JSON Export Example")
    print("=" * 50)

    # Option 1: Export existing data
    print("\n1️⃣ Exporting existing database data...")
    export_database_to_json("existing_data.json")

    # Option 2: Scrape sample data and export
    print("\n2️⃣ Scraping sample data and exporting...")
    scrape_and_export_sample_data()
    export_database_to_json("sample_data.json")

    # Option 3: Create formatted export
    print("\n3️⃣ Creating formatted export...")
    formatted = create_formatted_export()

    # Display summary
    print("\n📊 Export Summary:")
    print(f"  Sets: {formatted['summary']['total_sets']}")
    print(f"  Factions: {formatted['summary']['total_factions']}")

    print("\n🎉 JSON export examples completed!")
    print("\nGenerated files:")
    print("  • existing_data.json - Raw database export")
    print("  • sample_data.json - Sample scraped data")
    print("  • smashup_formatted_export.json - Formatted export")


if __name__ == "__main__":
    main()
