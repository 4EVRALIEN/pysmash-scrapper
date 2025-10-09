"""
Repository pattern implementation for database operations.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from ..models import (
    ActionCard,
)
from ..models import Base as BaseModel
from ..models import Faction as FactionModel
from ..models import (
    MinionCard,
)
from ..models import Set as SetModel
from .models import Action, BaseCard, Card, DatabaseEngine, Faction, Minion, Set

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
                    set_url=set_model.set_url,
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
                    set_id=faction_model.set_id,
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

                # Check if minion already exists
                existing_minion = session.query(Minion).filter(Minion.minion_id == minion_id).first()
                if not existing_minion:
                    # Insert minion data
                    db_minion = Minion(
                        minion_id=minion_id,
                        minion_name=minion.name,
                        minion_desc=minion.description,
                        minion_power=minion.power,
                        number_of=minion.number_of,
                    )
                    session.add(db_minion)

                # Check if card-faction link already exists
                existing_card = session.query(Card).filter(Card.card_id == minion_id).first()
                if not existing_card:
                    # Link to faction
                    db_card = Card(card_id=minion_id, faction_id=minion.faction_id)
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

                # Check if action already exists
                existing_action = session.query(Action).filter(Action.action_id == action_id).first()
                if not existing_action:
                    # Insert action data
                    db_action = Action(
                        action_id=action_id,
                        action_name=action.name,
                        action_desc=action.description,
                        number_of=action.number_of,
                    )
                    session.add(db_action)

                # Check if card-faction link already exists
                existing_card = session.query(Card).filter(Card.card_id == action_id).first()
                if not existing_card:
                    # Link to faction
                    db_card = Card(card_id=action_id, faction_id=action.faction_id)
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

                base_id = BaseScraper.generate_id(base.name)

                db_base = BaseCard(
                    base_id=base_id,
                    base_name=base.name,
                    base_power=base.base_power,
                    base_desc=base.description,
                    first_place=base.first_place,
                    second_place=base.second_place,
                    third_place=base.third_place,
                )
                session.add(db_base)

                logger.debug(f"Inserted base: {base.name}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert base {base.name}: {e}")
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
                        "created_at": s.created_at.isoformat(),
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
                        "created_at": f.created_at.isoformat(),
                    }
                    for f in factions
                ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve factions for set {set_id}: {e}")
            return []

    def get_all_minions(self) -> List[Dict[str, Any]]:
        """
        Get all minion cards from the database.

        Returns:
            List of minion card dictionaries
        """
        try:
            with self.get_session() as session:
                minions = session.query(Minion).all()
                return [
                    {
                        "minion_id": m.minion_id,
                        "minion_name": m.minion_name,
                        "minion_desc": m.minion_desc,
                        "minion_power": m.minion_power,
                        "number_of": m.number_of,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in minions
                ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve minions: {e}")
            return []

    def get_all_actions(self) -> List[Dict[str, Any]]:
        """
        Get all action cards from the database.

        Returns:
            List of action card dictionaries
        """
        try:
            with self.get_session() as session:
                actions = session.query(Action).all()
                return [
                    {
                        "action_id": a.action_id,
                        "action_name": a.action_name,
                        "action_desc": a.action_desc,
                        "number_of": a.number_of,
                        "created_at": a.created_at.isoformat(),
                    }
                    for a in actions
                ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve actions: {e}")
            return []

    def get_all_bases(self) -> List[Dict[str, Any]]:
        """
        Get all base cards from the database.

        Returns:
            List of base card dictionaries
        """
        try:
            with self.get_session() as session:
                bases = session.query(BaseCard).all()
                return [
                    {
                        "base_id": b.base_id,
                        "base_name": b.base_name,
                        "base_power": b.base_power,
                        "base_desc": b.base_desc,
                        "first_place": b.first_place,
                        "second_place": b.second_place,
                        "third_place": b.third_place,
                        "created_at": b.created_at.isoformat(),
                    }
                    for b in bases
                ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve bases: {e}")
            return []

    def get_cards_by_faction(self, faction_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all cards (minions and actions) for a specific faction.

        Args:
            faction_id: ID of the faction

        Returns:
            Dictionary with 'minions' and 'actions' lists
        """
        try:
            with self.get_session() as session:
                # Get card IDs linked to this faction
                cards = session.query(Card).filter(Card.faction_id == faction_id).all()
                card_ids = [c.card_id for c in cards]

                # Get minions and actions with these IDs
                minions = session.query(Minion).filter(Minion.minion_id.in_(card_ids)).all()
                actions = session.query(Action).filter(Action.action_id.in_(card_ids)).all()

                return {
                    "minions": [
                        {
                            "minion_id": m.minion_id,
                            "minion_name": m.minion_name,
                            "minion_desc": m.minion_desc,
                            "minion_power": m.minion_power,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in minions
                    ],
                    "actions": [
                        {
                            "action_id": a.action_id,
                            "action_name": a.action_name,
                            "action_desc": a.action_desc,
                            "created_at": a.created_at.isoformat(),
                        }
                        for a in actions
                    ]
                }
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve cards for faction {faction_id}: {e}")
            return {"minions": [], "actions": []}

    def get_minion_by_id(self, minion_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific minion card by ID.

        Args:
            minion_id: ID of the minion card

        Returns:
            Minion dictionary or None if not found
        """
        try:
            with self.get_session() as session:
                minion = session.query(Minion).filter(Minion.minion_id == minion_id).first()
                if minion:
                    return {
                        "minion_id": minion.minion_id,
                        "minion_name": minion.minion_name,
                        "minion_desc": minion.minion_desc,
                        "minion_power": minion.minion_power,
                        "number_of": minion.number_of,
                        "created_at": minion.created_at.isoformat(),
                    }
                return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve minion {minion_id}: {e}")
            return None

    def get_action_by_id(self, action_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific action card by ID.

        Args:
            action_id: ID of the action card

        Returns:
            Action dictionary or None if not found
        """
        try:
            with self.get_session() as session:
                action = session.query(Action).filter(Action.action_id == action_id).first()
                if action:
                    return {
                        "action_id": action.action_id,
                        "action_name": action.action_name,
                        "action_desc": action.action_desc,
                        "number_of": action.number_of,
                        "created_at": action.created_at.isoformat(),
                    }
                return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve action {action_id}: {e}")
            return None

    def get_base_by_id(self, base_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific base card by ID.

        Args:
            base_id: ID of the base card

        Returns:
            Base dictionary or None if not found
        """
        try:
            with self.get_session() as session:
                base = session.query(BaseCard).filter(BaseCard.base_id == base_id).first()
                if base:
                    return {
                        "base_id": base.base_id,
                        "base_name": base.base_name,
                        "base_power": base.base_power,
                        "base_desc": base.base_desc,
                        "first_place": base.first_place,
                        "second_place": base.second_place,
                        "third_place": base.third_place,
                        "created_at": base.created_at.isoformat(),
                    }
                return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve base {base_id}: {e}")
            return None

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
