import client from '../client';
import { browser } from '$app/environment';
import type {
	CaptchaConfigResponse,
	LoginResponse,
	MessageResponse,
	RegisterResponse,
	UserResponse
} from '../types/api-responses';
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
		turnstile_token?: string;
	}): Promise<AxiosResponse<RegisterResponse>> => {
		const response = await client.post<RegisterResponse>('/api/v1/register', userData);
		return response;
	},

	getCaptchaConfig: async (): Promise<AxiosResponse<CaptchaConfigResponse>> => {
		const response = await client.get<CaptchaConfigResponse>('/api/v1/auth/captcha-config');
		return response;
	},

	forgotPassword: async (
		email: string,
		turnstileToken?: string
	): Promise<AxiosResponse<MessageResponse>> => {
		const response = await client.post<MessageResponse>('/api/v1/auth/forgot-password', {
			email,
			turnstile_token: turnstileToken
		});
		return response;
	},

	resetPassword: async (
		token: string,
		password: string,
		rotateApiToken = false
	): Promise<AxiosResponse<MessageResponse>> => {
		const response = await client.post<MessageResponse>('/api/v1/auth/reset-password', {
			token,
			password,
			rotate_api_token: rotateApiToken
		});
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
