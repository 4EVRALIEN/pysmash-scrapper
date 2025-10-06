"""
Repository pattern implementation for database operations.
"""
import logging
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .models import DatabaseEngine, Set, Faction, Card, Minion, Action, BaseCard
from ..models import (
    Set as SetModel, 
    Faction as FactionModel, 
    MinionCard, 
    ActionCard, 
    Base as BaseModel
)


logger = logging.getLogger(__name__)


class SmashUpRepository:
    """Repository for Smash Up data operations with proper error handling."""
    
    def __init__(self, database_url: str = "sqlite:///smashup.db"):
        """
        Initialize repository with database connection.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.db_engine = DatabaseEngine(database_url)
        self.db_engine.create_tables()
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions with automatic cleanup."""
        session = self.db_engine.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def insert_set(self, set_model: SetModel) -> bool:
        """
        Insert a set into the database.
        
        Args:
            set_model: Set model to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                db_set = Set(
                    set_id=set_model.set_id,
                    set_name=set_model.set_name,
                    set_url=set_model.set_url
                )
                session.add(db_set)
                logger.debug(f"Inserted set: {set_model.set_name}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert set {set_model.set_name}: {e}")
            return False
    
    def insert_faction(self, faction_model: FactionModel) -> bool:
        """
        Insert a faction into the database.
        
        Args:
            faction_model: Faction model to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                db_faction = Faction(
                    faction_id=faction_model.faction_id,
                    faction_name=faction_model.faction_name,
                    faction_url=faction_model.faction_url,
                    set_id=faction_model.set_id
                )
                session.add(db_faction)
                logger.debug(f"Inserted faction: {faction_model.faction_name}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert faction {faction_model.faction_name}: {e}")
            return False
    
    def insert_minion(self, minion: MinionCard) -> bool:
        """
        Insert a minion card into the database.
        
        Args:
            minion: Minion card model to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # Generate ID from name
                from ..scrapers.base_scraper import BaseScraper
                minion_id = BaseScraper.generate_id(minion.name)
                
                # Insert minion data
                db_minion = Minion(
                    minion_id=minion_id,
                    minion_name=minion.name,
                    minion_desc=minion.description,
                    minion_power=minion.power
                )
                session.add(db_minion)
                
                # Link to faction
                db_card = Card(
                    card_id=minion_id,
                    faction_id=minion.faction_id
                )
                session.add(db_card)
                
                logger.debug(f"Inserted minion: {minion.name}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert minion {minion.name}: {e}")
            return False
    
    def insert_action(self, action: ActionCard) -> bool:
        """
        Insert an action card into the database.
        
        Args:
            action: Action card model to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # Generate ID from name
                from ..scrapers.base_scraper import BaseScraper
                action_id = BaseScraper.generate_id(action.name)
                
                # Insert action data
                db_action = Action(
                    action_id=action_id,
                    action_name=action.name,
                    action_desc=action.description
                )
                session.add(db_action)
                
                # Link to faction
                db_card = Card(
                    card_id=action_id,
                    faction_id=action.faction_id
                )
                session.add(db_card)
                
                logger.debug(f"Inserted action: {action.name}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert action {action.name}: {e}")
            return False
    
    def insert_base(self, base: BaseModel) -> bool:
        """
        Insert a base card into the database.
        
        Args:
            base: Base card model to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # Generate ID from name
                from ..scrapers.base_scraper import BaseScraper
                base_id = BaseScraper.generate_id(base.base_name)
                
                db_base = BaseCard(
                    base_id=base_id,
                    base_name=base.base_name,
                    base_power=base.base_power,
                    base_desc=base.base_desc,
                    first_place=base.first_place,
                    second_place=base.second_place,
                    third_place=base.third_place
                )
                session.add(db_base)
                
                logger.debug(f"Inserted base: {base.base_name}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert base {base.base_name}: {e}")
            return False
    
    def get_all_sets(self) -> List[Dict[str, Any]]:
        """
        Get all sets from the database.
        
        Returns:
            List of set dictionaries
        """
        try:
            with self.get_session() as session:
                sets = session.query(Set).all()
                return [
                    {
                        "set_id": s.set_id,
                        "set_name": s.set_name,
                        "set_url": s.set_url,
                        "created_at": s.created_at.isoformat()
                    }
                    for s in sets
                ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve sets: {e}")
            return []
    
    def get_factions_by_set(self, set_id: str) -> List[Dict[str, Any]]:
        """
        Get all factions for a specific set.
        
        Args:
            set_id: ID of the set
            
        Returns:
            List of faction dictionaries
        """
        try:
            with self.get_session() as session:
                factions = session.query(Faction).filter(Faction.set_id == set_id).all()
                return [
                    {
                        "faction_id": f.faction_id,
                        "faction_name": f.faction_name,
                        "faction_url": f.faction_url,
                        "set_id": f.set_id,
                        "created_at": f.created_at.isoformat()
                    }
                    for f in factions
                ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve factions for set {set_id}: {e}")
            return []
    
    def clear_all_data(self) -> bool:
        """
        Clear all data from the database (for testing/reset).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # Delete in correct order due to foreign key constraints
                session.query(Card).delete()
                session.query(Minion).delete()
                session.query(Action).delete()
                session.query(BaseCard).delete()
                session.query(Faction).delete()
                session.query(Set).delete()
                logger.info("Cleared all data from database")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to clear database: {e}")
            return False
