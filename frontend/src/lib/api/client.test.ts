import { describe, it, expect, vi, beforeEach } from 'vitest';

// Helper that resets modules, installs per-test mocks, and dynamically imports getApiBaseUrl.
// This is necessary because getApiBaseUrl reads `env` and `browser` at call time from
// module-level imports — vi.resetModules() forces a fresh evaluation of those imports.
async function loadWith(opts: {
	publicApiBaseUrl?: string;
	browser?: boolean;
	hostname?: string;
	port?: string;
	protocol?: string;
}): Promise<string> {
	vi.resetModules();

	vi.doMock('$env/dynamic/public', () => ({
		env: { PUBLIC_API_BASE_URL: opts.publicApiBaseUrl ?? '' }
	}));

	vi.doMock('$app/environment', () => ({
		browser: opts.browser ?? false
	}));

	Object.defineProperty(window, 'location', {
		value: {
			hostname: opts.hostname ?? 'localhost',
			port: opts.port ?? '',
			protocol: opts.protocol ?? 'https:'
		},
		writable: true
	});

	const { getApiBaseUrl } = await import('./client');
	return getApiBaseUrl();
}

describe('getApiBaseUrl', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns PUBLIC_API_BASE_URL when env var is set', async () => {
		const url = await loadWith({ publicApiBaseUrl: 'https://custom.api.example.com' });
		expect(url).toBe('https://custom.api.example.com');
	});

	it('returns protocol+hostname for a production domain (no port)', async () => {
		const url = await loadWith({
			browser: true,
			hostname: 'gwtm.science',
			port: '',
			protocol: 'https:'
		});
		expect(url).toBe('https://gwtm.science');
	});

	it('appends non-standard port for production domain', async () => {
		const url = await loadWith({
			browser: true,
			hostname: 'staging.gwtm.science',
			port: '8443',
			protocol: 'https:'
		});
		expect(url).toBe('https://staging.gwtm.science:8443');
	});

	it('omits port 80 for production domain', async () => {
		const url = await loadWith({
			browser: true,
			hostname: 'gwtm.science',
			port: '80',
			protocol: 'http:'
		});
		expect(url).toBe('http://gwtm.science');
	});

	it('omits port 443 for production domain', async () => {
		const url = await loadWith({
			browser: true,
			hostname: 'gwtm.science',
			port: '443',
			protocol: 'https:'
		});
		expect(url).toBe('https://gwtm.science');
	});

	it('returns empty string for localhost:3000 (proxy mode)', async () => {
		const url = await loadWith({ browser: true, hostname: 'localhost', port: '3000' });
		expect(url).toBe('');
	});

	it('does not treat 127.0.0.1 as a production domain', async () => {
		const url = await loadWith({ browser: true, hostname: '127.0.0.1', port: '8000' });
		expect(url).not.toMatch(/^https?:\/\/127\.0\.0\.1.*\/\//);
		expect(url).toBe('http://localhost:8000');
	});

	it('does not treat ::1 as a production domain', async () => {
		const url = await loadWith({ browser: true, hostname: '::1', port: '' });
		expect(url).toBe('http://localhost:8000');
	});

	it('falls back to http://localhost:8000 outside the browser', async () => {
		const url = await loadWith({ browser: false });
		expect(url).toBe('http://localhost:8000');
	});
});
