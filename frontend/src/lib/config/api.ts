/**
 * @fileoverview API configuration for different environments
 * @description Handles API endpoint configuration for development, testing, and production
 * @category Configuration
 * @version 1.0.0
 * @author GWTM Team
 * @since 2024-01-25
 */

// Environment-aware API configuration
interface ApiConfig {
	baseUrl: string;
	fastApiUrl: string;
	flaskUrl: string;
}

function getApiConfig(): ApiConfig {
	// Check if we're running in browser environment
	if (typeof window === 'undefined') {
		// Server-side rendering - use defaults
		return {
			baseUrl: '/api/v1',
			fastApiUrl: 'http://fastapi-backend:8000',
			flaskUrl: 'http://flask-backend:8080'
		};
	}

	// Browser environment - check for runtime configuration
	const hostname = window.location.hostname;
	const port = window.location.port;

	// Production or Kubernetes environment detection
	if (hostname === 'gwtm.local' || hostname.includes('.')) {
		// Production/staging environment
		return {
			baseUrl: '/api/v1',
			fastApiUrl: '/api/v1', // Use relative URLs in production
			flaskUrl: '/flask'
		};
	}

	// Development environment (localhost)
	if (hostname === 'localhost' || hostname === '127.0.0.1') {
		// In development, check if we have a proxy setup
		const currentPort = port || '3000';

		if (currentPort === '3000') {
			// Frontend dev server - API calls should be proxied or go to different ports
			return {
				baseUrl: '/api/v1', // Will be proxied by Vite
				fastApiUrl: '/api/v1', // Proxied to FastAPI
				flaskUrl: 'http://localhost:8080' // Direct to Flask
			};
		}
	}

	// Fallback configuration
	return {
		baseUrl: '/api/v1',
		fastApiUrl: '/api/v1',
		flaskUrl: '/flask'
	};
}

// Export the configuration
export const apiConfig = getApiConfig();

// Helper functions for building URLs
export function buildApiUrl(endpoint: string): string {
	// Remove leading slash if present
	const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

	// Use relative URLs that will be proxied or routed appropriately
	return `/${cleanEndpoint}`;
}

export function buildFastApiUrl(endpoint: string): string {
	const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
	return `/${cleanEndpoint}`;
}

export function buildFlaskUrl(endpoint: string): string {
	const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
	return `/${cleanEndpoint}`;
}

// Export commonly used URLs
export const API_ENDPOINTS = {
	// FastAPI endpoints
	login: '/api/v1/auth/login',
	logout: '/api/v1/auth/logout',
	queryAlerts: '/api/v1/query_alerts',
	instruments: '/api/v1/instruments',
	pointings: '/api/v1/pointings',
	doiAuthorGroups: '/api/v1/doi_author_groups',

	// UI endpoints (no API prefix)
	pointingFromId: '/ajax_pointingfromid',

	// Admin endpoints
	adminUsers: '/admin/users'
} as const;
