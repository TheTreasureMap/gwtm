import axios, { type AxiosInstance } from 'axios';
import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

const defaultUrl = 'http://localhost:8000';
const baseURL = env.PUBLIC_API_BASE_URL || defaultUrl;

const client: AxiosInstance = axios.create({
    baseURL: baseURL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor - add API token (unless explicitly disabled)
client.interceptors.request.use(
    (config) => {
        // Skip auth if explicitly disabled via custom header
        if (!config.headers['skip-auth']) {
            const token = browser ? localStorage.getItem('api_token') : null;
            if (token) {
                config.headers['api_token'] = token;
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

// Response interceptor
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
    (error) => {
        console.error('GWTM API Error:', error);
        if (error.response?.status === 401) {
            if (browser) {
                localStorage.removeItem('api_token');
                // Redirect to login or show auth error
            }
        }
        return Promise.reject(error);
    }
);

export default client;
