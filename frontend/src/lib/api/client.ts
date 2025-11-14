import axios, { type AxiosInstance } from 'axios';
import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

// Environment-aware API URL configuration
function getApiBaseUrl(): string {
	// Check environment variable first
	if (env.PUBLIC_API_BASE_URL) {
		return env.PUBLIC_API_BASE_URL;
	}

	// In browser, detect environment from hostname
	if (browser) {
		const hostname = window.location.hostname;
		const protocol = window.location.protocol;
		const port = window.location.port;

		// Production/staging environment (domain name or non-localhost)
		if (hostname === 'gwtm.local' || hostname.includes('.') || !hostname.includes('localhost')) {
			return `${protocol}//${hostname}${port && port !== '80' && port !== '443' ? ':' + port : ''}`;
		}

		// Development with skaffold (frontend on localhost:3000)
		if (hostname === 'localhost' && port === '3000') {
			// First try to use the proxy (empty base URL)
			// If that fails, it will fall back to direct connection
			return '';
		}
	}

	// Fallback: try direct connection to FastAPI
	return 'http://localhost:8000';
}

const baseURL = getApiBaseUrl();

const client: AxiosInstance = axios.create({
	baseURL: baseURL,
	timeout: 30000,
	headers: {
		'Content-Type': 'application/json'
	}
});

// Request interceptor - add JWT token (unless explicitly disabled)
client.interceptors.request.use(
	(config) => {
		// Skip auth if explicitly disabled via custom header
		if (!config.headers['skip-auth']) {
			const token = browser ? localStorage.getItem('access_token') : null;
			if (token) {
				config.headers['Authorization'] = `Bearer ${token}`;
			}
		}

		// Remove the skip-auth header before sending request
		delete config.headers['skip-auth'];

		// Log requests in development
		if (browser && import.meta.env.DEV) {
			console.log(`GWTM API Request: ${config.method?.toUpperCase()} ${config.url}`, {
				params: config.params,
				data: config.data
			});
		}

		return config;
	},
	(error) => {
		console.error('Request error:', error);
		return Promise.reject(error);
	}
);

// Response interceptor with fallback support
client.interceptors.response.use(
	(response) => {
		if (browser && import.meta.env.DEV) {
			console.log(
				`GWTM API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`,
				response.data
			);
		}
		return response;
	},
	async (error) => {
		console.error('GWTM API Error:', error);

		// If we're getting connection refused and using proxy, try direct connection
		if (error.code === 'ECONNREFUSED' || error.message?.includes('ECONNREFUSED')) {
			if (baseURL === '' && browser) {
				console.warn('Proxy failed, attempting direct connection to FastAPI...');

				// Create a new client with direct connection
				const fallbackClient = axios.create({
					baseURL: 'http://localhost:8000',
					timeout: 30000,
					headers: {
						'Content-Type': 'application/json'
					}
				});

				// Add auth header if available
				const token = localStorage.getItem('access_token');
				if (token) {
					fallbackClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
				}

				// Retry the request with direct connection
				try {
					const originalConfig = error.config;
					const retryResponse = await fallbackClient.request(originalConfig);
					console.log('Direct connection succeeded');
					return retryResponse;
				} catch (fallbackError) {
					console.error('Direct connection also failed:', fallbackError);
				}
			}
		}

		if (error.response?.status === 401) {
			if (browser) {
				localStorage.removeItem('access_token');
				// Redirect to login or show auth error
			}
		}
		return Promise.reject(error);
	}
);

export default client;
