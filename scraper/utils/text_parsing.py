"""
Text parsing utilities for cleaning and processing scraped content.
"""
import re
from typing import Optional


def clean_card_text(text: str) -> str:
    """
    Clean scraped card text by removing unwanted characters and formatting.
    
    Args:
        text: Raw text scraped from the wiki
        
    Returns:
        Cleaned text suitable for database storage
    """
    return (text.replace("\n", "")
            .replace("\t", "")
            .replace("\r", "")
            .replace(" FAQ", "")
            .strip())


def extract_power_from_text(text: str) -> Optional[int]:
    """
    Extract power value from minion card text.
    
    Args:
        text: Card text containing power information
        
    Returns:
        Power value as integer, or None if not found/invalid
    """
    power_match = re.search(r"power\s+(\d+)", text.lower())
    if power_match:
        try:
            return int(power_match.group(1))
        except ValueError:
            return None
    return None


def extract_card_description(text: str, card_type: str = "action") -> Optional[str]:
    """
    Extract card description from scraped text.
    
    Args:
        text: Raw card text
        card_type: Type of card ("action" or "minion")
        
    Returns:
        Cleaned card description or None if extraction fails
    """
    parts = text.split(" - ")
    
    if card_type == "minion" and len(parts) >= 3:
        # For minions: Name - Power info - Description
        return clean_card_text(parts[2])
    elif card_type == "action" and len(parts) >= 2:
        # For actions: Name - Description
        return clean_card_text(parts[1])
    
    return None


def is_minion_card_text(text: str) -> bool:
    """
    Determine if text represents a minion card based on format.
    
    Args:
        text: Raw card text
        
    Returns:
        True if text appears to be from a minion card
    """
    return bool(re.search(r"power\s+\d", text.lower())) and len(text.split(" - ")) == 3


def normalize_faction_name(name: str) -> str:
    """
    Normalize faction name for consistent processing.
    
    Args:
        name: Raw faction name
        
    Returns:
        Normalized faction name
    """
    return name.strip().replace("_", " ")


def extract_base_components(text: str) -> Optional[dict]:
    """
    Extract base card components from text.
    
    Args:
        text: Raw base card text
        
    Returns:
        Dictionary with base components or None if parsing fails
    """
    try:
        parts = text.split(" - ")
        if len(parts) < 4:
            return None
            
        name = parts[0].strip()
        breakpoint = parts[1].replace("breakpoint ", "").strip()
        vps_text = parts[2].replace("VPs: ", "").strip()
        description = parts[3].replace("FAQ", "").strip()
        
        # Parse VP values
        vps = vps_text.split()
        if len(vps) < 3:
            return None
            
        return {
            "name": name,
            "breakpoint": int(breakpoint),
            "first_place": int(vps[0]),
            "second_place": int(vps[1]),
            "third_place": int(vps[2]),
            "description": description
        }
    except (ValueError, IndexError):
        return None
