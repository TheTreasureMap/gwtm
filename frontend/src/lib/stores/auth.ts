import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { api } from '$lib/api';
import { errorHandler } from '$lib/utils/errorHandling';

// Define the User interface based on the previous file
interface User {
	id: number;
	email: string;
	username: string;
	first_name?: string;
	last_name?: string;
}

// Define the state for our auth store
interface AuthState {
	isAuthenticated: boolean;
	user: User | null;
	loading: boolean;
	token: string | null;
}

// Define result types for auth operations
interface AuthResult {
	success: boolean;
	error?: string;
	user?: User;
}

function createAuthStore() {
	const { subscribe, update, set } = writable<AuthState>({
		isAuthenticated: false,
		user: null,
		loading: true, // Start loading until init is complete
		token: null
	});

	// This function will be called when the app loads
	const init = () => {
		if (!browser) {
			update((state) => ({ ...state, loading: false }));
			return;
		}

		const token = api.auth.getApiToken();
		const userStr = localStorage.getItem('user');

		if (token && userStr) {
			try {
				const user = JSON.parse(userStr);
				set({
					isAuthenticated: true,
					user: user,
					token: token,
					loading: false
				});
			} catch (e) {
				// If parsing fails, clear everything
				api.auth.clearApiToken();
				localStorage.removeItem('user');
				set({ isAuthenticated: false, user: null, token: null, loading: false });
			}
		} else {
			// Not authenticated
			set({ isAuthenticated: false, user: null, token: null, loading: false });
		}
	};

	const login = async (email: string, password: string): Promise<AuthResult> => {
		update((state) => ({ ...state, loading: true }));
		try {
			const response = await api.auth.login(email, password);
			if (response.data && response.data.api_token) {
				const { api_token: token, user } = response.data;

				api.auth.setApiToken(token);
				if (browser) {
					localStorage.setItem('user', JSON.stringify(user));
				}

				set({
					isAuthenticated: true,
					user: user,
					token: token,
					loading: false
				});

				errorHandler.showToast('Login successful!', { type: 'info', duration: 3000 });
				goto('/alerts'); // Redirect to a protected route
				return { success: true, user };
			} else {
				throw new Error('Login response did not contain an API token.');
			}
		} catch (err) {
			console.error('Login failed:', err);
			const errorMessage =
				(err as any).response?.data?.detail || 'Invalid credentials. Please try again.';
			errorHandler.showToast(errorMessage, { type: 'error' });
			update((state) => ({
				...state,
				isAuthenticated: false,
				user: null,
				token: null,
				loading: false
			}));
			return { success: false, error: errorMessage };
		}
	};

	const logout = () => {
		api.auth.clearApiToken();
		if (browser) {
			localStorage.removeItem('user');
		}
		set({
			isAuthenticated: false,
			user: null,
			token: null,
			loading: false
		});
		errorHandler.showToast('You have been logged out.', { type: 'info' });
		goto('/'); // Redirect to home or login page
	};

	const register = async (userData: any): Promise<AuthResult> => {
		update((state) => ({ ...state, loading: true }));
		try {
			await api.auth.register(userData);
			errorHandler.showToast('Registration successful! Please check your email for verification.', {
				type: 'info',
				duration: 5000
			});
			goto('/login');
			update((state) => ({ ...state, loading: false }));
			return { success: true };
		} catch (err) {
			console.error('Registration failed:', err);
			const errorMessage =
				(err as any).response?.data?.detail || 'Registration failed. Please try again.';
			errorHandler.showToast(errorMessage, { type: 'error' });
			update((state) => ({ ...state, loading: false }));
			return { success: false, error: errorMessage };
		}
	};

	return {
		subscribe,
		init,
		login,
		logout,
		register
	};
}

export const auth = createAuthStore();

// Initialize on load
auth.init();
