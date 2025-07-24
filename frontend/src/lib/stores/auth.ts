import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { gwtmApi } from '$lib/api';

interface User {
	id: number;
	email: string;
	username: string;
	first_name?: string;
	last_name?: string;
}

interface AuthState {
	user: User | null;
	token: string | null;
	isAuthenticated: boolean;
	loading: boolean;
}

const initialState: AuthState = {
	user: null,
	token: null,
	isAuthenticated: false,
	loading: false
};

// Create the auth store
export const auth = writable<AuthState>(initialState);

// Helper functions
export const authActions = {
	// Initialize auth state from localStorage
	init() {
		if (!browser) return;

		const token = localStorage.getItem('jwt_token');
		const userStr = localStorage.getItem('user');

		if (token && userStr) {
			try {
				const user = JSON.parse(userStr);
				auth.set({
					user,
					token,
					isAuthenticated: true,
					loading: false
				});

				// Set default authorization header
				gwtmApi.setApiToken(token);
			} catch (e) {
				// Clear invalid data
				localStorage.removeItem('jwt_token');
				localStorage.removeItem('user');
			}
		}
	},

	// Login function
	async login(email: string, password: string) {
		auth.update((state) => ({ ...state, loading: true }));

		try {
			const response = await gwtmApi.login(email, password);
			const { access_token, user } = response.data;

			// Store in localStorage
			if (browser) {
				localStorage.setItem('jwt_token', access_token);
				localStorage.setItem('user', JSON.stringify(user));
			}

			// Set authorization header
			gwtmApi.setApiToken(access_token);

			// Update store
			auth.set({
				user,
				token: access_token,
				isAuthenticated: true,
				loading: false
			});

			return { success: true };
		} catch (error: any) {
			auth.update((state) => ({ ...state, loading: false }));
			return {
				success: false,
				error: error.response?.data?.detail || 'Login failed'
			};
		}
	},

	// Logout function
	logout() {
		if (browser) {
			localStorage.removeItem('jwt_token');
			localStorage.removeItem('user');
		}

		// Clear authorization header
		gwtmApi.clearApiToken();

		// Reset store
		auth.set(initialState);

		// Redirect to login
		goto('/login');
	},

	// Register function
	async register(userData: {
		email: string;
		password: string;
		username: string;
		first_name?: string;
		last_name?: string;
	}) {
		auth.update((state) => ({ ...state, loading: true }));

		try {
			const response = await gwtmApi.register(userData);
			auth.update((state) => ({ ...state, loading: false }));
			return { success: true, data: response.data };
		} catch (error: any) {
			auth.update((state) => ({ ...state, loading: false }));
			return {
				success: false,
				error: error.response?.data?.detail || 'Registration failed'
			};
		}
	}
};

// Initialize auth state when the module loads
if (browser) {
	authActions.init();
}
