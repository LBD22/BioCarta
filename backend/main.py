import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .core.db import Base, engine
from .api import auth, biomarkers, measurements, uploads, dashboard, export, timeline, integrations, genetics, bioage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
Base.metadata.create_all(bind=engine)

# Initialize database with seed data on startup
try:
    from .seeds.load_all import load
    logger.info("Starting database seed data initialization...")
    load()
    logger.info("✓ Database initialized with seed data successfully")
except Exception as e:
    logger.error(f"⚠ Seed data initialization failed: {e}", exc_info=True)

app.include_router(auth.router)
app.include_router(biomarkers.router)
app.include_router(measurements.router)
app.include_router(uploads.router)
app.include_router(dashboard.router)
app.include_router(export.router)
app.include_router(timeline.router)
app.include_router(integrations.router)
app.include_router(genetics.router)
app.include_router(bioage.router)

# Mount static files after API routes to avoid conflicts
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
