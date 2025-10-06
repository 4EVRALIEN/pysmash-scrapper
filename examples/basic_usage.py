"""
Basic usage example for the PySmash scraper.
"""
import logging
from scraper.scrapers.set_scraper import SetScraper
from scraper.scrapers.faction_scraper import FactionScraper
from scraper.database.repository import SmashUpRepository
from scraper.utils.web_client import SmashUpWebClient


def main():
    """Demonstrate basic usage of the scraper."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize repository
    repository = SmashUpRepository()
    print("✅ Database initialized")
    
    # Create web client
    with SmashUpWebClient() as web_client:
        print("🌐 Web client created")
        
        # Initialize scrapers
        set_scraper = SetScraper(web_client)
        faction_scraper = FactionScraper(web_client)
        
        # Get available sets
        sets = set_scraper.get_available_sets()
        print(f"📦 Found {len(sets)} available sets:")
        for set_name in sets[:3]:  # Show first 3 sets
            print(f"  • {set_name}")
        
        # Scrape a specific set
        target_set = "Core_Set"
        print(f"\n🎯 Scraping set: {target_set}")
        
        set_data = set_scraper.scrape_set_data(target_set)
        success = repository.insert_set(set_data)
        
        if success:
            print(f"✅ Set '{target_set}' inserted successfully")
            
            # Get factions for this set
            factions = set_scraper.scrape_set_factions(target_set)
            print(f"🏛️ Found {len(factions)} factions in {target_set}:")
            
            for faction_name in list(factions)[:2]:  # Process first 2 factions
                print(f"  Processing faction: {faction_name}")
                
                faction_data = faction_scraper.scrape_faction_data(
                    faction_name, set_data.set_id
                )
                
                if repository.insert_faction(faction_data):
                    print(f"    ✅ Faction '{faction_name}' inserted")
                    
                    # Scrape cards for this faction
                    card_result = faction_scraper.scrape_faction_cards(
                        faction_name, faction_data.faction_id
                    )
                    
                    if card_result:
                        print(f"    🃏 Cards processed for {faction_name}")
                else:
                    print(f"    ❌ Failed to insert faction '{faction_name}'")
        else:
            print(f"❌ Failed to insert set '{target_set}'")
    
    # Show final database state
    print("\n📊 Database Summary:")
    sets_in_db = repository.get_all_sets()
    print(f"  Sets in database: {len(sets_in_db)}")
    
    for db_set in sets_in_db:
        factions_in_set = repository.get_factions_by_set(db_set['set_id'])
        print(f"    {db_set['set_name']}: {len(factions_in_set)} factions")
    
    print("\n🎉 Basic usage example completed!")


if __name__ == "__main__":
    main()
