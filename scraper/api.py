"""
FastAPI web service for the PySmash scraper.
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .database.repository import SmashUpRepository
from .models import HealthCheck, ScrapingResult
from .scrapers.faction_scraper import FactionScraper
from .scrapers.set_scraper import SetScraper
from .utils.web_client import SmashUpWebClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PySmash Scraper API",
    description="A REST API for scraping Smash Up! card game data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global repository instance - will be initialized lazily
_repository = None


def get_repository() -> SmashUpRepository:
    """Get or create the repository instance."""
    global _repository
    if _repository is None:
        # Use environment variable or default to in-memory for tests
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/smashup.db")
        
        # Create data directory if using file-based SQLite
        if db_url.startswith("sqlite:///") and not db_url.endswith(":memory:"):
            db_path = db_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        _repository = SmashUpRepository(db_url)
    return _repository


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy", 
        timestamp=datetime.utcnow().isoformat(), 
        version="1.0.0"
    )


@app.get("/sets", response_model=List[Dict[str, Any]])
async def get_sets():
    """Get all sets from the database."""
    try:
        repository = get_repository()
        sets = repository.get_all_sets()
        return [
            {
                "set_id": s.set_id,
                "set_name": s.set_name,
                "set_url": s.set_url,
                "description": s.description,
            }
            for s in sets
        ]
    except Exception as e:
        logger.error(f"Error getting sets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sets")


@app.get("/sets/{set_id}/factions", response_model=List[Dict[str, Any]])
async def get_factions_by_set(set_id: str):
    """Get all factions for a specific set."""
    try:
        repository = get_repository()
        factions = repository.get_factions_by_set(set_id)
        if not factions:
            raise HTTPException(
                status_code=404, detail=f"No factions found for set {set_id}"
            )
        return [
            {
                "faction_id": f.faction_id,
                "faction_name": f.faction_name,
                "faction_url": f.faction_url,
                "set_id": f.set_id,
            }
            for f in factions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting factions for set {set_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve factions"
        )


@app.post("/scrape/faction/{faction_name}", response_model=ScrapingResult)
async def scrape_faction(
    faction_name: str, background_tasks: BackgroundTasks, set_name: str = None
):
    """Trigger scraping for a specific faction."""
    try:
        background_tasks.add_task(
            _background_scrape_faction, faction_name, set_name
        )
        return ScrapingResult(
            success=True,
            message=f"Faction scraping for '{faction_name}' started in background",
            items_processed=0,
            errors=[],
        )
    except Exception as e:
        logger.error(f"Error starting faction scrape for {faction_name}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to start faction scraping"
        )


@app.post("/scrape/set/{set_name}", response_model=ScrapingResult)
async def scrape_set(set_name: str, background_tasks: BackgroundTasks):
    """Trigger scraping for a specific set."""
    try:
        background_tasks.add_task(_background_scrape_set, set_name)
        return ScrapingResult(
            success=True,
            message=f"Set scraping for '{set_name}' started in background",
            items_processed=0,
            errors=[],
        )
    except Exception as e:
        logger.error(f"Error starting set scrape for {set_name}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to start set scraping"
        )


@app.post("/scrape/all", response_model=ScrapingResult)
async def scrape_all(background_tasks: BackgroundTasks):
    """Trigger scraping for all data."""
    try:
        background_tasks.add_task(_background_scrape_all)
        return ScrapingResult(
            success=True,
            message="Full scraping started in background",
            items_processed=0,
            errors=[],
        )
    except Exception as e:
        logger.error(f"Error starting full scrape: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scraping")


@app.delete("/data/clear")
async def clear_database():
    """Clear all data from the database."""
    try:
        repository = get_repository()
        repository.clear_all_data()
        return {"message": "Database cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear database")


# Background task functions
async def _background_scrape_faction(faction_name: str, set_name: str = None):
    """Background task for scraping a faction."""
    try:
        logger.info(f"Starting background scraping for faction: {faction_name}")
        repository = get_repository()

        with SmashUpWebClient() as web_client:
            faction_scraper = FactionScraper(web_client)
            
            set_id = None
            if set_name:
                # Create or get set first
                set_scraper = SetScraper(web_client)
                set_data = set_scraper.scrape_set_data(set_name)
                repository.save_set(set_data)
                set_id = set_data.set_id

            # Scrape faction
            result = faction_scraper.scrape(faction_name, set_id)
            if result.success:
                logger.info(
                    f"Background faction scraping completed for {faction_name}"
                )
            else:
                logger.error(
                    f"Background faction scraping failed for {faction_name}: "
                    f"{result.errors}"
                )

    except Exception as e:
        logger.error(f"Background faction scraping failed for {faction_name}: {e}")


async def _background_scrape_set(set_name: str):
    """Background task for scraping a set."""
    try:
        logger.info(f"Starting background scraping for set: {set_name}")
        repository = get_repository()

        with SmashUpWebClient() as web_client:
            set_scraper = SetScraper(web_client)
            faction_scraper = FactionScraper(web_client)

            # Scrape set data
            set_data = set_scraper.scrape_set_data(set_name)
            repository.save_set(set_data)

            # Scrape all factions in the set
            factions = set_scraper.scrape_set_factions(set_name)
            for faction_name in factions:
                faction_result = faction_scraper.scrape(
                    faction_name, set_data.set_id
                )
                if not faction_result.success:
                    logger.error(
                        f"Failed to scrape faction {faction_name} in set "
                        f"{set_name}: {faction_result.errors}"
                    )

        logger.info(f"Background set scraping completed for {set_name}")

    except Exception as e:
        logger.error(f"Background set scraping failed for {set_name}: {e}")


async def _background_scrape_all():
    """Background task for scraping all data."""
    try:
        logger.info("Starting background scraping for all data")
        repository = get_repository()

        with SmashUpWebClient() as web_client:
            set_scraper = SetScraper(web_client)
            faction_scraper = FactionScraper(web_client)

            # Get all available sets
            available_sets = set_scraper.get_available_sets()
            logger.info(f"Found {len(available_sets)} sets to scrape")

            for set_name in available_sets:
                try:
                    # Scrape set data
                    set_data = set_scraper.scrape_set_data(set_name)
                    repository.save_set(set_data)

                    # Scrape all factions in the set
                    factions = set_scraper.scrape_set_factions(set_name)
                    for faction_name in factions:
                        faction_result = faction_scraper.scrape(
                            faction_name, set_data.set_id
                        )
                        if not faction_result.success:
                            logger.error(
                                f"Failed to scrape faction {faction_name} in "
                                f"set {set_name}: {faction_result.errors}"
                            )

                except Exception as e:
                    logger.error(f"Error scraping set {set_name}: {e}")

        logger.info("Background scraping for all data completed")

    except Exception as e:
        logger.error(f"Background scraping for all data failed: {e}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("PySmash Scraper API starting up...")
    # Repository will be created lazily when first needed


# Main entry point for running with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)