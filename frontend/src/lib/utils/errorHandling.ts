import { writable } from 'svelte/store';

export interface AppError {
	id: string;
	message: string;
	type: 'error' | 'warning' | 'info';
	timestamp: Date;
	context?: string;
	details?: unknown;
	dismissible: boolean;
	duration?: number; // Auto-dismiss after ms (0 = no auto-dismiss)
}

export interface ErrorToastOptions {
	type?: AppError['type'];
	duration?: number;
	dismissible?: boolean;
	context?: string;
	details?: unknown;
}

// Global error store
export const globalErrors = writable<AppError[]>([]);

// Error handling utilities
export const errorHandler = {
	// Show a toast notification
	showToast(message: string, options: ErrorToastOptions = {}) {
		const error: AppError = {
			id: generateErrorId(),
			message,
			type: options.type || 'error',
			timestamp: new Date(),
			context: options.context,
			details: options.details,
			dismissible: options.dismissible ?? true,
			duration: options.duration ?? (options.type === 'error' ? 0 : 5000)
		};

		globalErrors.update((errors) => [...errors, error]);

		// Auto-dismiss if duration is set
		if (error.duration && error.duration > 0) {
			setTimeout(() => {
				this.dismissError(error.id);
			}, error.duration);
		}

		return error.id;
	},

	// Dismiss a specific error
	dismissError(errorId: string) {
		globalErrors.update((errors) => errors.filter((e) => e.id !== errorId));
	},

	// Clear all errors
	clearAllErrors() {
		globalErrors.set([]);
	},

	// Handle API errors with consistent formatting
	handleApiError(error: any, context?: string): string {
		console.error('API Error:', error, context);

		let message = 'An unexpected error occurred';
		let details = error;

		if (error?.response) {
			// Axios response error
			const status = error.response.status;
			const data = error.response.data;

			if (status === 401) {
				message = 'Authentication required. Please log in.';
			} else if (status === 403) {
				message = 'Access denied. You do not have permission to perform this action.';
			} else if (status === 404) {
				message = 'The requested resource was not found.';
			} else if (status === 422) {
				// Validation errors
				if (data?.detail && Array.isArray(data.detail)) {
					const validationErrors = data.detail
						.map((err: { loc?: string[]; msg: string }) => `${err.loc?.join('.')}: ${err.msg}`)
						.join(', ');
					message = `Validation error: ${validationErrors}`;
				} else if (data?.detail) {
					message = data.detail;
				} else {
					message = 'Invalid input data';
				}
			} else if (status === 500) {
				message = 'Internal server error. Please try again later.';
			} else if (data?.message) {
				message = data.message;
			} else if (data?.detail) {
				message = data.detail;
			} else if (status >= 400) {
				message = `Request failed with status ${status}`;
			}

			details = {
				status,
				url: error.response.config?.url,
				method: error.response.config?.method,
				data: data
			};
		} else if (error?.request) {
			// Network error
			message = 'Network error. Please check your connection and try again.';
			details = { type: 'network', request: error.request };
		} else if (error?.message) {
			// Other errors
			message = error.message;
		}

		this.showToast(message, {
			type: 'error',
			context,
			details,
			dismissible: true,
			duration: 0 // Don't auto-dismiss API errors
		});

		return message;
	},

	// Handle async operations with error boundaries
	async withErrorHandling<T>(
		operation: () => Promise<T>,
		context?: string,
		options: {
			showSuccessToast?: boolean;
			successMessage?: string;
			retryable?: boolean;
		} = {}
	): Promise<T | null> {
		try {
			const result = await operation();

			if (options.showSuccessToast && options.successMessage) {
				this.showToast(options.successMessage, {
					type: 'info',
					duration: 3000
				});
			}

			return result;
		} catch (error) {
			this.handleApiError(error, context);
			return null;
		}
	}
};

// Utility functions
function generateErrorId(): string {
	return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Error logging utilities
export const errorLogger = {
	log(error: any, context?: string, extra?: unknown) {
		const timestamp = new Date().toISOString();
		const errorObj =
			error instanceof Error
				? {
						name: error.name,
						message: error.message,
						stack: error.stack
					}
				: { message: error };

		console.error(`[${timestamp}] ${context || 'Error'}:`, errorObj, extra);

		// In production, you might want to send this to an error reporting service
		if (import.meta.env.PROD) {
			// Example: Send to error reporting service
			// errorReportingService.captureException(error, { context, extra });
		}
	},

	logApiError(error: any, endpoint?: string) {
		this.log(error, `API Error${endpoint ? ` (${endpoint})` : ''}`, {
			status: error?.response?.status,
			data: error?.response?.data,
			config: error?.config
		});
	}
};

// Validation utilities
export const validation = {
	isRequired(value: unknown, fieldName: string): string | null {
		if (value === null || value === undefined || value === '') {
			return `${fieldName} is required`;
		}
		return null;
	},

	isEmail(value: string): string | null {
		const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
		if (!emailRegex.test(value)) {
			return 'Please enter a valid email address';
		}
		return null;
	},

	minLength(value: string, min: number, fieldName: string): string | null {
		if (value.length < min) {
			return `${fieldName} must be at least ${min} characters long`;
		}
		return null;
	},

	maxLength(value: string, max: number, fieldName: string): string | null {
		if (value.length > max) {
			return `${fieldName} must be no more than ${max} characters long`;
		}
		return null;
	},

	isNumber(value: unknown, fieldName: string): string | null {
		if (isNaN(value as number) || value === '') {
			return `${fieldName} must be a valid number`;
		}
		return null;
	},

	range(value: number, min: number, max: number, fieldName: string): string | null {
		if (value < min || value > max) {
			return `${fieldName} must be between ${min} and ${max}`;
		}
		return null;
	}
};

// Form validation helper
export function validateForm(
	values: Record<string, unknown>,
	rules: Record<string, ((value: unknown) => string | null)[]>
): Record<string, string> {
	const errors: Record<string, string> = {};

	for (const [field, fieldRules] of Object.entries(rules)) {
		const value = values[field];

		for (const rule of fieldRules) {
			const error = rule(value);
			if (error) {
				errors[field] = error;
				break; // Stop at first error for this field
			}
		}
	}

	return errors;
}
