# GWTM FastAPI Backend

This directory contains the FastAPI implementation of the GWTM backend API.

## Overview

The FastAPI implementation provides a modern, high-performance REST API for the Gravitational-Wave Treasure Map application. It is designed to be a drop-in replacement for the Flask-based API with improved performance, better type checking, automatic documentation, and a more modular structure.

## Directory Structure

```
server/
├── auth/            # Authentication utilities
│   └── auth.py      # JWT token handling and user authentication
├── core/            # Core functionality and shared components
│   └── enums/       # Enumeration types (bandpass, depth_unit, etc.)
├── db/              # Database models and configuration
│   ├── models/      # SQLAlchemy ORM models
│   ├── config.py    # Database configuration
│   ├── database.py  # Database connection and session management
│   └── utils.py     # Database utility functions
├── routes/          # API route definitions
│   ├── pointing/    # Pointing management routes
│   │   ├── router.py           # Consolidated pointing router
│   │   ├── create_pointings.py # POST /pointings endpoint
│   │   ├── get_pointings.py    # GET /pointings endpoint
│   │   ├── update_pointings.py # POST /update_pointings endpoint
│   │   ├── cancel_all.py       # POST /cancel_all endpoint
│   │   ├── request_doi.py      # POST /request_doi endpoint
│   │   └── test_refactoring.py # GET /test_refactoring endpoint
│   ├── instrument/  # Instrument management routes
│   │   ├── router.py           # Consolidated instrument router
│   │   ├── get_instruments.py  # GET /instruments endpoint
│   │   ├── get_footprints.py   # GET /footprints endpoint
│   │   ├── create_instrument.py# POST /instruments endpoint
│   │   └── create_footprint.py # POST /footprints endpoint
│   ├── admin/       # Admin-related routes
│   │   ├── router.py           # Consolidated admin router
│   │   └── fixdata.py          # GET/POST /fixdata endpoint
│   ├── candidate/   # Candidate management routes
│   │   ├── router.py           # Consolidated candidate router
│   │   ├── get_candidates.py   # GET /candidate endpoint
│   │   ├── create_candidates.py# POST /candidate endpoint
│   │   ├── update_candidate.py # PUT /candidate endpoint
│   │   └── delete_candidates.py# DELETE /candidate endpoint
│   ├── doi/         # DOI request routes
│   │   ├── router.py           # Consolidated DOI router
│   │   ├── get_doi_pointings.py# GET /doi_pointings endpoint
│   │   ├── get_author_groups.py# GET /doi_author_groups endpoint
│   │   └── get_authors.py      # GET /doi_authors/{group_id} endpoint
│   ├── gw_alert/    # GW alert management routes
│   │   ├── router.py           # Consolidated GW alert router
│   │   ├── query_alerts.py     # GET /query_alerts endpoint
│   │   ├── post_alert.py       # POST /post_alert endpoint
│   │   ├── get_skymap.py       # GET /gw_skymap endpoint
│   │   ├── get_contour.py      # GET /gw_contour endpoint
│   │   ├── get_grb_moc.py      # GET /grb_moc_file endpoint
│   │   └── delete_test_alerts.py # POST /del_test_alerts endpoint
│   ├── gw_galaxy/   # Galaxy catalog management routes
│   │   ├── router.py           # Consolidated galaxy router
│   │   ├── get_event_galaxies.py # GET /event_galaxies endpoint
│   │   ├── post_event_galaxies.py # POST /event_galaxies endpoint
│   │   ├── remove_event_galaxies.py # DELETE /remove_event_galaxies endpoint
│   │   └── get_glade.py        # GET /glade endpoint
│   ├── icecube/     # IceCube neutrino event routes
│   │   ├── router.py           # Consolidated IceCube router
│   │   └── post_icecube_notice.py # POST /post_icecube_notice endpoint
│   ├── event/       # Event candidate management routes
│   │   ├── router.py           # Consolidated event router
│   │   ├── utils.py            # Utility functions for event routes
│   │   ├── get_candidate_events.py # GET /candidate/event endpoint
│   │   ├── create_candidate_event.py # POST /candidate/event endpoint
│   │   ├── update_candidate_event.py # PUT /candidate/event/{candidate_id} endpoint
│   │   └── delete_candidate_event.py # DELETE /candidate/event/{candidate_id} endpoint
│   └── ui/          # UI-specific endpoints (AJAX helpers)
│       ├── router.py           # Consolidated UI router
│       ├── alert_instruments_footprints.py # GET /ajax_alertinstruments_footprints
│       ├── preview_footprint.py # GET /ajax_preview_footprint
│       ├── resend_verification_email.py # POST /ajax_resend_verification_email
│       ├── coverage_calculator.py # POST /ajax_coverage_calculator
│       ├── spectral_range_from_bands.py # GET /ajax_update_spectral_range_from_selected_bands
│       ├── pointing_from_id.py # GET /ajax_pointingfromid
│       ├── grade_calculator.py # POST /ajax_grade_calculator
│       ├── icecube_notice.py   # GET /ajax_icecube_notice
│       ├── event_galaxies.py   # GET /ajax_event_galaxies
│       ├── scimma_xrt.py       # GET /ajax_scimma_xrt
│       ├── candidate_fetch.py  # GET /ajax_candidate
│       ├── request_doi.py      # GET /ajax_request_doi
│       └── alert_type.py       # GET /ajax_alerttype
├── schemas/         # Pydantic schemas for validation
│   ├── candidate.py # Candidate schemas
│   ├── doi.py       # DOI schemas
│   ├── glade.py     # GLADE catalog schemas
│   ├── gw_alert.py  # GW alert schemas
│   ├── gw_galaxy.py # Galaxy schemas
│   ├── icecube.py   # IceCube schemas
│   ├── instrument.py# Instrument schemas
│   ├── pointing.py  # Pointing schemas
│   └── users.py     # User schemas
├── utils/           # Utility functions
│   ├── email.py     # Email utilities
│   ├── error_handling.py # Error handling utilities
│   ├── function.py  # General utility functions
│   ├── gwtm_io.py   # File I/O utilities
│   ├── pointing.py  # Pointing validation and creation utilities
│   └── spectral.py  # Spectral range calculations and conversions
├── config.py        # Application configuration
├── main.py          # FastAPI application entry point
├── requirements.txt # Python dependencies
└── Dockerfile       # Docker configuration for deployment
```

## Development

### Preferred Development Setup with Skaffold

The recommended way to run the development server is using Skaffold, which manages the full application stack including database, cache, and all services:

1. **Prerequisites:**
   - [Skaffold](https://skaffold.dev/docs/install/) installed
   - [kubectl](https://kubernetes.io/docs/tasks/tools/) configured for local cluster (minikube, kind, or Docker Desktop)
   - [Helm](https://helm.sh/docs/intro/install/) installed

2. **Start the development environment:**
   ```bash
   cd gwtm-helm
   skaffold dev
   ```

   This will:
   - Build Docker images for all services
   - Deploy the complete stack to your local Kubernetes cluster
   - Watch for file changes and automatically rebuild/redeploy
   - Forward ports to access services locally

3. **Access the services:**
   - FastAPI server: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Database: localhost:5432
   - Redis cache: localhost:6379

4. **Load test data** (required for running tests):
   ```bash
   kubectl exec -it deployment/database -- psql -U treasuremap -d treasuremap_dev -f /docker-entrypoint-initdb.d/test-data.sql
   ```

### Alternative: Local Development

If you prefer to run only the FastAPI server locally:

1. **Set up the database:**
   - Ensure PostgreSQL is running with PostGIS extension
   - Create a database named `treasuremap_dev`
   - Load test data: `psql -U treasuremap -d treasuremap_dev -f tests/test-data.sql`

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r server/requirements.txt
   ```

4. **Set environment variables:**
   Create a `.env` file in the server directory:
   ```
   DB_USER=treasuremap
   DB_PWD=your_password
   DB_NAME=treasuremap_dev
   DB_HOST=localhost
   DB_PORT=5432
   DEBUG=True
   ```

5. **Run the development server:**
   ```bash
   cd server
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Testing

The FastAPI application includes comprehensive tests to ensure functionality and compatibility with the Flask implementation.

### Prerequisites for Testing

1. **Install test dependencies:**
   ```bash
   pip install -r tests/requirements.txt
   ```

2. **Ensure FastAPI server is running:**
   - Using Skaffold: `skaffold dev` (FastAPI available at http://localhost:8000)
   - Using local setup: `uvicorn main:app --reload` (from server directory)

3. **Load test data:** Tests automatically load fresh test data before running, but you can also load manually:
   ```bash
   # Using Skaffold/Kubernetes
   gwtm-helm/restore-db tests/test-data.sql
   
   # Using local database
   psql -U treasuremap -d treasuremap_dev -f tests/test-data.sql
   ```

### Running Tests

**From the project root directory:**

```bash
# Run all FastAPI tests
python -m pytest tests/fastapi/ -v --disable-warnings

# Run specific test modules
python -m pytest tests/fastapi/test_pointing.py -v
python -m pytest tests/fastapi/test_instrument.py -v
python -m pytest tests/fastapi/test_ui.py -v

# Run with more verbose output
python -m pytest tests/fastapi/ -vv

# Run with coverage reporting
python -m pytest tests/fastapi/ -v --cov=server
```

**Using the test script:**

```bash
# Run all tests
./gwtm-helm/run-module-tests.sh

# Run specific module (e.g., pointing tests)
./gwtm-helm/run-module-tests.sh pointing
```

### Test Configuration

Tests are configured in `tests/fastapi/conftest.py` which:
- Automatically waits for the FastAPI server to be ready
- Loads fresh test data before running tests
- Provides common fixtures for API URLs, headers, and test tokens

### Environment Variables

Set these environment variables if your setup differs from defaults:

```bash
export API_BASE_URL="http://localhost:8000"  # FastAPI server URL
export DB_HOST="localhost"                   # Database host
export DB_PORT="5432"                        # Database port
export DB_NAME="treasuremap"                 # Database name
export DB_USER="treasuremap"                 # Database user
export DB_PWD="treasuremap"                  # Database password
```

### Test Categories

- **`test_admin.py`** - Administrative functions and user management
- **`test_candidate.py`** - Candidate management and CRUD operations
- **`test_doi.py`** - DOI request and author management
- **`test_event.py`** - GW event and alert querying
- **`test_gw_alert.py`** - GW alert management
- **`test_gw_galaxy.py`** - Galaxy catalog management
- **`test_icecube.py`** - IceCube neutrino event integration
- **`test_instrument.py`** - Instrument management and validation
- **`test_pointing.py`** - Pointing CRUD operations and validation
- **`test_ui.py`** - UI-specific endpoints and AJAX helpers

### Test Data

The test suite uses predefined data from `tests/test-data.sql` which includes:
- Sample GW alerts with known GraceIDs
- Test users with various permission levels
- Sample instruments and their configurations
- Test pointings and observations
- Galaxy catalog entries

**Note:** Always ensure test data is loaded before running tests, as many tests depend on specific entries existing in the database.

## Deployment

### Production Deployment with Helm

The recommended deployment method is using the Helm chart which deploys the complete GWTM stack:

```bash
# Deploy to production
cd gwtm-helm
helm install gwtm . -f values-prod.yaml

# Deploy to development/staging
helm install gwtm-dev . -f values-dev.yaml
```

The Helm chart includes:
- FastAPI backend service
- PostgreSQL database with PostGIS
- Redis cache
- Frontend service
- Ingress configuration
- Persistent volumes for data storage

For detailed deployment configuration, see `gwtm-helm/README.md`.

### Development Deployment with Skaffold

For development environments with automatic rebuilds:

```bash
cd gwtm-helm
skaffold run  # Deploy once
# or
skaffold dev  # Deploy with file watching and auto-rebuild
```

### Using Docker (Standalone)

To run just the FastAPI service in a container:

```bash
# Build the Docker image
docker build -f server/Dockerfile -t gwtm-fastapi .

# Run with required environment variables
docker run -p 8000:8000 \
  -e DB_HOST=your-postgres-host \
  -e DB_USER=treasuremap \
  -e DB_PWD=your_password \
  -e DB_NAME=treasuremap \
  gwtm-fastapi
```

**Note:** The FastAPI service requires a PostgreSQL database with PostGIS extension and Redis cache for full functionality.

## API Documentation

The API documentation is automatically generated and available at `/docs` when the application is running. It provides:

- Interactive API documentation
- Request/response examples
- Schema definitions
- Authentication information

## Authentication

The API uses JWT-based authentication. To authenticate:

1. Send a POST request to `/api/v1/login` with username and password
2. Use the returned token in the `Authorization` header as `Bearer <token>` for protected endpoints