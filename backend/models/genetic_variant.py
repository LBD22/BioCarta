"""
Genetic Variant Model
Stores SNP (Single Nucleotide Polymorphism) data from genetic tests
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from ..core.db import Base


class GeneticVariant(Base):
    """
    Genetic variant (SNP) from 23andMe, AncestryDNA, etc.
    """
    __tablename__ = "genetic_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # SNP identifier (e.g., "rs1801133", "rs429358")
    rsid = Column(String(50), nullable=False, index=True)
    
    # Chromosome (1-22, X, Y, MT)
    chromosome = Column(String(10), nullable=True)
    
    # Position on chromosome
    position = Column(Integer, nullable=True)
    
    # Genotype (e.g., "AA", "AG", "GG", "CT")
    genotype = Column(String(10), nullable=False)
    
    # Gene name (e.g., "MTHFR", "APOE", "FTO")
    gene = Column(String(50), nullable=True, index=True)
    
    # Clinical significance (e.g., "pathogenic", "benign", "uncertain")
    clinical_significance = Column(String(50), nullable=True)
    
    # Risk score (0-1, higher = higher risk)
    risk_score = Column(Float, nullable=True)
    
    # Interpretation (human-readable description)
    interpretation = Column(Text, nullable=True)
    
    # Source of genetic data (23andme, ancestry, promethease, etc.)
    source = Column(String(50), nullable=True)
    
    # Additional data (JSON) - renamed from metadata to avoid SQLAlchemy conflict
    additional_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class GeneticReport(Base):
    """
    Genetic report/upload record
    Tracks when genetic data was uploaded
    """
    __tablename__ = "genetic_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File path
    file_path = Column(String(500), nullable=True)
    
    # File type (23andme, ancestry, promethease, vcf, etc.)
    file_type = Column(String(50), nullable=True)
    
    # Number of variants imported
    variant_count = Column(Integer, default=0)
    
    # Processing status
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, error
    
    # Error message if processing failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
