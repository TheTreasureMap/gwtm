import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { get } from 'svelte/store';
import {
	errorHandler,
	errorLogger,
	validation,
	validateForm,
	globalErrors,
	type AppError,
	type ErrorToastOptions
} from '../errorHandling';
import { testErrors, mockConsole } from '../../../test-utils/helpers';

describe('Error Handling Utilities', () => {
	beforeEach(() => {
		// Clear the global error store before each test
		globalErrors.set([]);
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('errorHandler', () => {
		describe('showToast', () => {
			it('should add error to global store', () => {
				const errorId = errorHandler.showToast('Test error message');

				const errors = get(globalErrors);
				expect(errors).toHaveLength(1);
				expect(errors[0].message).toBe('Test error message');
				expect(errors[0].id).toBe(errorId);
				expect(errors[0].type).toBe('error'); // default type
			});

			it('should create error with correct default properties', () => {
				const errorId = errorHandler.showToast('Test message');

				const errors = get(globalErrors);
				const error = errors[0];

				expect(error.type).toBe('error');
				expect(error.dismissible).toBe(true);
				expect(error.duration).toBe(5000); // Current implementation uses options.type check, not resolved type
				expect(error.timestamp).toBeInstanceOf(Date);
				expect(typeof error.id).toBe('string');
				expect(error.id).toContain('error_');
			});

			it('should use custom options', () => {
				const options: ErrorToastOptions = {
					type: 'warning',
					duration: 3000,
					dismissible: false,
					context: 'test-context',
					details: { extra: 'data' }
				};

				errorHandler.showToast('Custom message', options);

				const errors = get(globalErrors);
				const error = errors[0];

				expect(error.type).toBe('warning');
				expect(error.duration).toBe(3000);
				expect(error.dismissible).toBe(false);
				expect(error.context).toBe('test-context');
				expect(error.details).toEqual({ extra: 'data' });
			});

			it('should auto-dismiss non-error types by default', () => {
				errorHandler.showToast('Info message', { type: 'info' });

				const errors = get(globalErrors);
				expect(errors[0].duration).toBe(5000);
			});

			it('should not auto-dismiss explicit error type', () => {
				errorHandler.showToast('Error message', { type: 'error' });

				const errors = get(globalErrors);
				expect(errors[0].duration).toBe(0);
				expect(errors[0].type).toBe('error');
			});

			it('should auto-dismiss when duration is set', () => {
				vi.useFakeTimers();

				const errorId = errorHandler.showToast('Auto-dismiss message', { duration: 1000 });

				// Error should be present initially
				expect(get(globalErrors)).toHaveLength(1);

				// Fast-forward time
				vi.advanceTimersByTime(1000);

				// Error should be dismissed
				expect(get(globalErrors)).toHaveLength(0);

				vi.useRealTimers();
			});

			it('should generate unique error IDs', () => {
				const id1 = errorHandler.showToast('Message 1');
				const id2 = errorHandler.showToast('Message 2');
				const id3 = errorHandler.showToast('Message 3');

				expect(id1).not.toBe(id2);
				expect(id2).not.toBe(id3);
				expect(id1).not.toBe(id3);

				// All should start with 'error_'
				expect(id1).toMatch(/^error_\d+_[a-z0-9]+$/);
				expect(id2).toMatch(/^error_\d+_[a-z0-9]+$/);
				expect(id3).toMatch(/^error_\d+_[a-z0-9]+$/);
			});
		});

		describe('dismissError', () => {
			it('should remove specific error from store', () => {
				const id1 = errorHandler.showToast('Error 1');
				const id2 = errorHandler.showToast('Error 2');

				expect(get(globalErrors)).toHaveLength(2);

				errorHandler.dismissError(id1);

				const remainingErrors = get(globalErrors);
				expect(remainingErrors).toHaveLength(1);
				expect(remainingErrors[0].id).toBe(id2);
			});

			it('should handle non-existent error IDs gracefully', () => {
				errorHandler.showToast('Test error');
				expect(get(globalErrors)).toHaveLength(1);

				// Try to dismiss non-existent error
				errorHandler.dismissError('non-existent-id');

				// Original error should still be there
				expect(get(globalErrors)).toHaveLength(1);
			});
		});

		describe('clearAllErrors', () => {
			it('should remove all errors from store', () => {
				errorHandler.showToast('Error 1');
				errorHandler.showToast('Error 2');
				errorHandler.showToast('Error 3');

				expect(get(globalErrors)).toHaveLength(3);

				errorHandler.clearAllErrors();

				expect(get(globalErrors)).toHaveLength(0);
			});
		});

		describe('handleApiError', () => {
			it('should handle axios response errors', () => {
				const message = errorHandler.handleApiError(testErrors.apiError, 'test-context');

				expect(message).toContain('Validation error');
				expect(message).toContain('Field is required');

				const errors = get(globalErrors);
				expect(errors).toHaveLength(1);
				expect(errors[0].context).toBe('test-context');
				expect(errors[0].type).toBe('error');
				expect(errors[0].duration).toBe(0); // Don't auto-dismiss API errors
			});

			it('should handle different HTTP status codes', () => {
				const errors = [
					{ response: { status: 401 }, expected: 'Authentication required' },
					{ response: { status: 403 }, expected: 'Access denied' },
					{ response: { status: 404 }, expected: 'not found' },
					{ response: { status: 500 }, expected: 'Internal server error' }
				];

				errors.forEach(({ response, expected }) => {
					globalErrors.set([]); // Clear between tests
					const message = errorHandler.handleApiError({ response });
					expect(message.toLowerCase()).toContain(expected.toLowerCase());
				});
			});

			it('should parse validation errors correctly', () => {
				const validationError = {
					response: {
						status: 422,
						data: {
							detail: [
								{ loc: ['email'], msg: 'Invalid email format' },
								{ loc: ['password'], msg: 'Password too short' }
							]
						}
					}
				};

				const message = errorHandler.handleApiError(validationError);
				expect(message).toContain('email: Invalid email format');
				expect(message).toContain('password: Password too short');
			});

			it('should handle network errors', () => {
				const networkError = { request: { status: 0 } };
				const message = errorHandler.handleApiError(networkError);

				expect(message).toContain('Network error');
				expect(message).toContain('check your connection');
			});

			it('should handle generic errors', () => {
				const genericError = { message: 'Something went wrong' };
				const message = errorHandler.handleApiError(genericError);

				expect(message).toBe('Something went wrong');
			});

			it('should handle unknown error formats', () => {
				const unknownError = 'string error';
				const message = errorHandler.handleApiError(unknownError);

				expect(message).toBe('An unexpected error occurred');
			});

			it('should extract error details for store', () => {
				errorHandler.handleApiError(testErrors.simpleApiError);

				const errors = get(globalErrors);
				const error = errors[0];

				expect(error.details).toHaveProperty('status', 500);
				expect(error.details).toHaveProperty('url', '/api/test');
				expect(error.details).toHaveProperty('method', 'GET');
				expect(error.details).toHaveProperty('data');
			});
		});

		describe('withErrorHandling', () => {
			it('should return result when operation succeeds', async () => {
				const successfulOperation = () => Promise.resolve('success result');

				const result = await errorHandler.withErrorHandling(successfulOperation);

				expect(result).toBe('success result');
				expect(get(globalErrors)).toHaveLength(0);
			});

			it('should handle errors and return null', async () => {
				const failingOperation = () => Promise.reject(new Error('Operation failed'));

				const result = await errorHandler.withErrorHandling(failingOperation);

				expect(result).toBeNull();
				expect(get(globalErrors)).toHaveLength(1);
			});

			it('should show success toast when configured', async () => {
				const successfulOperation = () => Promise.resolve('success');

				await errorHandler.withErrorHandling(successfulOperation, 'test-context', {
					showSuccessToast: true,
					successMessage: 'Operation completed successfully'
				});

				const errors = get(globalErrors);
				expect(errors).toHaveLength(1);
				expect(errors[0].type).toBe('info');
				expect(errors[0].message).toBe('Operation completed successfully');
				expect(errors[0].duration).toBe(3000);
			});

			it('should include context in error handling', async () => {
				const failingOperation = () => Promise.reject(testErrors.networkError);

				await errorHandler.withErrorHandling(failingOperation, 'user-registration');

				const errors = get(globalErrors);
				expect(errors[0].context).toBe('user-registration');
			});
		});
	});

	describe('errorLogger', () => {
		beforeEach(() => {
			vi.spyOn(console, 'error').mockImplementation(() => {});
		});

		it('should log Error objects correctly', () => {
			const testError = new Error('Test error message');
			testError.stack = 'mock stack trace';

			errorLogger.log(testError, 'test-context', { extra: 'data' });

			expect(console.error).toHaveBeenCalledWith(
				expect.stringMatching(/\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\] test-context:/),
				{
					name: 'Error',
					message: 'Test error message',
					stack: 'mock stack trace'
				},
				{ extra: 'data' }
			);
		});

		it('should log string messages correctly', () => {
			errorLogger.log('String error message', 'test-context');

			expect(console.error).toHaveBeenCalledWith(
				expect.stringMatching(/\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\] test-context:/),
				{ message: 'String error message' },
				undefined
			);
		});

		it('should use default context when none provided', () => {
			errorLogger.log('Test message');

			expect(console.error).toHaveBeenCalledWith(
				expect.stringMatching(/\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\] Error:/),
				{ message: 'Test message' },
				undefined
			);
		});

		it('should log API errors with formatted context', () => {
			const apiError = {
				response: { status: 404, data: { message: 'Not found' } },
				config: { url: '/api/test', method: 'GET' }
			};

			errorLogger.logApiError(apiError, '/api/test');

			expect(console.error).toHaveBeenCalledWith(
				expect.stringMatching(/API Error \(\/api\/test\):/),
				expect.anything(),
				expect.objectContaining({
					status: 404,
					data: { message: 'Not found' },
					config: expect.anything()
				})
			);
		});
	});

	describe('validation utilities', () => {
		describe('isRequired', () => {
			it('should pass for non-empty values', () => {
				expect(validation.isRequired('test', 'field')).toBeNull();
				expect(validation.isRequired('  test  ', 'field')).toBeNull();
				expect(validation.isRequired(0, 'field')).toBeNull();
				expect(validation.isRequired(false, 'field')).toBeNull();
			});

			it('should fail for empty values', () => {
				expect(validation.isRequired(null, 'field')).toBe('field is required');
				expect(validation.isRequired(undefined, 'field')).toBe('field is required');
				expect(validation.isRequired('', 'field')).toBe('field is required');
			});
		});

		describe('isEmail', () => {
			it('should pass for valid emails', () => {
				expect(validation.isEmail('test@example.com')).toBeNull();
				expect(validation.isEmail('user+tag@domain.co.uk')).toBeNull();
			});

			it('should fail for invalid emails', () => {
				expect(validation.isEmail('not-an-email')).toBe('Please enter a valid email address');
				expect(validation.isEmail('test@')).toBe('Please enter a valid email address');
				expect(validation.isEmail('@example.com')).toBe('Please enter a valid email address');
			});
		});

		describe('minLength', () => {
			it('should pass for strings meeting minimum', () => {
				expect(validation.minLength('hello', 3, 'field')).toBeNull();
				expect(validation.minLength('hello', 5, 'field')).toBeNull();
			});

			it('should fail for strings below minimum', () => {
				expect(validation.minLength('hi', 5, 'field')).toBe(
					'field must be at least 5 characters long'
				);
			});
		});

		describe('maxLength', () => {
			it('should pass for strings within maximum', () => {
				expect(validation.maxLength('hello', 10, 'field')).toBeNull();
				expect(validation.maxLength('hello', 5, 'field')).toBeNull();
			});

			it('should fail for strings exceeding maximum', () => {
				expect(validation.maxLength('hello world', 5, 'field')).toBe(
					'field must be no more than 5 characters long'
				);
			});
		});

		describe('isNumber', () => {
			it('should pass for valid numbers', () => {
				expect(validation.isNumber(123, 'field')).toBeNull();
				expect(validation.isNumber('123', 'field')).toBeNull();
				expect(validation.isNumber('123.45', 'field')).toBeNull();
				expect(validation.isNumber(0, 'field')).toBeNull();
			});

			it('should fail for invalid numbers', () => {
				expect(validation.isNumber('not-a-number', 'field')).toBe('field must be a valid number');
				expect(validation.isNumber('', 'field')).toBe('field must be a valid number');
				expect(validation.isNumber('123abc', 'field')).toBe('field must be a valid number');
			});
		});

		describe('range', () => {
			it('should pass for values within range', () => {
				expect(validation.range(5, 1, 10, 'field')).toBeNull();
				expect(validation.range(1, 1, 10, 'field')).toBeNull();
				expect(validation.range(10, 1, 10, 'field')).toBeNull();
			});

			it('should fail for values outside range', () => {
				expect(validation.range(0, 1, 10, 'field')).toBe('field must be between 1 and 10');
				expect(validation.range(15, 1, 10, 'field')).toBe('field must be between 1 and 10');
			});
		});
	});

	describe('validateForm', () => {
		it('should validate form with multiple rules', () => {
			const values = {
				email: 'test@example.com',
				password: 'short', // This should fail minLength(8)
				age: 25
			};

			const rules = {
				email: [
					(value: unknown) => validation.isRequired(value, 'email'),
					(value: unknown) => validation.isEmail(value as string)
				],
				password: [
					(value: unknown) => validation.isRequired(value, 'password'),
					(value: unknown) => validation.minLength(value as string, 8, 'password')
				],
				age: [
					(value: unknown) => validation.isRequired(value, 'age'),
					(value: unknown) => validation.isNumber(value, 'age'),
					(value: unknown) => validation.range(value as number, 18, 120, 'age')
				]
			};

			const errors = validateForm(values, rules);

			expect(errors).toEqual({
				password: 'password must be at least 8 characters long'
			});
		});

		it('should return empty object when all validations pass', () => {
			const values = {
				email: 'test@example.com',
				name: 'John Doe'
			};

			const rules = {
				email: [
					(value: unknown) => validation.isRequired(value, 'email'),
					(value: unknown) => validation.isEmail(value as string)
				],
				name: [
					(value: unknown) => validation.isRequired(value, 'name'),
					(value: unknown) => validation.minLength(value as string, 2, 'name')
				]
			};

			const errors = validateForm(values, rules);
			expect(errors).toEqual({});
		});

		it('should stop at first error per field', () => {
			const values = {
				password: '' // Should fail both required and minLength
			};

			const rules = {
				password: [
					(value: unknown) => validation.isRequired(value, 'password'),
					(value: unknown) => validation.minLength(value as string, 8, 'password')
				]
			};

			const errors = validateForm(values, rules);

			// Should only have the required error (first one)
			expect(errors).toEqual({
				password: 'password is required'
			});
		});

		it('should handle fields with no rules', () => {
			const values = { field1: 'value1' };
			const rules = {};

			const errors = validateForm(values, rules);
			expect(errors).toEqual({});
		});
	});
});
