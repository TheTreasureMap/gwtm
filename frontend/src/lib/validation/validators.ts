/**
 * @fileoverview Comprehensive validation utilities for forms
 * @description Provides reusable validation functions, schemas, and error handling
 * @category Validation
 * @version 1.0.0
 * @author GWTM Team
 * @since 2024-01-25
 */

export type ValidationResult = {
	isValid: boolean;
	errors: string[];
	warnings?: string[];
};

export type ValidatorFunction<T = unknown> = (
	value: T,
	context?: Record<string, unknown>
) => ValidationResult;

// More flexible validator type that accepts any validator function
export type AnyValidatorFunction = ValidatorFunction<unknown>;

export type FieldValidator<T = unknown> = {
	required?: boolean;
	validators?: AnyValidatorFunction[];
	customMessage?: string;
	dependsOn?: string[];
};

export type ValidationSchema<T = Record<string, unknown>> = {
	[K in keyof T]?: FieldValidator<T[K]>;
};

/**
 * Core validation utilities
 */
export class ValidationUtils {
	/**
	 * Check if a value is empty (null, undefined, empty string, empty array)
	 */
	static isEmpty(value: unknown): boolean {
		if (value === null || value === undefined) return true;
		if (typeof value === 'string') return value.trim().length === 0;
		if (Array.isArray(value)) return value.length === 0;
		if (typeof value === 'object') return Object.keys(value).length === 0;
		return false;
	}

	/**
	 * Sanitize string input
	 */
	static sanitizeString(value: string): string {
		return value?.toString().trim() || '';
	}

	/**
	 * Check if string contains only safe characters
	 */
	static isSafeString(value: string): boolean {
		// Allow alphanumeric, spaces, basic punctuation, but block script injection
		const safePattern = /^[a-zA-Z0-9\s\-_.@#$%&()[\]{},;:!?'"+=<>/\\]*$/;
		const scriptPattern = /<script|javascript:|data:|vbscript:/i;
		return safePattern.test(value) && !scriptPattern.test(value);
	}

	/**
	 * Create a validation result
	 */
	static createResult(
		isValid: boolean,
		errors: string[] = [],
		warnings: string[] = []
	): ValidationResult {
		return { isValid, errors, warnings };
	}
}

/**
 * Common validation functions
 */
export const validators = {
	/**
	 * Required field validator
	 */
	required: (message = 'This field is required'): ValidatorFunction => {
		return (value: unknown) => {
			const isEmpty = ValidationUtils.isEmpty(value);
			return ValidationUtils.createResult(!isEmpty, isEmpty ? [message] : []);
		};
	},

	/**
	 * String length validators
	 */
	minLength: (min: number, message?: string): ValidatorFunction<string> => {
		return (value: string) => {
			const sanitized = ValidationUtils.sanitizeString(value);
			const isValid = sanitized.length >= min;
			const defaultMessage = `Must be at least ${min} characters long`;
			return ValidationUtils.createResult(isValid, isValid ? [] : [message || defaultMessage]);
		};
	},

	maxLength: (max: number, message?: string): ValidatorFunction<string> => {
		return (value: string) => {
			const sanitized = ValidationUtils.sanitizeString(value);
			const isValid = sanitized.length <= max;
			const defaultMessage = `Must be no more than ${max} characters long`;
			return ValidationUtils.createResult(isValid, isValid ? [] : [message || defaultMessage]);
		};
	},

	/**
	 * Email validator
	 */
	email: (message = 'Please enter a valid email address'): ValidatorFunction<string> => {
		return (value: string) => {
			const sanitized = ValidationUtils.sanitizeString(value);
			if (!sanitized) return ValidationUtils.createResult(true); // Empty is valid if not required

			const emailRegex =
				/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
			const isValid = emailRegex.test(sanitized);
			return ValidationUtils.createResult(isValid, isValid ? [] : [message]);
		};
	},

	/**
	 * Password strength validator
	 */
	password: (
		options: {
			minLength?: number;
			requireUppercase?: boolean;
			requireLowercase?: boolean;
			requireNumbers?: boolean;
			requireSpecialChars?: boolean;
			message?: string;
		} = {}
	): ValidatorFunction<string> => {
		const {
			minLength = 8,
			requireUppercase = true,
			requireLowercase = true,
			requireNumbers = true,
			requireSpecialChars = false
		} = options;

		return (value: string) => {
			const sanitized = ValidationUtils.sanitizeString(value);
			if (!sanitized) return ValidationUtils.createResult(true); // Empty is valid if not required

			const errors: string[] = [];

			if (sanitized.length < minLength) {
				errors.push(`Password must be at least ${minLength} characters long`);
			}

			if (requireUppercase && !/[A-Z]/.test(sanitized)) {
				errors.push('Password must contain at least one uppercase letter');
			}

			if (requireLowercase && !/[a-z]/.test(sanitized)) {
				errors.push('Password must contain at least one lowercase letter');
			}

			if (requireNumbers && !/\d/.test(sanitized)) {
				errors.push('Password must contain at least one number');
			}

			if (requireSpecialChars && !/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(sanitized)) {
				errors.push('Password must contain at least one special character');
			}

			return ValidationUtils.createResult(errors.length === 0, errors);
		};
	},

	/**
	 * Confirm password validator
	 */
	confirmPassword: (
		passwordField: string,
		message = 'Passwords do not match'
	): ValidatorFunction<string> => {
		return (value: string, context: Record<string, unknown>) => {
			const sanitized = ValidationUtils.sanitizeString(value);
			const originalPassword = context?.[passwordField];
			const isValid = sanitized === originalPassword;
			return ValidationUtils.createResult(isValid, isValid ? [] : [message]);
		};
	},

	/**
	 * URL validator
	 */
	url: (message = 'Please enter a valid URL'): ValidatorFunction<string> => {
		return (value: string) => {
			const sanitized = ValidationUtils.sanitizeString(value);
			if (!sanitized) return ValidationUtils.createResult(true); // Empty is valid if not required

			try {
				new URL(sanitized);
				return ValidationUtils.createResult(true);
			} catch {
				return ValidationUtils.createResult(false, [message]);
			}
		};
	},

	/**
	 * Number validators
	 */
	number: (message = 'Please enter a valid number'): ValidatorFunction<string | number> => {
		return (value: string | number) => {
			if (typeof value === 'number' && !isNaN(value)) {
				return ValidationUtils.createResult(true);
			}

			const sanitized = ValidationUtils.sanitizeString(value as string);
			if (!sanitized) return ValidationUtils.createResult(true); // Empty is valid if not required

			const isValid = !isNaN(Number(sanitized));
			return ValidationUtils.createResult(isValid, isValid ? [] : [message]);
		};
	},

	min: (minimum: number, message?: string): ValidatorFunction<string | number> => {
		return (value: string | number) => {
			const numValue = typeof value === 'number' ? value : Number(value);
			if (isNaN(numValue)) return ValidationUtils.createResult(true); // Let number validator handle this

			const isValid = numValue >= minimum;
			const defaultMessage = `Must be at least ${minimum}`;
			return ValidationUtils.createResult(isValid, isValid ? [] : [message || defaultMessage]);
		};
	},

	max: (maximum: number, message?: string): ValidatorFunction<string | number> => {
		return (value: string | number) => {
			const numValue = typeof value === 'number' ? value : Number(value);
			if (isNaN(numValue)) return ValidationUtils.createResult(true); // Let number validator handle this

			const isValid = numValue <= maximum;
			const defaultMessage = `Must be no more than ${maximum}`;
			return ValidationUtils.createResult(isValid, isValid ? [] : [message || defaultMessage]);
		};
	},

	/**
	 * Pattern validator
	 */
	pattern: (regex: RegExp, message = 'Invalid format'): ValidatorFunction<string> => {
		return (value: string) => {
			const sanitized = ValidationUtils.sanitizeString(value);
			if (!sanitized) return ValidationUtils.createResult(true); // Empty is valid if not required

			const isValid = regex.test(sanitized);
			return ValidationUtils.createResult(isValid, isValid ? [] : [message]);
		};
	},

	/**
	 * Custom validator
	 */
	custom: (
		validatorFn: (
			value: unknown,
			context?: Record<string, unknown>
		) => boolean | string | ValidationResult,
		message = 'Invalid value'
	): ValidatorFunction => {
		return (value: unknown, context?: Record<string, unknown>) => {
			const result = validatorFn(value, context);

			if (typeof result === 'boolean') {
				return ValidationUtils.createResult(result, result ? [] : [message]);
			}

			if (typeof result === 'string') {
				return ValidationUtils.createResult(false, [result]);
			}

			return result; // ValidationResult
		};
	},

	/**
	 * Safety validators
	 */
	safe: (message = 'Invalid characters detected'): ValidatorFunction<string> => {
		return (value: string) => {
			const sanitized = ValidationUtils.sanitizeString(value);
			if (!sanitized) return ValidationUtils.createResult(true);

			const isValid = ValidationUtils.isSafeString(sanitized);
			return ValidationUtils.createResult(isValid, isValid ? [] : [message]);
		};
	},

	/**
	 * Date validators
	 */
	date: (message = 'Please enter a valid date'): ValidatorFunction<string | Date> => {
		return (value: string | Date) => {
			if (value instanceof Date && !isNaN(value.getTime())) {
				return ValidationUtils.createResult(true);
			}

			const sanitized = ValidationUtils.sanitizeString(value as string);
			if (!sanitized) return ValidationUtils.createResult(true);

			const date = new Date(sanitized);
			const isValid = !isNaN(date.getTime());
			return ValidationUtils.createResult(isValid, isValid ? [] : [message]);
		};
	},

	minDate: (minDate: Date, message?: string): ValidatorFunction<string | Date> => {
		return (value: string | Date) => {
			const date = value instanceof Date ? value : new Date(value);
			if (isNaN(date.getTime())) return ValidationUtils.createResult(true); // Let date validator handle this

			const isValid = date >= minDate;
			const defaultMessage = `Date must be after ${minDate.toDateString()}`;
			return ValidationUtils.createResult(isValid, isValid ? [] : [message || defaultMessage]);
		};
	},

	maxDate: (maxDate: Date, message?: string): ValidatorFunction<string | Date> => {
		return (value: string | Date) => {
			const date = value instanceof Date ? value : new Date(value);
			if (isNaN(date.getTime())) return ValidationUtils.createResult(true); // Let date validator handle this

			const isValid = date <= maxDate;
			const defaultMessage = `Date must be before ${maxDate.toDateString()}`;
			return ValidationUtils.createResult(isValid, isValid ? [] : [message || defaultMessage]);
		};
	}
};

/**
 * Pre-defined validation schemas for common use cases
 */
export const validationSchemas = {
	auth: {
		login: {
			email: {
				required: true,
				validators: [validators.email()]
			},
			password: {
				required: true,
				validators: [validators.minLength(1)]
			}
		} as ValidationSchema<{ email: string; password: string }>,

		register: {
			email: {
				required: true,
				validators: [validators.email()]
			},
			username: {
				required: true,
				validators: [
					validators.minLength(3, 'Username must be at least 3 characters'),
					validators.maxLength(50, 'Username must be less than 50 characters'),
					validators.pattern(
						/^[a-zA-Z0-9_-]+$/,
						'Username can only contain letters, numbers, underscores, and dashes'
					),
					validators.safe()
				]
			},
			password: {
				required: true,
				validators: [validators.password()]
			},
			confirmPassword: {
				required: true,
				validators: [validators.confirmPassword('password')],
				dependsOn: ['password']
			},
			firstName: {
				validators: [
					validators.maxLength(100, 'First name must be less than 100 characters'),
					validators.safe()
				]
			},
			lastName: {
				validators: [
					validators.maxLength(100, 'Last name must be less than 100 characters'),
					validators.safe()
				]
			}
		} as ValidationSchema<{
			email: string;
			username: string;
			password: string;
			confirmPassword: string;
			firstName: string;
			lastName: string;
		}>
	},

	instrument: {
		create: {
			instrument_name: {
				required: true,
				validators: [
					validators.minLength(2, 'Instrument name must be at least 2 characters'),
					validators.maxLength(200, 'Instrument name must be less than 200 characters'),
					validators.safe()
				]
			},
			nickname: {
				validators: [
					validators.maxLength(100, 'Nickname must be less than 100 characters'),
					validators.safe()
				]
			},
			instrument_type: {
				required: true,
				validators: [validators.number('Please select a valid instrument type')]
			}
		} as ValidationSchema<{
			instrument_name: string;
			nickname: string;
			instrument_type: number;
		}>
	},

	pointing: {
		create: {
			ra: {
				required: true,
				validators: [
					validators.number('Right Ascension must be a valid number'),
					validators.min(0, 'Right Ascension must be between 0 and 360'),
					validators.max(360, 'Right Ascension must be between 0 and 360')
				]
			},
			dec: {
				required: true,
				validators: [
					validators.number('Declination must be a valid number'),
					validators.min(-90, 'Declination must be between -90 and 90'),
					validators.max(90, 'Declination must be between -90 and 90')
				]
			},
			depth: {
				validators: [
					validators.number('Depth must be a valid number'),
					validators.min(0, 'Depth must be positive')
				]
			},
			time: {
				validators: [validators.date('Please enter a valid observation time')]
			}
		} as ValidationSchema<{
			ra: number;
			dec: number;
			depth: number;
			time: string;
		}>
	}
};

/**
 * Field validation function
 */
export function validateField<T>(
	value: T,
	fieldConfig: FieldValidator<T>,
	context?: Record<string, unknown>,
	fieldName?: string
): ValidationResult {
	const errors: string[] = [];
	const warnings: string[] = [];

	// Check required
	if (fieldConfig.required && ValidationUtils.isEmpty(value)) {
		errors.push(fieldConfig.customMessage || `${fieldName || 'Field'} is required`);
		return { isValid: false, errors, warnings };
	}

	// Run validators
	if (fieldConfig.validators) {
		for (const validator of fieldConfig.validators) {
			const result = validator(value, context);
			errors.push(...result.errors);
			if (result.warnings) {
				warnings.push(...result.warnings);
			}
		}
	}

	return {
		isValid: errors.length === 0,
		errors,
		warnings: warnings.length > 0 ? warnings : undefined
	};
}

/**
 * Schema validation function
 */
export function validateSchema<T extends Record<string, unknown>>(
	data: T,
	schema: ValidationSchema<T>
): Record<keyof T, ValidationResult> & { isValid: boolean } {
	const results = {} as Record<keyof T, ValidationResult>;
	let isValid = true;

	// Validate each field
	for (const [fieldName, fieldConfig] of Object.entries(schema) as [keyof T, FieldValidator][]) {
		const fieldResult = validateField(data[fieldName], fieldConfig, data, fieldName as string);
		results[fieldName] = fieldResult;

		if (!fieldResult.isValid) {
			isValid = false;
		}
	}

	return { ...results, isValid };
}
