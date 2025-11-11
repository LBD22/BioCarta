import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .core.db import Base, engine
from .api import auth, biomarkers, measurements, uploads, dashboard, export, timeline, integrations, genetics, bioage

app = FastAPI(title=settings.app_name)
Base.metadata.create_all(bind=engine)

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
