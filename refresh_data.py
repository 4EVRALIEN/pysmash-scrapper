#!/usr/bin/env python3
"""
Modern refactored version of the original refresh_data.py script.
This version uses the new modular architecture while maintaining the same functionality.
"""
import logging
import sys
from typing import List

from scraper.database.repository import SmashUpRepository
from scraper.models import Base
from scraper.scrapers.faction_scraper import FactionScraper
from scraper.scrapers.set_scraper import SetScraper
from scraper.utils.text_parsing import extract_base_components
from scraper.utils.web_client import SmashUpWebClient

# Configure logging to match original script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModernDataRefresher:
    """
    Modern implementation of the original data refresh functionality.
    Uses the new modular architecture for better maintainability.
    """
    
    def __init__(self, database_url: str = "sqlite:///smashup.db"):
        """
        Initialize the data refresher.
        
        Args:
            database_url: Database connection URL
        """
        self.repository = SmashUpRepository(database_url)
        logger.info("Database connection established")
    
    def refresh_wiki_data(self):
        """
        Refresh faction and card data from the wiki.
        Modern equivalent of the original pull_wiki_data function.
        """
        logger.info("Starting wiki data refresh...")
        
        total_processed = 0
        total_errors = 0
        
        with SmashUpWebClient() as web_client:
            set_scraper = SetScraper(web_client)
            faction_scraper = FactionScraper(web_client)
            
            # Get all available sets
            sets = set_scraper.get_available_sets()
            logger.info(f"Found {len(sets)} sets to process")
            
            for set_name in sets:
                try:
                    logger.info(f"Processing set: {set_name}")
                    
                    # Scrape and insert set data
                    set_data = set_scraper.scrape_set_data(set_name)
                    if not self.repository.insert_set(set_data):
                        logger.error(f"Failed to insert set {set_name}, skipping...")
                        total_errors += 1
                        continue
                    
                    total_processed += 1
                    
                    # Get factions for this set
                    factions = set_scraper.scrape_set_factions(set_name)
                    logger.info(f"Found {len(factions)} factions in {set_name}")
                    
                    for faction_name in factions:
                        if not faction_name.strip():
                            continue
                        
                        try:
                            # Scrape faction data
                            faction_data = faction_scraper.scrape_faction_data(
                                faction_name, set_data.set_id
                            )
                            
                            if not self.repository.insert_faction(faction_data):
                                logger.error(f"Failed to insert faction {faction_name}")
                                total_errors += 1
                                continue
                            
                            total_processed += 1
                            
                            # Scrape cards for this faction
                            card_result = faction_scraper.scrape_faction_cards(
                                faction_name, faction_data.faction_id
                            )
                            
                            if card_result:
                                total_processed += card_result.items_processed
                            else:
                                total_errors += 1
                                
                        except Exception as e:
                            logger.error(f"Error processing faction {faction_name}: {e}")
                            total_errors += 1
                
                except Exception as e:
                    logger.error(f"Error processing set {set_name}: {e}")
                    total_errors += 1
        
        logger.info(f"Wiki data refresh complete. Processed: {total_processed}, Errors: {total_errors}")
        return total_processed, total_errors
    
    def refresh_base_data(self):
        """
        Refresh base card data from the wiki.
        Modern equivalent of the original pull_base_data function.
        """
        logger.info("Starting base data refresh...")
        
        try:
            with SmashUpWebClient() as web_client:
                response = web_client.get_bases_page()
                
                if not response:
                    logger.error("Could not fetch bases page")
                    return 0, 1
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, "html.parser")
                list_items = soup.find_all("li")
                
                successful_inserts = 0
                failed_inserts = 0
                
                # Process list items (matching original logic for indices 124-325)
                for i, li in enumerate(list_items):
                    if i < 124 or i > 325:
                        continue
                    
                    try:
                        base_components = extract_base_components(li.text)
                        if not base_components:
                            logger.warning(f"Could not parse base at index {i}: {li.text[:50]}...")
                            failed_inserts += 1
                            continue
                        
                        # Create base model
                        base = Base(
                            base_name=base_components["name"],
                            base_power=base_components["breakpoint"],
                            base_desc=base_components["description"],
                            first_place=base_components["first_place"],
                            second_place=base_components["second_place"],
                            third_place=base_components["third_place"]
                        )
                        
                        if self.repository.insert_base(base):
                            successful_inserts += 1
                            logger.debug(f"Inserted base: {base.base_name}")
                        else:
                            failed_inserts += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing base at index {i}: {e}")
                        failed_inserts += 1
                
                logger.info(f"Base data refresh complete. Success: {successful_inserts}, Failed: {failed_inserts}")
                return successful_inserts, failed_inserts
                
        except Exception as e:
            logger.error(f"Base data refresh failed: {e}")
            return 0, 1
    
    def full_refresh(self):
        """
        Perform a complete data refresh.
        Modern equivalent of the original main function.
        """
        logger.info("Starting full data refresh...")
        
        try:
            # Refresh wiki data (sets, factions, cards)
            wiki_processed, wiki_errors = self.refresh_wiki_data()
            
            # Refresh base data
            base_processed, base_errors = self.refresh_base_data()
            
            total_processed = wiki_processed + base_processed
            total_errors = wiki_errors + base_errors
            
            logger.info("Data refresh completed!")
            logger.info(f"Total items processed: {total_processed}")
            logger.info(f"Total errors: {total_errors}")
            
            return total_processed > 0 and total_errors == 0
            
        except Exception as e:
            logger.error(f"Full data refresh failed: {e}")
            return False


def main():
    """
    Main entry point - maintains compatibility with original script.
    """
    logger.info("Starting modernized data refresh process...")
    
    try:
        refresher = ModernDataRefresher()
        success = refresher.full_refresh()
        
        if success:
            logger.info("Data refresh completed successfully!")
            sys.exit(0)
        else:
            logger.error("Data refresh completed with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Data refresh cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
