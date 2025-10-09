"""
SQLAlchemy database models for the Smash Up scraper.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Set(Base):
    """Database model for sets/expansions."""

    __tablename__ = "_sets"

    set_id = Column(String(32), primary_key=True)
    set_name = Column(String(100), nullable=False)
    set_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    factions = relationship(
        "Faction", back_populates="set", cascade="all, delete-orphan"
    )


class Faction(Base):
    """Database model for factions."""

    __tablename__ = "_factions"

    faction_id = Column(String(32), primary_key=True)
    faction_name = Column(String(100), nullable=False)
    faction_url = Column(String(255), nullable=False)
    set_id = Column(String(32), ForeignKey("_sets.set_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    set = relationship("Set", back_populates="factions")
    cards = relationship("Card", back_populates="faction", cascade="all, delete-orphan")


class Card(Base):
    """Database model for linking cards to factions."""

    __tablename__ = "_cards"

    card_id = Column(String(32), primary_key=True)
    faction_id = Column(String(32), ForeignKey("_factions.faction_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    faction = relationship("Faction", back_populates="cards")


class Minion(Base):
    """Database model for minion cards."""

    __tablename__ = "_minions"

    minion_id = Column(String(32), primary_key=True)
    minion_name = Column(String(100), nullable=False)
    minion_desc = Column(Text, nullable=False)
    minion_power = Column(Integer, nullable=False)
    number_of = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Action(Base):
    """Database model for action cards."""

    __tablename__ = "_actions"

    action_id = Column(String(32), primary_key=True)
    action_name = Column(String(100), nullable=False)
    action_desc = Column(Text, nullable=False)
    number_of = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class BaseCard(Base):
    """Database model for base cards."""

    __tablename__ = "bases"

    base_id = Column(String(32), primary_key=True)
    base_name = Column(String(100), nullable=False)
    base_power = Column(Integer, nullable=False)
    base_desc = Column(Text, nullable=False)
    first_place = Column(Integer, nullable=False)
    second_place = Column(Integer, nullable=False)
    third_place = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseEngine:
    """Database engine and session management."""

    def __init__(self, database_url: str = "sqlite:///smashup.db"):
        """
        Initialize database engine.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()

    def drop_tables(self):
        """Drop all tables (for testing/reset)."""
        Base.metadata.drop_all(bind=self.engine)
