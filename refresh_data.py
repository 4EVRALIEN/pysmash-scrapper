import hashlib
import logging
from re import search
from typing import List, Set, Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from pysmash.cards import ActionCard, MinionCard
from pysmash.database import DevelopmentDatabase, SQLite
from pysmash.factions import Faction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL: str = "https://smashup.fandom.com/wiki/"


@dataclass
class ScrapedCard:
    """Represents a card scraped from the wiki before database insertion."""
    name: str
    description: str
    faction_name: str
    faction_id: str


@dataclass
class ScrapedMinion(ScrapedCard):
    """Represents a minion card with power."""
    power: int


@dataclass
class ScrapedAction(ScrapedCard):
    """Represents an action card."""
    pass


class SafeDataInserter:
    """Handles safe database insertions using parameterized queries."""
    
    def __init__(self, db: DevelopmentDatabase):
        self.db = db
        logger.info("Database connection established")
    
    def insert_set(self, set_id: str, set_name: str, set_url: str) -> bool:
        """Insert a set with parameterized query to prevent SQL injection."""
        try:
            sql = "INSERT INTO _sets (set_id, set_name, set_url) VALUES (?, ?, ?)"
            self.db.execute(sql, (set_id, set_name, set_url))
            self.db.commit()
            logger.info(f"Inserted set: {set_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert set {set_name}: {e}")
            self.db.rollback()
            return False
    
    def insert_faction(self, faction_id: str, faction_name: str, faction_url: str, set_id: str) -> bool:
        """Insert a faction with parameterized query."""
        try:
            sql = "INSERT INTO _factions (faction_id, faction_name, faction_url, set_id) VALUES (?, ?, ?, ?)"
            self.db.execute(sql, (faction_id, faction_name, faction_url, set_id))
            self.db.commit()
            logger.info(f"Inserted faction: {faction_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert faction {faction_name}: {e}")
            self.db.rollback()
            return False
    
    def insert_minion(self, minion: ScrapedMinion) -> bool:
        """Insert a minion card safely."""
        try:
            minion_id = hashlib.md5(minion.name.encode()).hexdigest()
            
            # Insert minion data
            sql_minion = "INSERT INTO _minions VALUES (?, ?, ?, ?)"
            self.db.execute(sql_minion, (minion_id, minion.name, minion.description, minion.power))
            
            # Link to faction
            sql_card = "INSERT INTO _cards (card_id, faction_id) VALUES (?, ?)"
            self.db.execute(sql_card, (minion_id, minion.faction_id))
            
            self.db.commit()
            logger.debug(f"Inserted minion: {minion.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert minion {minion.name}: {e}")
            self.db.rollback()
            return False
    
    def insert_action(self, action: ScrapedAction) -> bool:
        """Insert an action card safely."""
        try:
            action_id = hashlib.md5(action.name.encode()).hexdigest()
            
            # Insert action data
            sql_action = "INSERT INTO _actions VALUES (?, ?, ?)"
            self.db.execute(sql_action, (action_id, action.name, action.description))
            
            # Link to faction
            sql_card = "INSERT INTO _cards (card_id, faction_id) VALUES (?, ?)"
            self.db.execute(sql_card, (action_id, action.faction_id))
            
            self.db.commit()
            logger.debug(f"Inserted action: {action.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert action {action.name}: {e}")
            self.db.rollback()
            return False


def get_sets() -> List[str]:
    """
    Returns a list of box sets.
    TODO: Scrape this dynamically from the wiki instead of hardcoding.
    """
    sets = [
        "Core_Set",
        "The_Big_Geeky_Box", 
        "The_Obligatory_Cthulhu_Set",
        "Pretty_Pretty_Smash_Up",
        "Awesome_Level_9000",
        "Science_Fiction_Double_Feature",
        "Monster_Smash",
    ]
    logger.info(f"Found {len(sets)} box sets")
    return sets


def get_factions(box_set: str) -> Set[str]:
    """
    Returns a set of factions for a given box set.
    """
    try:
        factions: Set[str] = set()
        faction_url = f"{BASE_URL}{box_set}"
        
        logger.info(f"Scraping factions from: {faction_url}")
        faction_page = requests.get(faction_url, timeout=10)
        faction_page.raise_for_status()  # Raise exception for bad status codes
        
        faction_soup = BeautifulSoup(faction_page.content, "html.parser")
        results = faction_soup.find(id="gallery-0")
        
        if not results:
            logger.warning(f"No gallery found for {box_set}")
            return factions
            
        anchors = results.find_all("img")
        for record in anchors:
            alt_text = record.get("alt")
            if alt_text:
                factions.add(alt_text)
        
        logger.info(f"Found {len(factions)} factions in {box_set}")
        return factions
        
    except requests.RequestException as e:
        logger.error(f"Network error scraping {box_set}: {e}")
        return set()
    except Exception as e:
        logger.error(f"Unexpected error scraping {box_set}: {e}")
        return set()


def clean_card_text(text: str) -> str:
    """
    Clean scraped card text by removing unwanted characters and formatting.
    """
    return (text.replace("\n", "")
            .replace("\t", "")
            .replace("\r", "")
            .replace(" FAQ", "")
            .strip())

def pull_wiki_data(db: DevelopmentDatabase):
    """
    Improved version with better error handling and separation of concerns.
    """
    inserter = SafeDataInserter(db)
    
    for box_set in get_sets():
        set_id = hashlib.md5(box_set.encode()).hexdigest()
        set_url = f"{BASE_URL}{box_set}"
        
        # Insert set safely
        if not inserter.insert_set(set_id, box_set, set_url):
            logger.error(f"Failed to insert set {box_set}, skipping...")
            continue

        for faction_name in get_factions(box_set):
            if not faction_name:  # Skip None/empty values
                continue
                
            faction_id = hashlib.md5(faction_name.encode()).hexdigest()
            
            # Handle special case for Cthulhu faction
            faction_url = (f"{BASE_URL}{faction_name}" 
                          if 'cthulhu' not in faction_name.lower() 
                          else f"{BASE_URL}Minions_of_Cthulhu")
            
            # Insert faction safely
            if not inserter.insert_faction(faction_id, faction_name, faction_url, set_id):
                logger.error(f"Failed to insert faction {faction_name}, skipping...")
                continue
            
            # Scrape cards for this faction
            cards = scrape_faction_cards(faction_name, faction_id, faction_url)
            
            # Insert cards using our safe inserter
            for card in cards:
                if isinstance(card, ScrapedMinion):
                    inserter.insert_minion(card)
                elif isinstance(card, ScrapedAction):
                    inserter.insert_action(card)


def scrape_faction_cards(faction_name: str, faction_id: str, faction_url: str) -> List[ScrapedCard]:
    """
    Scrape all cards for a given faction.
    Separated for better testability and readability.
    """
    try:
        logger.info(f"Scraping cards for faction: {faction_name}")
        faction_page = requests.get(faction_url, timeout=10)
        faction_page.raise_for_status()
        
        faction_soup = BeautifulSoup(faction_page.content, "html.parser")
        faction_results = faction_soup.find_all("p")
        
        cards: List[ScrapedCard] = []
        
        for record in faction_results:
            span = record.find("span")
            if not span:
                continue
                
            try:
                card_name = span["id"]
            except KeyError:
                continue
            
            # Parse card based on whether it's a minion or action
            card = parse_card_from_text(record.text, card_name, faction_name, faction_id)
            if card:
                cards.append(card)
        
        logger.info(f"Found {len(cards)} cards for {faction_name}")
        return cards
        
    except requests.RequestException as e:
        logger.error(f"Network error scraping faction {faction_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error scraping faction {faction_name}: {e}")
        return []


def parse_card_from_text(text: str, card_name: str, faction_name: str, faction_id: str) -> Optional[ScrapedCard]:
    """
    Parse a card from scraped text.
    Returns either ScrapedMinion or ScrapedAction based on content.
    """
    try:
        # Check if this is a minion (has power and proper format)
        if search(r"power\s\d", text) and len(text.split(" - ")) == 3:
            # Extract power value
            power_text = text.split("power")[1].split(" - ")[0].strip()
            try:
                power = int(power_text)
            except ValueError:
                logger.warning(f"Could not parse power for {card_name}: {power_text}")
                return None
            
            # Extract description 
            description = clean_card_text(text.split(" - ")[2])
            
            return ScrapedMinion(
                name=card_name,
                description=description,
                faction_name=faction_name,
                faction_id=faction_id,
                power=power
            )
        
        # Otherwise it's an action card
        elif " - " in text:
            description = clean_card_text(text.split(" - ")[1])
            
            return ScrapedAction(
                name=card_name,
                description=description,
                faction_name=faction_name,
                faction_id=faction_id
            )
        
        # If format doesn't match expectations
        logger.warning(f"Unknown card format for {card_name}: {text[:50]}...")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing card {card_name}: {e}")
        return None

def pull_base_data():
    """
    Scrape base data from the wiki with improved error handling.
    """
    try:
        base_url = "https://smashup.fandom.com/wiki/Bases"
        logger.info(f"Scraping base data from: {base_url}")
        
        base_page = requests.get(base_url, timeout=10)
        base_page.raise_for_status()
        
        base_soup = BeautifulSoup(base_page.content, "html.parser")
        lis = base_soup.find_all("li")
        
        db = SQLite()
        successful_inserts = 0
        failed_inserts = 0
        
        for i, li in enumerate(lis):
            # Skip elements outside the expected range
            if i < 124 or i > 325:
                continue
                
            try:
                base_parts = li.text.split(" - ")
                if len(base_parts) < 4:
                    logger.warning(f"Unexpected base format at index {i}: {li.text[:50]}...")
                    continue
                
                name = base_parts[0].strip()
                breakpoint = base_parts[1].replace("breakpoint ", "").strip()
                vps_text = base_parts[2].replace("VPs: ", "").strip()
                description = base_parts[3].replace("FAQ", "").strip()
                
                # Parse VP values
                vps = vps_text.split(" ")
                if len(vps) < 3:
                    logger.warning(f"Could not parse VPs for base {name}: {vps_text}")
                    continue
                
                # Use parameterized query for safety
                sql = """
                INSERT INTO bases (base_name, first_place, second_place, third_place, base_power, base_desc)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                
                db.execute(sql, (name, vps[0], vps[1], vps[2], breakpoint, description))
                db.commit()
                successful_inserts += 1
                logger.debug(f"Inserted base: {name}")
                
            except (IndexError, ValueError) as e:
                logger.warning(f"Error parsing base at index {i}: {e}")
                db.rollback()
                failed_inserts += 1
                continue
            except Exception as e:
                logger.error(f"Unexpected error inserting base at index {i}: {e}")
                db.rollback()
                failed_inserts += 1
                continue
        
        logger.info(f"Base data scraping complete. Success: {successful_inserts}, Failed: {failed_inserts}")
        
    except requests.RequestException as e:
        logger.error(f"Network error scraping bases: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in pull_base_data: {e}")


def main():
    """
    Main entry point for data refresh operations.
    """
    logger.info("Starting data refresh process...")
    
    try:
        # Initialize database connection
        db = SQLite()  # You might want to pass a proper database instance here
        
        # Pull faction and card data
        logger.info("Pulling wiki data...")
        pull_wiki_data(db)
        
        # Pull base data
        logger.info("Pulling base data...")
        pull_base_data()
        
        logger.info("Data refresh completed successfully!")
        
    except Exception as e:
        logger.error(f"Data refresh failed: {e}")
        raise


if __name__ == "__main__":
    main()
