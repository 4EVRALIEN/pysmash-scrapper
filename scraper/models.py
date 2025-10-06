"""
Pydantic models for data validation and serialization.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class CardBase(BaseModel):
    """Base model for all card types."""
    name: str = Field(..., description="The card name")
    description: str = Field(..., description="Card description/effect text")
    faction_name: str = Field(..., description="Name of the faction this card belongs to")
    faction_id: str = Field(..., description="Unique identifier for the faction")


class MinionCard(CardBase):
    """Model for minion cards with power."""
    power: int = Field(..., ge=0, le=20, description="Minion power value")
    
    @validator('power')
    def validate_power(cls, v):
        if not isinstance(v, int) or v < 0:
            raise ValueError('Power must be a non-negative integer')
        return v


class ActionCard(CardBase):
    """Model for action cards."""
    pass


class Faction(BaseModel):
    """Model for faction data."""
    faction_id: str = Field(..., description="Unique identifier")
    faction_name: str = Field(..., description="Display name")
    faction_url: str = Field(..., description="Wiki URL")
    set_id: str = Field(..., description="ID of the set this faction belongs to")


class Set(BaseModel):
    """Model for set/expansion data."""
    set_id: str = Field(..., description="Unique identifier")
    set_name: str = Field(..., description="Display name")
    set_url: str = Field(..., description="Wiki URL")
    factions: Optional[List[Faction]] = Field(default=None, description="Factions in this set")


class Base(BaseModel):
    """Model for base cards."""
    base_name: str = Field(..., description="Name of the base")
    base_power: int = Field(..., ge=1, description="Breakpoint power")
    base_desc: str = Field(..., description="Base effect description")
    first_place: int = Field(..., ge=0, description="VP for first place")
    second_place: int = Field(..., ge=0, description="VP for second place")
    third_place: int = Field(..., ge=0, description="VP for third place")
    
    @validator('base_power', 'first_place', 'second_place', 'third_place')
    def validate_positive_int(cls, v):
        if not isinstance(v, int) or v < 0:
            raise ValueError('Value must be a non-negative integer')
        return v


class ScrapingResult(BaseModel):
    """Model for scraping operation results."""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Result message")
    items_processed: int = Field(default=0, description="Number of items processed")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


class HealthCheck(BaseModel):
    """Model for API health check response."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
