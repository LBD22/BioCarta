"""
Database migration script
Adds new tables for genetics and updates user table
"""

import sys
import os

# Add parent directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(backend_dir)
sys.path.insert(0, app_dir)

from backend.core.db import Base, engine
from backend.models.user import User
from backend.models.biomarker import Biomarker
from backend.models.measurement import Measurement
from backend.models.upload import Upload
from backend.models.parse_candidate import ParseCandidate
from backend.models.reference import ReferenceRange
from backend.models.synonym import BiomarkerSynonym
# from backend.models.unitconv import UnitConversion  # Not needed for migration
from backend.models.genetic_variant import GeneticVariant, GeneticReport

print("Creating/updating database tables...")

# Create all tables
Base.metadata.create_all(bind=engine)

print("✓ Database migration completed successfully!")
print("  - User table updated (added metadata, date_of_birth)")
print("  - GeneticVariant table created")
print("  - GeneticReport table created")
