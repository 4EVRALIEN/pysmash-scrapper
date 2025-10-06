"""
FastAPI web service for the PySmash scraper.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from .models import HealthCheck, ScrapingResult
from .database.repository import SmashUpRepository
from .scrapers.set_scraper import SetScraper
from .scrapers.faction_scraper import FactionScraper
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
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global repository instance
repository = SmashUpRepository("sqlite:///data/smashup.db")


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
        sets = repository.get_all_sets()
        return sets
    except Exception as e:
        logger.error(f"Error retrieving sets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sets")


@app.get("/sets/{set_id}/factions", response_model=List[Dict[str, Any]])
async def get_factions_by_set(set_id: str):
    """Get all factions for a specific set."""
    try:
        factions = repository.get_factions_by_set(set_id)
        if not factions:
            raise HTTPException(status_code=404, detail="Set not found or no factions available")
        return factions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving factions for set {set_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve factions")


@app.post("/scrape/faction/{faction_name}", response_model=ScrapingResult)
async def scrape_faction(faction_name: str, background_tasks: BackgroundTasks, set_name: str = None):
    """Trigger scraping for a specific faction."""
    try:
        # Add the scraping task to background tasks
        background_tasks.add_task(
            _background_scrape_faction, 
            faction_name, 
            set_name
        )
        
        return ScrapingResult(
            success=True,
            message=f"Faction scraping for '{faction_name}' started in background",
            items_processed=0,
            errors=[]
        )
    except Exception as e:
        logger.error(f"Error starting faction scraping for {faction_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scraping")


@app.post("/scrape/set/{set_name}", response_model=ScrapingResult)
async def scrape_set(set_name: str, background_tasks: BackgroundTasks):
    """Trigger scraping for a specific set."""
    try:
        # Add the scraping task to background tasks
        background_tasks.add_task(_background_scrape_set, set_name)
        
        return ScrapingResult(
            success=True,
            message=f"Set scraping for '{set_name}' started in background",
            items_processed=0,
            errors=[]
        )
    except Exception as e:
        logger.error(f"Error starting set scraping for {set_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scraping")


@app.post("/scrape/all", response_model=ScrapingResult)
async def scrape_all(background_tasks: BackgroundTasks):
    """Trigger scraping for all data."""
    try:
        background_tasks.add_task(_background_scrape_all)
        
        return ScrapingResult(
            success=True,
            message="Full scraping started in background",
            items_processed=0,
            errors=[]
        )
    except Exception as e:
        logger.error(f"Error starting full scraping: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scraping")


@app.delete("/data/clear")
async def clear_database():
    """Clear all data from the database."""
    try:
        success = repository.clear_all_data()
        if success:
            return {"message": "Database cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear database")
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear database")


# Background task functions
async def _background_scrape_faction(faction_name: str, set_name: str = None):
    """Background task for scraping a faction."""
    try:
        logger.info(f"Starting background scraping for faction: {faction_name}")
        
        with SmashUpWebClient() as web_client:
            faction_scraper = FactionScraper(web_client)
            
            # Generate or get set_id
            set_id = None
            if set_name:
                set_scraper = SetScraper(web_client)
                set_data = set_scraper.scrape_set_data(set_name)
                set_id = set_data.set_id
                repository.insert_set(set_data)
            
            result = faction_scraper.scrape(faction_name, set_id)
            
            if result.success:
                logger.info(f"Successfully completed faction scraping: {faction_name}")
            else:
                logger.error(f"Failed faction scraping: {faction_name} - {result.message}")
                
    except Exception as e:
        logger.error(f"Background faction scraping failed for {faction_name}: {e}")


async def _background_scrape_set(set_name: str):
    """Background task for scraping a set."""
    try:
        logger.info(f"Starting background scraping for set: {set_name}")
        
        with SmashUpWebClient() as web_client:
            set_scraper = SetScraper(web_client)
            result = set_scraper.scrape(set_name)
            
            if result.success:
                logger.info(f"Successfully completed set scraping: {set_name}")
            else:
                logger.error(f"Failed set scraping: {set_name} - {result.message}")
                
    except Exception as e:
        logger.error(f"Background set scraping failed for {set_name}: {e}")


async def _background_scrape_all():
    """Background task for scraping all data."""
    try:
        logger.info("Starting background scraping for all data")
        
        with SmashUpWebClient() as web_client:
            set_scraper = SetScraper(web_client)
            faction_scraper = FactionScraper(web_client)
            
            sets = set_scraper.get_available_sets()
            total_processed = 0
            
            for set_name in sets:
                try:
                    # Scrape set data
                    set_data = set_scraper.scrape_set_data(set_name)
                    repository.insert_set(set_data)
                    total_processed += 1
                    
                    # Scrape factions for this set
                    factions = set_scraper.scrape_set_factions(set_name)
                    
                    for faction_name in factions:
                        if not faction_name.strip():
                            continue
                        
                        try:
                            faction_data = faction_scraper.scrape_faction_data(
                                faction_name, set_data.set_id
                            )
                            repository.insert_faction(faction_data)
                            
                            # Scrape cards for this faction
                            faction_scraper.scrape_faction_cards(
                                faction_name, faction_data.faction_id
                            )
                            total_processed += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing faction {faction_name}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error processing set {set_name}: {e}")
            
            logger.info(f"Successfully completed full scraping: {total_processed} items processed")
            
    except Exception as e:
        logger.error(f"Background full scraping failed: {e}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("PySmash Scraper API starting up...")
    logger.info("Database initialized and ready")


# Main entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
