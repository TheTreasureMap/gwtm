/**
 * @fileoverview Form validation hooks for reactive form management
 * @description Provides composable hooks for form validation and state management
 * @category Hooks
 * @version 1.0.0
 * @author GWTM Team
 * @since 2024-01-25
 */

import { writable, derived } from 'svelte/store';
import type { Writable, Readable } from 'svelte/store';
import type {
	ValidatorFunction,
	ValidationResult,
	ValidationSchema
} from '$lib/validation/validators';
import { validateField, validateSchema } from '$lib/validation/validators';

export interface UseFieldValidationOptions<T = unknown> {
	validators?: ValidatorFunction[];
	required?: boolean;
	validateOnChange?: boolean;
	validateOnBlur?: boolean;
	debounceMs?: number;
	initialValue?: T;
}

export interface FieldValidationState<T = unknown> {
	value: T;
	errors: string[];
	warnings: string[];
	isValid: boolean;
	isValidating: boolean;
	touched: boolean;
	focused: boolean;
}

/**
 * Hook for managing individual field validation
 */
export function useFieldValidation<T = unknown>(options: UseFieldValidationOptions<T> = {}) {
	const {
		validators = [],
		required = false,
		validateOnChange = true,
		validateOnBlur = true,
		debounceMs = 300,
		initialValue = ''
	} = options;

	// Create stores
	const state = writable<FieldValidationState<T>>({
		value: initialValue as T,
		errors: [],
		warnings: [],
		isValid: true,
		isValidating: false,
		touched: false,
		focused: false
	});

	// Derived stores
	const value = derived(state, ($state) => $state.value);
	const errors = derived(state, ($state) => $state.errors);
	const isValid = derived(state, ($state) => $state.isValid);
	const isValidating = derived(state, ($state) => $state.isValidating);

	let validationTimeout: ReturnType<typeof setTimeout>;
	let validationContext: Record<string, unknown> = {};

	/**
	 * Validate the field
	 */
	function validate(context?: Record<string, unknown>): ValidationResult {
		state.update((s) => ({ ...s, isValidating: true }));

		const currentState = state.subscribe ? state : { subscribe: () => ({}) };
		let currentValue: T;

		// Get current value from state
		const unsubscribe = state.subscribe((s) => {
			currentValue = s.value;
		});
		unsubscribe();

		const fieldConfig = { required, validators };
		const result = validateField(currentValue, fieldConfig, context || validationContext);

		state.update((s) => ({
			...s,
			errors: result.errors,
			warnings: result.warnings || [],
			isValid: result.isValid,
			isValidating: false
		}));

		return result;
	}

	/**
	 * Debounced validation
	 */
	function debouncedValidate(context?: Record<string, unknown>) {
		clearTimeout(validationTimeout);
		validationTimeout = setTimeout(() => validate(context), debounceMs);
	}

	/**
	 * Set field value
	 */
	function setValue(newValue: T, shouldValidate = validateOnChange) {
		state.update((s) => ({ ...s, value: newValue }));

		if (shouldValidate) {
			debouncedValidate();
		}
	}

	/**
	 * Set touched state
	 */
	function setTouched(touched = true) {
		state.update((s) => ({ ...s, touched }));

		if (touched && validateOnBlur) {
			validate();
		}
	}

	/**
	 * Set focused state
	 */
	function setFocused(focused = true) {
		state.update((s) => ({ ...s, focused }));
	}

	/**
	 * Set validation context
	 */
	function setValidationContext(context: Record<string, unknown>) {
		validationContext = context;
	}

	/**
	 * Set external errors
	 */
	function setErrors(errors: string[]) {
		state.update((s) => ({
			...s,
			errors,
			isValid: errors.length === 0
		}));
	}

	/**
	 * Clear errors
	 */
	function clearErrors() {
		state.update((s) => ({
			...s,
			errors: [],
			warnings: [],
			isValid: true
		}));
	}

	/**
	 * Reset field to initial state
	 */
	function reset() {
		clearTimeout(validationTimeout);
		state.set({
			value: initialValue,
			errors: [],
			warnings: [],
			isValid: true,
			isValidating: false,
			touched: false,
			focused: false
		});
	}

	return {
		// Stores
		state,
		value,
		errors,
		isValid,
		isValidating,

		// Actions
		setValue,
		setTouched,
		setFocused,
		setValidationContext,
		setErrors,
		clearErrors,
		validate,
		reset,

		// Cleanup
		destroy: () => clearTimeout(validationTimeout)
	};
}

export interface UseFormValidationOptions<T = Record<string, unknown>> {
	schema?: ValidationSchema<T>;
	initialValues?: Partial<T>;
	validateOnChange?: boolean;
	validateOnBlur?: boolean;
	mode?: 'onChange' | 'onBlur' | 'onSubmit';
}

export interface FormValidationState<T = Record<string, unknown>> {
	values: T;
	errors: Record<keyof T, string[]>;
	touched: Record<keyof T, boolean>;
	isValid: boolean;
	isValidating: boolean;
	isDirty: boolean;
}

/**
 * Hook for managing form-level validation
 */
export function useFormValidation<T extends Record<string, unknown> = Record<string, unknown>>(
	options: UseFormValidationOptions<T> = {}
) {
	const {
		schema,
		initialValues = {} as Partial<T>,
		validateOnChange = true,
		validateOnBlur = true,
		mode = 'onChange'
	} = options;

	// Create stores
	const state = writable<FormValidationState<T>>({
		values: { ...initialValues } as T,
		errors: {} as Record<keyof T, string[]>,
		touched: {} as Record<keyof T, boolean>,
		isValid: true,
		isValidating: false,
		isDirty: false
	});

	// Derived stores
	const values = derived(state, ($state) => $state.values);
	const errors = derived(state, ($state) => $state.errors);
	const isValid = derived(state, ($state) => $state.isValid);
	const isValidating = derived(state, ($state) => $state.isValidating);
	const isDirty = derived(state, ($state) => $state.isDirty);

	let fieldValidators: Record<string, ReturnType<typeof setTimeout>> = {};

	/**
	 * Validate specific field
	 */
	function validateFormField(
		fieldName: keyof T,
		context?: Record<string, unknown>
	): ValidationResult {
		if (!schema || !schema[fieldName]) {
			return { isValid: true, errors: [] };
		}

		let currentValues: T;
		let fieldValue: T[keyof T];

		// Get current values from state
		const unsubscribe = state.subscribe((s) => {
			currentValues = s.values;
			fieldValue = s.values[fieldName];
		});
		unsubscribe();

		const result = validateField(
			fieldValue,
			schema[fieldName]!,
			context || currentValues!,
			fieldName as string
		);

		// Update field errors
		state.update((s) => {
			const newErrors = { ...s.errors };

			if (result.isValid) {
				delete newErrors[fieldName];
			} else {
				newErrors[fieldName] = result.errors;
			}

			return {
				...s,
				errors: newErrors,
				isValid: Object.keys(newErrors).length === 0
			};
		});

		return result;
	}

	/**
	 * Validate all fields
	 */
	function validateAll(): boolean {
		if (!schema) return true;

		state.update((s) => ({ ...s, isValidating: true }));

		let currentValues: T;
		const unsubscribe = state.subscribe((s) => {
			currentValues = s.values;
		});
		unsubscribe();

		const results = validateSchema(currentValues!, schema);

		const newErrors = {} as Record<keyof T, string[]>;

		// Extract field errors
		for (const [fieldName, result] of Object.entries(results)) {
			if (
				fieldName !== 'isValid' &&
				typeof result === 'object' &&
				result !== null &&
				'isValid' in result &&
				!result.isValid
			) {
				newErrors[fieldName as keyof T] = result.errors;
			}
		}

		state.update((s) => ({
			...s,
			errors: newErrors,
			isValid: results.isValid,
			isValidating: false
		}));

		return results.isValid;
	}

	/**
	 * Set field value
	 */
	function setFieldValue(fieldName: keyof T, value: T[keyof T]) {
		state.update((s) => ({
			...s,
			values: { ...s.values, [fieldName]: value },
			isDirty: true
		}));

		// Validate based on mode
		if ((mode === 'onChange' || validateOnChange) && schema?.[fieldName]) {
			clearTimeout(fieldValidators[fieldName as string]);
			fieldValidators[fieldName as string] = setTimeout(() => {
				validateFormField(fieldName);
			}, 300);
		}
	}

	/**
	 * Set multiple field values
	 */
	function setValues(newValues: Partial<T>) {
		state.update((s) => ({
			...s,
			values: { ...s.values, ...newValues },
			isDirty: true
		}));

		if (mode === 'onChange' || validateOnChange) {
			setTimeout(validateAll, 300);
		}
	}

	/**
	 * Set field as touched
	 */
	function setFieldTouched(fieldName: keyof T, touched = true) {
		state.update((s) => ({
			...s,
			touched: { ...s.touched, [fieldName]: touched }
		}));

		if (touched && (mode === 'onBlur' || validateOnBlur)) {
			validateFormField(fieldName);
		}
	}

	/**
	 * Set field error
	 */
	function setFieldError(fieldName: keyof T, errors: string[]) {
		state.update((s) => {
			const newErrors = { ...s.errors };

			if (errors.length > 0) {
				newErrors[fieldName] = errors;
			} else {
				delete newErrors[fieldName];
			}

			return {
				...s,
				errors: newErrors,
				isValid: Object.keys(newErrors).length === 0
			};
		});
	}

	/**
	 * Clear all errors
	 */
	function clearErrors() {
		state.update((s) => ({
			...s,
			errors: {} as Record<keyof T, string[]>,
			isValid: true
		}));
	}

	/**
	 * Reset form
	 */
	function reset() {
		// Clear all timeouts
		Object.values(fieldValidators).forEach(clearTimeout);
		fieldValidators = {};

		state.set({
			values: { ...initialValues } as T,
			errors: {} as Record<keyof T, string[]>,
			touched: {} as Record<keyof T, boolean>,
			isValid: true,
			isValidating: false,
			isDirty: false
		});
	}

	/**
	 * Get field helpers
	 */
	function getFieldHelpers(fieldName: keyof T) {
		return {
			setValue: (value: T[keyof T]) => setFieldValue(fieldName, value),
			setTouched: (touched = true) => setFieldTouched(fieldName, touched),
			setError: (errors: string[]) => setFieldError(fieldName, errors),
			validate: () => validateFormField(fieldName),
			getValue: () => derived(values, (v) => v[fieldName]),
			getError: () => derived(errors, (e) => e[fieldName] || []),
			isTouched: () => derived(state, (s) => s.touched[fieldName] || false)
		};
	}

	return {
		// Stores
		state,
		values,
		errors,
		isValid,
		isValidating,
		isDirty,

		// Actions
		setFieldValue,
		setValues,
		setFieldTouched,
		setFieldError,
		clearErrors,
		validateField: validateFormField,
		validateAll,
		reset,

		// Helpers
		getFieldHelpers,

		// Cleanup
		destroy: () => {
			Object.values(fieldValidators).forEach(clearTimeout);
		}
	};
}

/**
 * Simple validation hook for single values
 */
export function useValidation<T = unknown>(
	validators: ValidatorFunction[],
	initialValue: T,
	options: { debounceMs?: number; validateOnChange?: boolean } = {}
) {
	const { debounceMs = 300, validateOnChange = true } = options;

	const value = writable(initialValue);
	const errors = writable<string[]>([]);
	const isValid = writable(true);
	const isValidating = writable(false);

	let validationTimeout: ReturnType<typeof setTimeout>;

	function validate(val?: T, context?: Record<string, unknown>): ValidationResult {
		isValidating.set(true);

		const currentValue = val !== undefined ? val : value;
		let combinedResult: ValidationResult = { isValid: true, errors: [] };

		// Run all validators
		for (const validator of validators) {
			const result = validator(currentValue, context);
			if (!result.isValid) {
				combinedResult = {
					isValid: false,
					errors: [...combinedResult.errors, ...result.errors],
					warnings: [...(combinedResult.warnings || []), ...(result.warnings || [])]
				};
			}
		}

		errors.set(combinedResult.errors);
		isValid.set(combinedResult.isValid);
		isValidating.set(false);

		return combinedResult;
	}

	function debouncedValidate(val?: T, context?: Record<string, unknown>) {
		clearTimeout(validationTimeout);
		validationTimeout = setTimeout(() => validate(val, context), debounceMs);
	}

	function setValue(newValue: T, shouldValidate = validateOnChange) {
		value.set(newValue);

		if (shouldValidate) {
			debouncedValidate(newValue);
		}
	}

	return {
		value,
		errors,
		isValid,
		isValidating,
		setValue,
		validate,
		reset: () => {
			clearTimeout(validationTimeout);
			value.set(initialValue);
			errors.set([]);
			isValid.set(true);
			isValidating.set(false);
		},
		destroy: () => clearTimeout(validationTimeout)
	};
}
