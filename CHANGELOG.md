# BioCarta Changelog

## Version 2.0.0 (November 11, 2024)

### 🎉 Major Features Added

#### 1. Apple Health Integration
- **File**: `/app/backend/domain/apple_health.py`
- **Endpoint**: `POST /uploads` (auto-detects Apple Health ZIP/XML)
- **Features**:
  - Import health data from iPhone/Apple Watch
  - Supports 15+ data types (weight, BMI, HR, HRV, blood pressure, SpO2, glucose, etc.)
  - Automatic deduplication by date
  - Handles both ZIP archives and raw XML files
  - Maps Apple Health types to BioCarta biomarkers

#### 2. WHOOP OAuth Integration
- **Files**: 
  - `/app/backend/domain/whoop_integration.py`
  - `/app/backend/api/integrations.py`
  - `/app/frontend/src/integrations_page.tsx`
- **Endpoints**:
  - `GET /integrations/whoop/auth` - Get authorization URL
  - `GET /integrations/whoop/callback` - OAuth callback
  - `POST /integrations/whoop/sync` - Sync data (1-90 days)
  - `DELETE /integrations/whoop/disconnect` - Disconnect
- **Metrics**: HRV, RHR, Respiratory Rate, SpO2, Weight, Body Fat %
- **Features**:
  - OAuth 2.0 Authorization Code Flow
  - Secure token storage in database
  - Automatic token refresh
  - Configurable sync period

#### 3. Oura Ring OAuth Integration
- **Files**:
  - `/app/backend/domain/oura_integration.py`
  - `/app/backend/api/integrations.py`
  - `/app/frontend/src/integrations_page.tsx`
- **Endpoints**:
  - `GET /integrations/oura/auth` - Get authorization URL
  - `GET /integrations/oura/callback` - OAuth callback
  - `POST /integrations/oura/sync` - Sync data (1-90 days)
  - `DELETE /integrations/oura/disconnect` - Disconnect
- **Metrics**: HRV, RHR, Respiratory Rate, SpO2, Heart Rate, Body Temperature
- **Features**:
  - OAuth 2.0 Authorization Code Flow
  - Daily data aggregation
  - Sleep and readiness metrics

#### 4. Genetics Module
- **Files**:
  - `/app/backend/models/genetic_variant.py` (NEW)
  - `/app/backend/domain/genetics_parser.py` (NEW)
  - `/app/backend/api/genetics.py` (NEW)
  - `/app/frontend/src/genetics_page.tsx` (NEW)
- **Endpoints**:
  - `POST /genetics/upload` - Upload genetic data
  - `GET /genetics/reports` - List reports
  - `GET /genetics/variants` - List variants
  - `GET /genetics/summary` - Get summary with risk analysis
  - `GET /genetics/variant/{rsid}` - Get variant details
  - `DELETE /genetics/reports/{id}` - Delete report
- **Supported Formats**: 23andMe TXT, AncestryDNA TXT, Promethease JSON
- **Analyzed SNPs** (10+):
  - **MTHFR** (rs1801133) - Methylation, homocysteine
  - **APOE** (rs429358) - Alzheimer's risk
  - **FTO** (rs9939609) - Obesity susceptibility
  - **COMT** (rs4680) - Stress response
  - **BDNF** (rs6265) - Memory, learning
  - **ACE** (rs4340) - Blood pressure, athletic performance
  - **ACTN3** (rs1815739) - Muscle fiber type
  - **CYP1A2** (rs762551) - Caffeine metabolism
  - **LCT** (rs4988235) - Lactose tolerance
  - **ALDH2** (rs671) - Alcohol metabolism
- **Features**:
  - Risk scoring (0-1 scale)
  - Clinical significance classification
  - Personalized interpretations
  - Privacy-focused (local storage only)

#### 5. Biological Age (BioAge)
- **Files**:
  - `/app/backend/domain/bioage.py` (NEW)
  - `/app/backend/api/bioage.py` (NEW)
  - `/app/frontend/src/bioage_page.tsx` (NEW)
- **Endpoints**:
  - `GET /bioage/phenoage` - Calculate PhenoAge (Levine 2018)
  - `GET /bioage/simple` - Calculate simplified BioAge
  - `GET /bioage/all` - Calculate all available metrics
- **Algorithms**:
  - **PhenoAge**: Scientific algorithm from Yale University
    - Requires: Albumin, Creatinine, Glucose, CRP, Lymphocyte %, MCV, RDW, ALP, WBC
    - Outputs: PhenoAge, mortality score, age delta
  - **Simplified BioAge**: Based on common biomarkers
    - Uses: Lipids, glucose, inflammation, liver, kidney, blood markers
    - Outputs: BioAge, aging score, age delta
- **Features**:
  - Age delta calculation (biological vs chronological)
  - Personalized interpretations
  - Recommendations for improvement

#### 6. InBody PDF Parsing (Enhanced)
- **File**: `/app/backend/domain/parsing.py` (updated)
- **Features**:
  - Auto-detection of InBody reports
  - Extracts body composition metrics
  - Supports multiple InBody models
  - OCR-based text extraction

### 🔧 Technical Changes

#### Database
- **New Tables**:
  - `genetic_variants` - Stores SNP data
  - `genetic_reports` - Tracks genetic uploads
- **Updated Tables**:
  - `users` - Added `integration_data` (JSON), `date_of_birth` (Date)
- **Migration**: `/app/backend/migrate_db.py`

#### Backend
- **New API Routers**:
  - `/integrations` - WHOOP/Oura OAuth
  - `/genetics` - Genetics module
  - `/bioage` - Biological age calculations
- **New Domain Modules**:
  - `apple_health.py` - Apple Health parser
  - `whoop_integration.py` - WHOOP API client
  - `oura_integration.py` - Oura API client
  - `genetics_parser.py` - Genetics data parser
  - `bioage.py` - Biological age algorithms
- **Updated Modules**:
  - `parsing.py` - Added Apple Health and InBody support
  - `uploads.py` - Support for ZIP and XML files
  - `main.py` - Registered new routers

#### Frontend
- **New Pages**:
  - `integrations_page.tsx` - WHOOP/Oura management
  - `bioage_page.tsx` - Biological age dashboard
  - `genetics_page.tsx` - Genetics analysis
- **Features**:
  - Modern UI with gradients
  - Risk scoring visualizations
  - OAuth flow handling
  - File upload with progress

#### Dependencies
- **Added**:
  - `requests` - HTTP client for API integrations
  - `python-dateutil` - Date parsing
- **Updated**:
  - `pydantic-settings` - Configuration management

### 📝 Documentation
- **NEW_FEATURES.md** - Comprehensive feature documentation
- **CHANGELOG.md** - This file

### 🔐 Security
- OAuth tokens stored securely in database (encrypted)
- Genetic data stored locally (not shared)
- API keys managed via environment variables

### 🚀 Deployment
- Updated `requirements.txt`
- Database migration script
- Environment variables for OAuth:
  - `WHOOP_CLIENT_ID`
  - `WHOOP_CLIENT_SECRET`
  - `WHOOP_REDIRECT_URI`
  - `OURA_CLIENT_ID`
  - `OURA_CLIENT_SECRET`
  - `OURA_REDIRECT_URI`

### 🐛 Bug Fixes
- Fixed SQLAlchemy reserved keyword conflict (`metadata` → `integration_data`, `additional_data`)
- Fixed import paths in migration script
- Fixed model class names (`Synonym` → `BiomarkerSynonym`)

### 📊 Statistics
- **Lines of Code Added**: ~3,500+
- **New Files**: 10
- **Updated Files**: 8
- **New API Endpoints**: 15+
- **New Database Tables**: 2
- **Supported SNPs**: 10
- **Supported Integrations**: 3 (Apple Health, WHOOP, Oura)

---

## Version 1.0.0 (November 9-10, 2024)

### Initial Release
- Basic biomarker tracking (67 biomarkers)
- File upload (CSV, XLSX, PDF)
- OCR parsing
- Automatic biomarker matching (119 synonyms)
- Composite metrics (BMI, Non-HDL, eGFR)
- Dashboard with statistics
- Russian localization
- Docker deployment
- GitHub integration
- Render.com deployment

---

## Roadmap (Future Versions)

### Version 2.1.0 (Planned)
- [ ] Frontend route integration for new pages
- [ ] Advanced charts (Chart.js/Recharts)
- [ ] Export to PDF reports
- [ ] Email notifications
- [ ] Multi-user support enhancements

### Version 2.2.0 (Planned)
- [ ] Garmin integration
- [ ] Fitbit integration
- [ ] Ultrasound/MRI image processing
- [ ] AI-powered insights
- [ ] Personalized recommendations engine

### Version 3.0.0 (Planned)
- [ ] Mobile app (React Native)
- [ ] Telemedicine integration
- [ ] Doctor dashboard
- [ ] Advanced genetics (polygenic risk scores)
- [ ] Epigenetics (methylation clocks)
