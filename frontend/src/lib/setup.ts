import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/svelte';
import { vi, afterEach } from 'vitest';

// Mock console methods to avoid noise in tests unless needed
global.console = {
	...console,
	log: vi.fn(),
	debug: vi.fn(),
	info: vi.fn(),
	warn: vi.fn(),
	error: vi.fn()
};

// Mock window.fetch for API-related tests
global.fetch = vi.fn();

// Mock window.location if needed
Object.defineProperty(window, 'location', {
	value: {
		hostname: 'localhost',
		port: '5173',
		protocol: 'http:',
		href: 'http://localhost:5173/',
		origin: 'http://localhost:5173'
	},
	writable: true
});

// Mock environment variables
vi.mock('$env/static/public', () => ({
	PUBLIC_API_BASE_URL: 'http://localhost:8000'
}));

vi.mock('$env/dynamic/public', () => ({
	env: {
		PUBLIC_API_BASE_URL: 'http://localhost:8000'
	}
}));

// SvelteKit runtime modules. Components import these directly, and outside a
// running SvelteKit app they do not resolve.
vi.mock('$app/environment', () => ({
	browser: true,
	dev: true,
	building: false,
	version: 'test'
}));

vi.mock('$app/navigation', () => ({
	goto: vi.fn(),
	invalidate: vi.fn(),
	invalidateAll: vi.fn(),
	pushState: vi.fn(),
	replaceState: vi.fn()
}));

vi.mock('$app/stores', async () => {
	// vi.mock factories are hoisted above imports, so the real module has to be
	// pulled in here rather than referenced from a top-level import.
	const { readable } = await vi.importActual<typeof import('svelte/store')>('svelte/store');
	return {
		page: readable({
			url: new URL('http://localhost:5173/'),
			params: {},
			route: { id: null },
			status: 200,
			error: null,
			data: {},
			form: null
		}),
		navigating: readable(null),
		updated: Object.assign(readable(false), { check: vi.fn() })
	};
});

// Setup cleanup after each test
afterEach(() => {
	cleanup();
	vi.clearAllMocks();
});

// Custom matchers or test utilities can be added here
export {};
