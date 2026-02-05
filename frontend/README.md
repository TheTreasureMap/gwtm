# GWTM Frontend

Modern SvelteKit frontend for the Gravitational Wave Treasure Map (GWTM) system.

## Overview

This frontend provides the web interface for managing gravitational wave observations, replacing the legacy Flask/Jinja2 templates. It connects to the FastAPI backend.

### Technology Stack

- **Framework**: SvelteKit 2.x with Svelte 5
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4.x
- **HTTP Client**: Axios
- **Testing**: Vitest with Testing Library
- **Build**: Vite

## Project Structure

```
frontend/
├── src/
│   ├── routes/                 # SvelteKit file-based routing
│   │   ├── +page.svelte        # Home page
│   │   ├── +layout.svelte      # Global layout
│   │   ├── alerts/             # GW alert pages
│   │   ├── search/             # Search pointings/instruments
│   │   ├── submit/             # Submit pointings/instruments
│   │   ├── login/              # Authentication
│   │   ├── register/           # User registration
│   │   ├── manage/             # User management
│   │   ├── instrument/         # Instrument details
│   │   └── documentation/      # Help and tutorials
│   └── lib/
│       ├── api/
│       │   ├── client.ts       # Axios HTTP client
│       │   ├── services/       # API service functions
│       │   └── types/          # TypeScript interfaces
│       ├── components/         # Reusable UI components
│       ├── stores/             # Svelte stores (auth, forms)
│       ├── validation/         # Form validation
│       ├── utils/              # Utility functions
│       └── design-system/      # Design tokens
├── static/                     # Static assets
├── Dockerfile                  # Container build
└── package.json
```

## Development

### Prerequisites

- Node.js 20+
- npm
- FastAPI backend running (port 8000)

### Commands

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# TypeScript checking
npm run check

# Linting
npm run lint

# Format code
npm run format

# Production build
npm run build

# Preview production build
npm run preview
```

The development server runs on http://localhost:5173 with hot module replacement.

## Testing

Tests use Vitest with Testing Library for component testing.

### Running Tests

```bash
# Run tests once
npm run test:run

# Run tests in watch mode
npm run test:watch

# Run with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### Test Structure

Tests are co-located with source files in `__tests__` directories:

```
src/lib/
├── utils/
│   ├── errorHandling.ts
│   └── __tests__/
│       └── errorHandling.test.ts
├── validation/
│   ├── validators.ts
│   └── __tests__/
│       └── validators.test.ts
```

### Writing Tests

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import MyComponent from './MyComponent.svelte';

describe('MyComponent', () => {
	it('renders correctly', () => {
		render(MyComponent, { props: { title: 'Test' } });
		expect(screen.getByText('Test')).toBeInTheDocument();
	});
});
```

## API Integration

The API client in `lib/api/client.ts` handles:

- Base URL configuration (environment-aware)
- JWT token injection from localStorage
- Request/response interceptors
- Error handling

### Using API Services

```typescript
import { alertService } from '$lib/api/services/alert.service';

// Fetch alerts
const alerts = await alertService.getAlerts({ page: 1, limit: 20 });
```

### Available Services

- `alert.service.ts` - GW alert operations
- `pointing.service.ts` - Telescope pointing operations
- `instrument.service.ts` - Instrument management
- `auth.service.ts` - Authentication
- `candidate.service.ts` - Candidate objects
- `galaxy.service.ts` - Galaxy catalog
- `icecube.service.ts` - IceCube events
- `doi.service.ts` - DOI operations

## Deployment

### With Skaffold (Recommended)

```bash
cd ../gwtm-helm
skaffold dev
```

This runs the full stack with hot reload:

- Frontend: http://localhost:3000
- FastAPI: http://localhost:8000

### Docker

```bash
docker build -t gwtm-frontend .
docker run -p 3000:3000 gwtm-frontend
```

## Environment Configuration

The frontend detects the API endpoint automatically:

- **Development** (`npm run dev`): Proxies to `http://localhost:8000`
- **Skaffold**: Uses Kubernetes service discovery
- **Production**: Set `PUBLIC_API_BASE_URL` environment variable

## External Dependencies

### Aladin Lite (Sky Visualization)

The sky map visualization uses [Aladin Lite v3](https://aladin.cds.unistra.fr/AladinLite/doc/), loaded from CDN in `src/app.html`.

**Current Version**: v3.7.0-beta

**Important**: We use v3.7.0-beta specifically because v3.6.x has a polygon visibility culling bug where large GW contours disappear when partially scrolled off-screen. When updating the Aladin version:

1. Test that outer probability contours remain visible when rotating/panning the sky view

**Dependencies loaded via CDN** (`src/app.html`):

- jQuery 3.7.1 (required by Aladin Lite)
- Aladin Lite v3.7.0-beta
- Plotly 2.35.2 (for coverage plots)
