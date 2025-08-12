import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { api } from '$lib/api';
import { errorHandler } from '$lib/utils/errorHandling';

// Define the User interface based on the FastAPI response
interface User {
	id: number;
	email: string;
	username: string;
	firstname: string;
	lastname: string;
	verified?: boolean; // Optional during Flask/FastAPI transition
	api_token?: string;
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

	const login = async (
		username: string,
		password: string,
		rememberMe = false
	): Promise<AuthResult> => {
		update((state) => ({ ...state, loading: true }));
		try {
			const response = await api.auth.login(username, password, rememberMe);

			if (response.data && response.data.access_token) {
				const { access_token: token, user } = response.data;

				// Store the JWT token
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
				throw new Error('Login response did not contain an access token.');
			}
		} catch (err) {
			console.error('Login failed:', err);
			const errorMessage =
				(err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
				'Invalid credentials. Please try again.';
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

	const logout = async () => {
		try {
			// Call the logout endpoint (optional for JWT)
			await api.auth.logout();
		} catch (error) {
			// Ignore logout endpoint errors
			console.warn('Logout endpoint error:', error);
		}

		// Clear local storage and state
		api.auth.clearApiToken();
		set({
			isAuthenticated: false,
			user: null,
			token: null,
			loading: false
		});
		errorHandler.showToast('You have been logged out.', { type: 'info' });
		goto('/'); // Redirect to home or login page
	};

	const register = async (userData: {
		email: string;
		password: string;
		username: string;
		first_name?: string;
		last_name?: string;
	}): Promise<AuthResult> => {
		update((state) => ({ ...state, loading: true }));
		try {
			const response = await api.auth.register(userData);

			// Show success message based on response
			const successMessage =
				response.data?.message ||
				'Registration successful! Please check your email for verification.';

			errorHandler.showToast(successMessage, {
				type: 'info',
				duration: 8000 // Longer duration for important verification message
			});

			update((state) => ({ ...state, loading: false }));
			return { success: true };
		} catch (err) {
			console.error('Registration failed:', err);

			// Enhanced error handling for better user experience
			let errorMessage = 'Registration failed. Please try again.';

			if (err && typeof err === 'object' && 'response' in err) {
				const response = err.response as any;

				// Handle validation errors from FastAPI
				if (response?.data?.errors && Array.isArray(response.data.errors)) {
					const errors = response.data.errors.map((error: any) => error.message).join(', ');
					errorMessage = errors;
				} else if (response?.data?.detail) {
					// Handle single error detail
					if (Array.isArray(response.data.detail)) {
						// Pydantic validation errors format
						const validationErrors = response.data.detail
							.map((error: any) => `${error.loc?.[1] || error.loc?.[0] || 'Field'}: ${error.msg}`)
							.join(', ');
						errorMessage = validationErrors;
					} else if (typeof response.data.detail === 'string') {
						errorMessage = response.data.detail;
					}
				} else if (response?.status === 400) {
					errorMessage = 'Please check your information and try again.';
				} else if (response?.status === 409) {
					errorMessage = 'An account with this email or username already exists.';
				} else if (response?.status >= 500) {
					errorMessage = 'Server error. Please try again later.';
				}
			}

			errorHandler.showToast(errorMessage, { type: 'error', duration: 6000 });
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
