# GWTM FastAPI Backend

This directory contains the FastAPI implementation of the GWTM backend API.

## Overview

The FastAPI implementation provides a modern, high-performance REST API for the Gravitational-Wave Treasure Map application. It is designed to be a drop-in replacement for the Flask-based API with improved performance, better type checking, automatic documentation, and a more modular structure.

## Directory Structure

```
server/
├── core/            # Core functionality and shared components
│   ├── enums/       # Enumeration types
│   └── schemas/     # Pydantic schemas
├── db/              # Database models and configuration
│   ├── models/      # SQLAlchemy ORM models
│   └── config.py    # Database configuration
├── routes/          # API route definitions
│   ├── instrument/  # Instrument-related routes
│   ├── pointing/    # Pointing-related routes
│   └── ...          # Other route modules
├── config.py        # Application configuration
├── main.py          # FastAPI application entry point
└── Dockerfile       # Docker configuration for deployment
```

## Development

### Setting Up a Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r server/requirements.txt
   ```

3. Run the development server:
   ```bash
   cd server
   uvicorn main:app --reload
   ```

4. Access the API documentation at http://localhost:8000/docs

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the server directory with the following variables:

```
DB_USER=treasuremap
DB_PWD=your_password
DB_NAME=treasuremap_dev
DB_HOST=localhost
DB_PORT=5432
DEBUG=True
```

## Deployment

### Using Docker

Build the Docker image:

```bash
docker build -f server/Dockerfile -t gwtm-fastapi .
```

Run the Docker container:

```bash
docker run -p 8000:8000 -e DB_HOST=postgres -e DB_PWD=your_password gwtm-fastapi
```

### Using Helm

The application can be deployed to a Kubernetes cluster using the Helm chart in the `gwtm-helm` directory:

```bash
helm install gwtm ./gwtm-helm
```

For more detailed deployment instructions, see the `gwtm-helm/README.md` file.

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