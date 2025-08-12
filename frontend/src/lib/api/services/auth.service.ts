import client from '../client';
import { browser } from '$app/environment';
import type { LoginResponse, RegisterResponse, UserResponse } from '../types/api-responses';
import type { AxiosResponse } from 'axios';

export const authService = {
	login: async (
		username: string,
		password: string,
		rememberMe = false
	): Promise<AxiosResponse<LoginResponse>> => {
		const response = await client.post<LoginResponse>('/api/v1/auth/login', {
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
	}): Promise<AxiosResponse<RegisterResponse>> => {
		const response = await client.post<RegisterResponse>('/api/v1/register', userData);
		return response;
	},

	logout: async (): Promise<AxiosResponse<{ success: boolean; message: string }> | undefined> => {
		// Call the logout endpoint (optional in JWT systems)
		try {
			const response = await client.post<{ success: boolean; message: string }>(
				'/api/v1/auth/logout'
			);
			return response;
		} catch (error) {
			// Logout endpoint might fail if token is invalid, but we still want to clear local storage
			console.warn('Logout endpoint failed:', error);
			return undefined;
		}
	},

	getCurrentUser: async (): Promise<AxiosResponse<UserResponse>> => {
		const response = await client.get<UserResponse>('/api/v1/auth/me');
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
