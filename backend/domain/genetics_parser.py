"""
Genetics Data Parser
Parses genetic data from 23andMe, AncestryDNA, and other formats
"""

import csv
import json
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.genetic_variant import GeneticVariant, GeneticReport
from ..models.user import User


# Known SNPs with health implications
# Format: rsid -> {gene, risk_allele, condition, interpretation}
KNOWN_SNPS = {
    # MTHFR - Methylation, homocysteine metabolism
    "rs1801133": {
        "gene": "MTHFR",
        "risk_allele": "T",
        "condition": "Elevated homocysteine",
        "interpretation": {
            "CC": "Normal MTHFR function",
            "CT": "Mildly reduced MTHFR activity (~65%)",
            "TT": "Significantly reduced MTHFR activity (~30%), may need B vitamin supplementation"
        }
    },
    
    # APOE - Alzheimer's risk
    "rs429358": {
        "gene": "APOE",
        "risk_allele": "C",
        "condition": "Alzheimer's disease risk",
        "interpretation": {
            "TT": "APOE e3/e3 - Average risk",
            "TC": "APOE e3/e4 - 2-3x increased risk",
            "CC": "APOE e4/e4 - 8-12x increased risk"
        }
    },
    
    # FTO - Obesity risk
    "rs9939609": {
        "gene": "FTO",
        "risk_allele": "A",
        "condition": "Obesity susceptibility",
        "interpretation": {
            "TT": "Lower obesity risk",
            "AT": "Moderately increased obesity risk",
            "AA": "Higher obesity risk, benefits more from exercise"
        }
    },
    
    # COMT - Dopamine metabolism
    "rs4680": {
        "gene": "COMT",
        "risk_allele": "A",
        "condition": "Stress response, pain sensitivity",
        "interpretation": {
            "GG": "Warrior gene - better under stress, lower pain sensitivity",
            "AG": "Intermediate",
            "AA": "Worrier gene - more sensitive to stress and pain"
        }
    },
    
    # BDNF - Brain-derived neurotrophic factor
    "rs6265": {
        "gene": "BDNF",
        "risk_allele": "A",
        "condition": "Memory, learning",
        "interpretation": {
            "GG": "Normal BDNF function",
            "AG": "Slightly reduced BDNF",
            "AA": "Reduced BDNF, may affect memory and learning"
        }
    },
    
    # ACE - Blood pressure, athletic performance
    "rs4340": {
        "gene": "ACE",
        "risk_allele": "D",
        "condition": "Blood pressure, endurance vs power",
        "interpretation": {
            "II": "Better endurance performance",
            "ID": "Balanced",
            "DD": "Better power/strength performance, higher BP risk"
        }
    },
    
    # ACTN3 - Muscle fiber type
    "rs1815739": {
        "gene": "ACTN3",
        "risk_allele": "X",
        "condition": "Muscle fiber composition",
        "interpretation": {
            "RR": "More fast-twitch muscle fibers (sprinter)",
            "RX": "Mixed muscle fiber type",
            "XX": "More slow-twitch muscle fibers (endurance)"
        }
    },
    
    # CYP1A2 - Caffeine metabolism
    "rs762551": {
        "gene": "CYP1A2",
        "risk_allele": "C",
        "condition": "Caffeine metabolism",
        "interpretation": {
            "AA": "Fast caffeine metabolizer",
            "AC": "Intermediate caffeine metabolizer",
            "CC": "Slow caffeine metabolizer, higher cardiovascular risk from coffee"
        }
    },
    
    # LCT - Lactose tolerance
    "rs4988235": {
        "gene": "LCT",
        "risk_allele": "G",
        "condition": "Lactose tolerance",
        "interpretation": {
            "AA": "Lactose tolerant",
            "AG": "Likely lactose tolerant",
            "GG": "Lactose intolerant"
        }
    },
    
    # ALDH2 - Alcohol metabolism
    "rs671": {
        "gene": "ALDH2",
        "risk_allele": "A",
        "condition": "Alcohol flush reaction",
        "interpretation": {
            "GG": "Normal alcohol metabolism",
            "GA": "Reduced alcohol tolerance, flush reaction",
            "AA": "Very poor alcohol tolerance, severe flush reaction"
        }
    }
}


def parse_23andme_txt(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse 23andMe raw data TXT file
    Format: # rsid chromosome position genotype
    """
    variants = []
    
    with open(file_path, 'r') as f:
        for line in f:
            # Skip comments
            if line.startswith('#'):
                continue
            
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue
            
            rsid = parts[0]
            chromosome = parts[1]
            position = parts[2]
            genotype = parts[3]
            
            # Skip if no genotype
            if genotype in ('--', ''):
                continue
            
            variant = {
                'rsid': rsid,
                'chromosome': chromosome,
                'position': int(position) if position.isdigit() else None,
                'genotype': genotype,
                'source': '23andme'
            }
            
            # Add interpretation if known SNP
            if rsid in KNOWN_SNPS:
                snp_info = KNOWN_SNPS[rsid]
                variant['gene'] = snp_info['gene']
                variant['interpretation'] = snp_info['interpretation'].get(genotype, "Unknown genotype")
                
                # Calculate risk score based on risk allele count
                risk_allele = snp_info['risk_allele']
                risk_count = genotype.count(risk_allele)
                variant['risk_score'] = risk_count / 2.0  # 0, 0.5, or 1.0
                
                # Clinical significance
                if risk_count == 0:
                    variant['clinical_significance'] = 'benign'
                elif risk_count == 1:
                    variant['clinical_significance'] = 'uncertain'
                else:
                    variant['clinical_significance'] = 'likely_pathogenic'
            
            variants.append(variant)
    
    return variants


def parse_ancestry_txt(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse AncestryDNA raw data TXT file
    Similar format to 23andMe
    """
    # AncestryDNA uses similar format to 23andMe
    variants = parse_23andme_txt(file_path)
    
    # Update source
    for v in variants:
        v['source'] = 'ancestry'
    
    return variants


def parse_promethease_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse Promethease JSON export
    """
    variants = []
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Promethease format varies, handle common structures
    if isinstance(data, list):
        for item in data:
            variant = {
                'rsid': item.get('rsid', ''),
                'genotype': item.get('genotype', ''),
                'gene': item.get('gene', ''),
                'interpretation': item.get('summary', ''),
                'clinical_significance': item.get('magnitude', 'unknown'),
                'source': 'promethease'
            }
            variants.append(variant)
    
    return variants


def import_genetic_data(db: Session, user: User, file_path: str, file_type: str = 'auto') -> GeneticReport:
    """
    Import genetic data from file
    Returns GeneticReport with import status
    """
    # Create report record
    report = GeneticReport(
        user_id=user.id,
        file_path=file_path,
        file_type=file_type,
        status='processing'
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    try:
        # Auto-detect file type if needed
        if file_type == 'auto':
            with open(file_path, 'r') as f:
                first_line = f.readline()
                if '23andMe' in first_line or 'rsid\tchromosome' in first_line:
                    file_type = '23andme'
                elif 'AncestryDNA' in first_line:
                    file_type = 'ancestry'
                elif first_line.startswith('{') or first_line.startswith('['):
                    file_type = 'promethease'
                else:
                    file_type = '23andme'  # Default
        
        # Parse file
        if file_type in ('23andme', 'txt'):
            variants = parse_23andme_txt(file_path)
        elif file_type == 'ancestry':
            variants = parse_ancestry_txt(file_path)
        elif file_type in ('promethease', 'json'):
            variants = parse_promethease_json(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_type}")
        
        # Filter to only known SNPs to avoid overwhelming database
        known_variants = [v for v in variants if v['rsid'] in KNOWN_SNPS]
        
        # Save to database
        for variant_data in known_variants:
            variant = GeneticVariant(
                user_id=user.id,
                rsid=variant_data['rsid'],
                chromosome=variant_data.get('chromosome'),
                position=variant_data.get('position'),
                genotype=variant_data['genotype'],
                gene=variant_data.get('gene'),
                clinical_significance=variant_data.get('clinical_significance'),
                risk_score=variant_data.get('risk_score'),
                interpretation=variant_data.get('interpretation'),
                source=variant_data.get('source'),
                additional_data=variant_data.get('metadata')
            )
            db.add(variant)
        
        db.commit()
        
        # Update report
        report.variant_count = len(known_variants)
        report.status = 'completed'
        db.commit()
    
    except Exception as e:
        report.status = 'error'
        report.error_message = str(e)
        db.commit()
        raise
    
    return report


def get_genetic_summary(db: Session, user: User) -> Dict[str, Any]:
    """
    Get summary of user's genetic data
    Returns key findings and risk factors
    """
    variants = db.query(GeneticVariant).filter(GeneticVariant.user_id == user.id).all()
    
    if not variants:
        return {
            "total_variants": 0,
            "high_risk": [],
            "moderate_risk": [],
            "genes_tested": []
        }
    
    high_risk = []
    moderate_risk = []
    genes = set()
    
    for v in variants:
        genes.add(v.gene)
        
        if v.risk_score and v.risk_score >= 0.9:
            high_risk.append({
                "rsid": v.rsid,
                "gene": v.gene,
                "genotype": v.genotype,
                "interpretation": v.interpretation,
                "risk_score": v.risk_score
            })
        elif v.risk_score and v.risk_score >= 0.4:
            moderate_risk.append({
                "rsid": v.rsid,
                "gene": v.gene,
                "genotype": v.genotype,
                "interpretation": v.interpretation,
                "risk_score": v.risk_score
            })
    
    return {
        "total_variants": len(variants),
        "high_risk": high_risk,
        "moderate_risk": moderate_risk,
        "genes_tested": sorted(list(genes))
    }
