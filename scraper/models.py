"""
Pydantic models for data validation and serialization.
"""

from typing import List, Optional

from pydantic import BaseModel, field_validator


class MinionCard(BaseModel):
    """Model for a minion card."""

    card_id: str
    name: str
    faction_name: str
    faction_id: str
    power: int
    description: str
    card_url: Optional[str] = None

    @field_validator("power")
    @classmethod
    def validate_power(cls, v):
        """Validate power is non-negative."""
        if v < 0:
            raise ValueError("Power must be non-negative")
        return v


class ActionCard(BaseModel):
    """Model for an action card."""

    card_id: str
    name: str
    faction_name: str
    faction_id: str
    description: str
    card_url: Optional[str] = None


class Base(BaseModel):
    """Model for a base."""

    base_id: str
    name: str
    base_power: int
    first_place: int
    second_place: int
    third_place: int
    description: str
    base_url: Optional[str] = None

    @field_validator("base_power", "first_place", "second_place", "third_place")
    @classmethod
    def validate_points(cls, v):
        """Validate points are non-negative."""
        if v < 0:
            raise ValueError("Points must be non-negative")
        return v


class Faction(BaseModel):
    """Model for a faction."""

    faction_id: str
    faction_name: str
    set_id: str
    faction_url: Optional[str] = None
    description: Optional[str] = None
    minion_cards: List[MinionCard] = []
    action_cards: List[ActionCard] = []


class Set(BaseModel):
    """Model for a set."""

    set_id: str
    set_name: str
    set_url: Optional[str] = None
    description: Optional[str] = None
    factions: List[Faction] = []
    bases: List[Base] = []


class ScrapingResult(BaseModel):
    """Model for scraping operation results."""

    success: bool
    message: str
    items_processed: int
    errors: List[str] = []


class HealthCheck(BaseModel):
    """Model for health check response."""

    status: str
    timestamp: str
    version: str
