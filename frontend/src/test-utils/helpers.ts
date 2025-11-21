/**
 * Test utility functions and helpers
 */

import { vi, beforeEach, afterEach, expect } from 'vitest';

/**
 * Generate test data for validation tests
 */
export const testData = {
	validEmails: [
		'test@example.com',
		'user.name@domain.com',
		'test+tag@example.org',
		'user123@test-domain.co.uk'
	],

	invalidEmails: [
		'not-an-email',
		'@example.com',
		'test@',
		'test@.com',
		'test..test@example.com',
		'test@example',
		''
	],

	validPasswords: ['Password123!', 'MySecure1', 'Test123456', 'ComplexP@ss1'],

	invalidPasswords: [
		'short',
		'onlylowercase',
		'ONLYUPPERCASE',
		'NoNumbers!',
		'12345678' // only numbers
	],

	coordinates: {
		valid: {
			ra: [0, 180, 360, 45.5, 123.456],
			dec: [-90, -45, 0, 45, 90, -23.5, 67.8]
		},
		invalid: {
			ra: [-1, 361, -180, 400],
			dec: [-91, 91, -180, 180]
		}
	},

	dates: {
		validISOStrings: [
			'2024-01-01T00:00:00.000Z',
			'2023-12-25T15:30:00.000Z',
			'2024-03-15T12:00:00.000Z'
		],
		invalidDates: [
			'not-a-date',
			'2024-13-01', // invalid month
			'2024-02-30', // invalid day
			''
		]
	}
};

/**
 * Create mock validation context
 */
export function createMockContext(overrides: Record<string, unknown> = {}) {
	return {
		email: 'test@example.com',
		password: 'TestPassword123',
		confirmPassword: 'TestPassword123',
		username: 'testuser',
		...overrides
	};
}

/**
 * Mock console methods for cleaner test output
 */
export function mockConsole() {
	const originalConsole = { ...console };

	beforeEach(() => {
		vi.spyOn(console, 'log').mockImplementation(() => {});
		vi.spyOn(console, 'error').mockImplementation(() => {});
		vi.spyOn(console, 'warn').mockImplementation(() => {});
		vi.spyOn(console, 'info').mockImplementation(() => {});
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	return originalConsole;
}

/**
 * Create mock Date for consistent time-based testing
 */
export function mockDate(dateString: string = '2024-01-01T12:00:00.000Z') {
	const mockDate = new Date(dateString);
	vi.useFakeTimers();
	vi.setSystemTime(mockDate);

	return {
		mockDate,
		restore: () => {
			vi.useRealTimers();
		}
	};
}

/**
 * Create mock fetch responses for API-related tests
 */
export function createMockFetchResponse(data: unknown, status = 200, ok = true) {
	return Promise.resolve({
		ok,
		status,
		json: () => Promise.resolve(data),
		text: () => Promise.resolve(JSON.stringify(data))
	} as Response);
}

/**
 * Test error objects for error handling tests
 */
export const testErrors = {
	networkError: new Error('Network Error'),
	apiError: {
		response: {
			status: 422,
			data: {
				detail: [
					{ loc: ['field1'], msg: 'Field is required' },
					{ loc: ['field2'], msg: 'Invalid format' }
				]
			},
			config: {
				url: '/api/test',
				method: 'POST'
			}
		}
	},
	simpleApiError: {
		response: {
			status: 500,
			data: { message: 'Internal Server Error' },
			config: { url: '/api/test', method: 'GET' }
		}
	},
	authError: {
		response: {
			status: 401,
			data: { detail: 'Authentication required' }
		}
	}
};

/**
 * Helper to test validation function results
 */
export function expectValidationResult(
	result: { isValid: boolean; errors: string[]; warnings?: string[] },
	expectedValid: boolean,
	expectedErrors: string[] = [],
	expectedWarnings: string[] = []
) {
	expect(result.isValid).toBe(expectedValid);
	expect(result.errors).toEqual(expectedErrors);
	if (expectedWarnings.length > 0) {
		expect(result.warnings).toEqual(expectedWarnings);
	}
}

/**
 * Helper to test astronomical calculations with tolerance
 */
export function expectApproximatelyEqual(actual: number, expected: number, tolerance = 0.001) {
	expect(Math.abs(actual - expected)).toBeLessThan(tolerance);
}

/**
 * Create test user data
 */
export function createTestUser(overrides: Record<string, unknown> = {}) {
	return {
		id: '123',
		email: 'test@example.com',
		username: 'testuser',
		firstName: 'Test',
		lastName: 'User',
		...overrides
	};
}

/**
 * Create test instrument data
 */
export function createTestInstrument(overrides: Record<string, unknown> = {}) {
	return {
		id: 1,
		instrument_name: 'Test Telescope',
		nickname: 'TT-1',
		instrument_type: 1,
		...overrides
	};
}

/**
 * Create test pointing data
 */
export function createTestPointing(overrides: Record<string, unknown> = {}) {
	return {
		id: 1,
		ra: 180.0,
		dec: 0.0,
		depth: 20.5,
		time: '2024-01-01T12:00:00.000Z',
		instrument_id: 1,
		...overrides
	};
}
