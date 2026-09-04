import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { goto } from '$app/navigation';

const authApi = {
	getApiToken: vi.fn(),
	setApiToken: vi.fn(),
	clearApiToken: vi.fn(),
	login: vi.fn(),
	logout: vi.fn(),
	register: vi.fn()
};

const showToast = vi.fn();

vi.mock('$lib/api', () => ({ api: { auth: authApi } }));
vi.mock('$lib/utils/errorHandling', () => ({ errorHandler: { showToast } }));

/**
 * The module exports a singleton and calls init() on import, so each test needs
 * a fresh copy rather than a shared one carrying state between cases.
 */
async function loadAuth() {
	vi.resetModules();
	const { auth } = await import('../auth');
	return auth;
}

const user = { id: 1, username: 'ada', email: 'ada@example.com' };

/** An axios-shaped rejection, which is what the store's error paths expect. */
const httpError = (response: unknown) => Object.assign(new Error('request failed'), { response });

beforeEach(() => {
	localStorage.clear();
	vi.clearAllMocks();
	authApi.getApiToken.mockReturnValue(null);
});

describe('auth store', () => {
	describe('init', () => {
		it('restores a session when a token and user are both stored', async () => {
			authApi.getApiToken.mockReturnValue('stored-token');
			localStorage.setItem('user', JSON.stringify(user));

			const auth = await loadAuth();

			expect(get(auth)).toEqual({
				isAuthenticated: true,
				user,
				token: 'stored-token',
				loading: false
			});
		});

		it('stays logged out when there is no token', async () => {
			const auth = await loadAuth();

			expect(get(auth)).toEqual({
				isAuthenticated: false,
				user: null,
				token: null,
				loading: false
			});
		});

		it('stays logged out when a token exists but no user record does', async () => {
			authApi.getApiToken.mockReturnValue('stored-token');

			const auth = await loadAuth();

			expect(get(auth).isAuthenticated).toBe(false);
		});

		it('discards a corrupt stored user and clears the token', async () => {
			authApi.getApiToken.mockReturnValue('stored-token');
			localStorage.setItem('user', 'not json');

			const auth = await loadAuth();

			expect(get(auth).isAuthenticated).toBe(false);
			expect(authApi.clearApiToken).toHaveBeenCalled();
			expect(localStorage.getItem('user')).toBeNull();
		});

		it('always finishes loading', async () => {
			const auth = await loadAuth();
			expect(get(auth).loading).toBe(false);
		});
	});

	describe('login', () => {
		it('stores the token, persists the user and authenticates', async () => {
			authApi.login.mockResolvedValue({ data: { access_token: 'jwt-token', user } });
			const auth = await loadAuth();

			const result = await auth.login('ada', 'secret');

			expect(result).toEqual({ success: true, user });
			expect(authApi.setApiToken).toHaveBeenCalledWith('jwt-token');
			expect(JSON.parse(localStorage.getItem('user') as string)).toEqual(user);
			expect(get(auth)).toEqual({
				isAuthenticated: true,
				user,
				token: 'jwt-token',
				loading: false
			});
		});

		it('passes rememberMe through to the API', async () => {
			authApi.login.mockResolvedValue({ data: { access_token: 'jwt-token', user } });
			const auth = await loadAuth();

			await auth.login('ada', 'secret', true);

			expect(authApi.login).toHaveBeenCalledWith('ada', 'secret', true);
		});

		it('redirects to the alerts page on success', async () => {
			authApi.login.mockResolvedValue({ data: { access_token: 'jwt-token', user } });
			const auth = await loadAuth();

			await auth.login('ada', 'secret');

			expect(goto).toHaveBeenCalledWith('/alerts');
		});

		it('treats a response with no access token as a failure', async () => {
			authApi.login.mockResolvedValue({ data: {} });
			const auth = await loadAuth();

			const result = await auth.login('ada', 'secret');

			expect(result.success).toBe(false);
			expect(get(auth).isAuthenticated).toBe(false);
			expect(goto).not.toHaveBeenCalled();
		});

		it('surfaces the server detail when the request fails', async () => {
			authApi.login.mockRejectedValue(httpError({ data: { detail: 'Account not verified' } }));
			const auth = await loadAuth();

			const result = await auth.login('ada', 'secret');

			expect(result).toEqual({ success: false, error: 'Account not verified' });
			expect(showToast).toHaveBeenCalledWith('Account not verified', { type: 'error' });
		});

		it('falls back to a generic message when the server gives no detail', async () => {
			authApi.login.mockRejectedValue(new Error('network down'));
			const auth = await loadAuth();

			const result = await auth.login('ada', 'secret');

			expect(result.error).toBe('Invalid credentials. Please try again.');
		});

		it('clears any previous session on failure', async () => {
			authApi.getApiToken.mockReturnValue('stored-token');
			localStorage.setItem('user', JSON.stringify(user));
			const auth = await loadAuth();
			expect(get(auth).isAuthenticated).toBe(true);

			authApi.login.mockRejectedValue(new Error('nope'));
			await auth.login('ada', 'wrong');

			expect(get(auth)).toMatchObject({ isAuthenticated: false, user: null, token: null });
		});
	});

	describe('logout', () => {
		it('clears the token and the session', async () => {
			authApi.logout.mockResolvedValue({});
			const auth = await loadAuth();

			await auth.logout();

			expect(authApi.clearApiToken).toHaveBeenCalled();
			expect(get(auth)).toEqual({
				isAuthenticated: false,
				user: null,
				token: null,
				loading: false
			});
		});

		it('redirects home', async () => {
			authApi.logout.mockResolvedValue({});
			const auth = await loadAuth();

			await auth.logout();

			expect(goto).toHaveBeenCalledWith('/');
		});

		it('still logs out locally when the logout endpoint fails', async () => {
			authApi.logout.mockRejectedValue(new Error('endpoint gone'));
			const auth = await loadAuth();

			await auth.logout();

			expect(authApi.clearApiToken).toHaveBeenCalled();
			expect(get(auth).isAuthenticated).toBe(false);
		});
	});

	describe('register', () => {
		const details = { email: 'ada@example.com', password: 'secret', username: 'ada' };

		it('reports success and shows the server message', async () => {
			authApi.register.mockResolvedValue({ data: { message: 'Check your email' } });
			const auth = await loadAuth();

			const result = await auth.register(details);

			expect(result).toEqual({ success: true });
			expect(showToast).toHaveBeenCalledWith('Check your email', expect.objectContaining({}));
			expect(get(auth).loading).toBe(false);
		});

		it('falls back to a default success message', async () => {
			authApi.register.mockResolvedValue({ data: {} });
			const auth = await loadAuth();

			await auth.register(details);

			expect(showToast).toHaveBeenCalledWith(
				'Registration successful! Please check your email for verification.',
				expect.objectContaining({})
			);
		});

		it('does not authenticate the user', async () => {
			authApi.register.mockResolvedValue({ data: {} });
			const auth = await loadAuth();

			await auth.register(details);

			expect(get(auth).isAuthenticated).toBe(false);
		});

		it('joins a list of field errors', async () => {
			authApi.register.mockRejectedValue(
				httpError({ data: { errors: [{ message: 'email taken' }, { message: 'weak password' }] } })
			);
			const auth = await loadAuth();

			const result = await auth.register(details);

			expect(result.error).toBe('email taken, weak password');
		});

		it('formats pydantic validation errors with their field names', async () => {
			authApi.register.mockRejectedValue(
				httpError({
					data: {
						detail: [
							{ loc: ['body', 'email'], msg: 'invalid address' },
							{ loc: ['body', 'password'], msg: 'too short' }
						]
					}
				})
			);
			const auth = await loadAuth();

			const result = await auth.register(details);

			expect(result.error).toBe('email: invalid address, password: too short');
		});

		it('uses a string detail as-is', async () => {
			authApi.register.mockRejectedValue(httpError({ data: { detail: 'username reserved' } }));
			const auth = await loadAuth();

			expect((await auth.register(details)).error).toBe('username reserved');
		});

		it('maps a 400 to a check-your-details message', async () => {
			authApi.register.mockRejectedValue(httpError({ status: 400, data: {} }));
			const auth = await loadAuth();

			expect((await auth.register(details)).error).toBe(
				'Please check your information and try again.'
			);
		});

		it('maps a 409 to a duplicate-account message', async () => {
			authApi.register.mockRejectedValue(httpError({ status: 409, data: {} }));
			const auth = await loadAuth();

			expect((await auth.register(details)).error).toBe(
				'An account with this email or username already exists.'
			);
		});

		it('maps a 500 to a server-error message', async () => {
			authApi.register.mockRejectedValue(httpError({ status: 503, data: {} }));
			const auth = await loadAuth();

			expect((await auth.register(details)).error).toBe('Server error. Please try again later.');
		});

		it('falls back to a generic message for a non-HTTP failure', async () => {
			authApi.register.mockRejectedValue(new Error('socket hang up'));
			const auth = await loadAuth();

			expect((await auth.register(details)).error).toBe('Registration failed. Please try again.');
		});

		it('clears the loading flag after a failure', async () => {
			authApi.register.mockRejectedValue(new Error('nope'));
			const auth = await loadAuth();

			await auth.register(details);

			expect(get(auth).loading).toBe(false);
		});
	});
});
