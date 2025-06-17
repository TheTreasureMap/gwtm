# GWTM Frontend

**⚠️ Work in Progress**: Modern SvelteKit frontend for the Gravitational Wave Treasure Map (GWTM) system, currently under active development.

## Overview

This frontend provides a modern web interface for managing gravitational wave observations, replacing the legacy Flask templates. It connects to the FastAPI backend and provides features for:

- **GW Alerts Management**: Browse and filter gravitational wave events ✅
- **Telescope Pointings**: View observation data and statistics 🚧
- **Real-time Data**: Live updates from LIGO/Virgo detectors 🚧
- **Responsive Design**: Works on desktop and mobile devices ✅

**Current Status**: Basic GW alerts functionality implemented. Additional features being migrated from Flask templates.

## Architecture

- **Framework**: SvelteKit with TypeScript
- **Styling**: Tailwind CSS for responsive design
- **API Integration**: RESTful calls to FastAPI backend
- **Deployment**: Static build with adapter-static for production

## Development

### Prerequisites
- Node.js 18+ and npm
- FastAPI backend running on port 8000

### Local Development

```bash
# Install dependencies
npm install

# Start development server (connects to localhost:8000 API)
npm run dev

# Open in browser
npm run dev -- --open
```

The development server runs on http://localhost:5173 and automatically proxies API calls to the FastAPI backend.

### Environment Configuration

The frontend automatically detects the API endpoint:
- **Development**: Uses `http://localhost:8000` (with port forwarding)
- **Production**: Uses `PUBLIC_API_BASE_URL` environment variable

### Building for Production

```bash
# Create production build
npm run build

# Preview production build locally
npm run preview
```

## Deployment

### Kubernetes with Helm

The frontend is deployed as part of the GWTM Helm chart:

```bash
cd ../gwtm-helm
skaffold dev  # Full development environment with hot reload
```

This provides:
- Frontend at http://localhost:3000
- FastAPI at http://localhost:8000  
- PostgreSQL and Redis services

### Docker

The frontend uses a multi-stage Dockerfile:
- **Development**: Node.js with hot reload
- **Production**: Static files served by Node.js

## Current Implementation

### ✅ Completed Features
- **GW Events Page** (`/alerts/select`): Full filtering, search, and pagination
- **API Integration**: Type-safe FastAPI client
- **URL Parameters**: Deep linking with filter state
- **Responsive Design**: Mobile-friendly interface

### 🚧 In Development
- **Authentication**: User login and permissions
- **Pointing Management**: Create and edit telescope observations
- **Dashboard**: Overview and statistics
- **Additional Pages**: Instruments, candidates, etc.

### 📋 Planned Features
- **Real-time Updates**: WebSocket integration
- **Data Visualisation**: Charts and maps
- **Export Functions**: Data download capabilities
- **Advanced Filtering**: Complex query builder

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   └── api.ts          # FastAPI client
│   ├── routes/
│   │   ├── alerts/
│   │   │   └── select/     # GW events page (completed)
│   │   └── +layout.svelte  # Global layout
│   └── app.html           # Main template
├── static/               # Static assets (favicon, etc.)
├── Dockerfile           # Multi-stage build
└── svelte.config.js    # SvelteKit configuration
```

## Code Quality

```bash
# Type checking
npm run check

# Linting and formatting  
npm run lint
npm run format
```

## Migration Notes

This frontend is **actively replacing** the Flask Jinja2 templates. Current progress:

- **✅ GW Events**: Fully migrated with enhanced functionality
- **🚧 Other Pages**: Being migrated incrementally
- **📋 Flask Templates**: Still available as fallback during transition

For Flask template equivalents, see the legacy `src/templates/` directory in the main project.

## Contributing

This is an active work in progress. When contributing:
1. Check existing implementation patterns in `/routes/alerts/select/`
2. Maintain TypeScript coverage
3. Follow established API client patterns in `lib/api.ts`
4. Test with both development and production builds