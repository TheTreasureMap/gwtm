import client from '../client';
import { browser } from '$app/environment';

export const authService = {
	login: async (username: string, password: string, rememberMe = false): Promise<any> => {
		const response = await client.post('/api/v1/auth/login', {
			username,
			password,
			remember_me: rememberMe
		});
		return response;
	},

	register: async (userData: {
		email: string;
		password: string;
		username: string;
		first_name?: string;
		last_name?: string;
	}): Promise<any> => {
		const response = await client.post('/api/v1/register', userData);
		return response;
	},

	logout: async (): Promise<any> => {
		// Call the logout endpoint (optional in JWT systems)
		try {
			const response = await client.post('/api/v1/auth/logout');
			return response;
		} catch (error) {
			// Logout endpoint might fail if token is invalid, but we still want to clear local storage
			console.warn('Logout endpoint failed:', error);
		}
	},

	getCurrentUser: async (): Promise<any> => {
		const response = await client.get('/api/v1/auth/me');
		return response;
	},

	setApiToken: (token: string): void => {
		if (browser) {
			localStorage.setItem('access_token', token);
		}
	},

	getApiToken: (): string | null => {
		return browser ? localStorage.getItem('access_token') : null;
	},

	clearApiToken: (): void => {
		if (browser) {
			localStorage.removeItem('access_token');
			localStorage.removeItem('user');
		}
	},

	isAuthenticated: (): boolean => {
		return !!authService.getApiToken();
	}
};
