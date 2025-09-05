import '@testing-library/jest-dom';
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
	PUBLIC_API_URL: 'http://localhost:8000'
}));

vi.mock('$env/dynamic/public', () => ({
	env: {
		PUBLIC_API_URL: 'http://localhost:8000'
	}
}));

// Setup cleanup after each test
afterEach(() => {
	vi.clearAllMocks();
});

// Custom matchers or test utilities can be added here
export {};
