import client from '../client';
import { browser } from '$app/environment';

export const authService = {
	login: async (email: string, password: string): Promise<any> => {
		const response = await client.post('/api/v1/login', {
			email,
			password
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

	setApiToken: (token: string): void => {
		if (browser) {
			localStorage.setItem('api_token', token);
		}
	},

	getApiToken: (): string | null => {
		return browser ? localStorage.getItem('api_token') : null;
	},

	clearApiToken: (): void => {
		if (browser) {
			localStorage.removeItem('api_token');
		}
	},

	isAuthenticated: (): boolean => {
		return !!authService.getApiToken();
	}
};
