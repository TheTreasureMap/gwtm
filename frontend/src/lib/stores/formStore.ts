/**
 * @fileoverview Form management store with validation and state handling
 * @description Provides reactive form state management with built-in validation
 * @category Stores
 * @version 1.0.0
 * @author GWTM Team
 * @since 2024-01-25
 */

import { writable, derived, get } from 'svelte/store';
import type { Writable, Readable } from 'svelte/store';
import type { ValidationSchema, ValidationResult } from '$lib/validation/validators';
import { validateSchema, validateField } from '$lib/validation/validators';

export interface FormFieldState<T = unknown> {
	value: T;
	errors: string[];
	warnings: string[];
	touched: boolean;
	focused: boolean;
	isValid: boolean;
	isValidating: boolean;
}

export interface FormState<T = Record<string, unknown>> {
	data: T;
	fields: Record<keyof T, FormFieldState<T[keyof T]>>;
	isValid: boolean;
	isSubmitting: boolean;
	isDirty: boolean;
	submitCount: number;
	errors: Record<keyof T, string[]>;
	globalError: string;
}

export interface FormOptions<T = Record<string, unknown>> {
	initialValues?: Partial<T>;
	validationSchema?: ValidationSchema<T>;
	validateOnChange?: boolean;
	validateOnBlur?: boolean;
	resetOnSubmit?: boolean;
	submitHandler?: (data: T) => Promise<{ success: boolean; error?: string; result?: unknown }>;
}

/**
 * Create a reactive form store with validation
 */
export function createFormStore<T extends Record<string, unknown> = Record<string, unknown>>(
	options: FormOptions<T> = {}
) {
	const {
		initialValues = {} as Partial<T>,
		validationSchema,
		validateOnChange = true,
		validateOnBlur = true,
		resetOnSubmit = false,
		submitHandler
	} = options;

	// Initialize form state
	const initialState: FormState<T> = {
		data: { ...initialValues } as T,
		fields: {} as Record<keyof T, FormFieldState<T[keyof T]>>,
		isValid: true,
		isSubmitting: false,
		isDirty: false,
		submitCount: 0,
		errors: {} as Record<keyof T, string[]>,
		globalError: ''
	};

	// Initialize fields from initial values
	for (const [key, value] of Object.entries(initialValues)) {
		initialState.fields[key as keyof T] = {
			value,
			errors: [],
			warnings: [],
			touched: false,
			focused: false,
			isValid: true,
			isValidating: false
		};
	}

	const store = writable<FormState<T>>(initialState);

	// Derived stores for convenience
	const data = derived(store, ($store) => $store.data);
	const isValid = derived(store, ($store) => $store.isValid);
	const isSubmitting = derived(store, ($store) => $store.isSubmitting);
	const isDirty = derived(store, ($store) => $store.isDirty);
	const errors = derived(store, ($store) => $store.errors);
	const globalError = derived(store, ($store) => $store.globalError);

	// Submit result store for tracking submission results
	const submitResult = writable<{ success: boolean; error?: string; result?: unknown } | null>(
		null
	);

	/**
	 * Validate a single field
	 */
	function validateSingleField(fieldName: keyof T): ValidationResult {
		const currentState = get(store);
		const fieldValue = currentState.data[fieldName];
		const fieldConfig = validationSchema?.[fieldName];

		if (!fieldConfig) {
			return { isValid: true, errors: [] };
		}

		return validateField(fieldValue, fieldConfig, currentState.data, fieldName as string);
	}

	/**
	 * Validate all fields
	 */
	function validateAllFields(): boolean {
		if (!validationSchema) return true;

		const currentState = get(store);
		const results = validateSchema(currentState.data, validationSchema);

		store.update((state) => {
			const newFields = { ...state.fields };
			const newErrors = {} as Record<keyof T, string[]>;

			// Update field states and errors
			for (const [fieldName, result] of Object.entries(results)) {
				if (fieldName === 'isValid') continue;

				const typedFieldName = fieldName as keyof T;
				const validationResult = result as ValidationResult; // Type assertion since we know it's ValidationResult (not boolean)

				if (!newFields[typedFieldName]) {
					newFields[typedFieldName] = {
						value: state.data[typedFieldName],
						errors: [],
						warnings: [],
						touched: false,
						focused: false,
						isValid: true,
						isValidating: false
					};
				}

				newFields[typedFieldName] = {
					...newFields[typedFieldName],
					errors: validationResult.errors,
					warnings: validationResult.warnings || [],
					isValid: validationResult.isValid,
					isValidating: false
				};

				if (!validationResult.isValid) {
					newErrors[typedFieldName] = validationResult.errors;
				}
			}

			return {
				...state,
				fields: newFields,
				errors: newErrors,
				isValid: results.isValid
			};
		});

		return results.isValid;
	}

	/**
	 * Set field value and optionally validate
	 */
	function setFieldValue(fieldName: keyof T, value: T[keyof T], validate = validateOnChange): void {
		store.update((state) => {
			const newData = { ...state.data, [fieldName]: value };
			const newFields = { ...state.fields };

			// Ensure field exists
			if (!newFields[fieldName]) {
				newFields[fieldName] = {
					value,
					errors: [],
					warnings: [],
					touched: false,
					focused: false,
					isValid: true,
					isValidating: false
				};
			}

			// Update field
			newFields[fieldName] = {
				...newFields[fieldName],
				value,
				isValidating: validate
			};

			const newState = {
				...state,
				data: newData,
				fields: newFields,
				isDirty: true
			};

			// Validate if requested
			if (validate && validationSchema?.[fieldName]) {
				const validationResult = validateField(
					value,
					validationSchema[fieldName],
					newData,
					fieldName as string
				);

				newFields[fieldName] = {
					...newFields[fieldName],
					errors: validationResult.errors,
					warnings: validationResult.warnings || [],
					isValid: validationResult.isValid,
					isValidating: false
				};

				const newErrors = { ...state.errors };
				if (validationResult.isValid) {
					delete newErrors[fieldName];
				} else {
					newErrors[fieldName] = validationResult.errors;
				}

				newState.errors = newErrors;
				newState.fields = newFields;
			}

			return newState;
		});

		// Validate all fields to update overall form validity
		if (validate) {
			setTimeout(validateAllFields, 0);
		}
	}

	/**
	 * Set field as touched
	 */
	function setFieldTouched(fieldName: keyof T, touched = true): void {
		store.update((state) => {
			const newFields = { ...state.fields };

			if (!newFields[fieldName]) {
				newFields[fieldName] = {
					value: state.data[fieldName],
					errors: [],
					warnings: [],
					touched: false,
					focused: false,
					isValid: true,
					isValidating: false
				};
			}

			newFields[fieldName] = {
				...newFields[fieldName],
				touched
			};

			return { ...state, fields: newFields };
		});

		// Validate on blur if enabled
		if (touched && validateOnBlur) {
			setTimeout(() => validateSingleField(fieldName), 0);
		}
	}

	/**
	 * Set field focus state
	 */
	function setFieldFocused(fieldName: keyof T, focused = true): void {
		store.update((state) => {
			const newFields = { ...state.fields };

			if (!newFields[fieldName]) {
				newFields[fieldName] = {
					value: state.data[fieldName],
					errors: [],
					warnings: [],
					touched: false,
					focused: false,
					isValid: true,
					isValidating: false
				};
			}

			newFields[fieldName] = {
				...newFields[fieldName],
				focused
			};

			return { ...state, fields: newFields };
		});
	}

	/**
	 * Set field error
	 */
	function setFieldError(fieldName: keyof T, errors: string[]): void {
		store.update((state) => {
			const newFields = { ...state.fields };
			const newErrors = { ...state.errors };

			if (!newFields[fieldName]) {
				newFields[fieldName] = {
					value: state.data[fieldName],
					errors: [],
					warnings: [],
					touched: false,
					focused: false,
					isValid: true,
					isValidating: false
				};
			}

			newFields[fieldName] = {
				...newFields[fieldName],
				errors,
				isValid: errors.length === 0
			};

			if (errors.length > 0) {
				newErrors[fieldName] = errors;
			} else {
				delete newErrors[fieldName];
			}

			const isValid = Object.keys(newErrors).length === 0;

			return {
				...state,
				fields: newFields,
				errors: newErrors,
				isValid
			};
		});
	}

	/**
	 * Reset form to initial state
	 */
	function reset(): void {
		store.set({
			data: { ...initialValues } as T,
			fields: Object.keys(initialValues).reduce(
				(acc, key) => {
					acc[key as keyof T] = {
						value: initialValues[key as keyof T] as T[keyof T],
						errors: [],
						warnings: [],
						touched: false,
						focused: false,
						isValid: true,
						isValidating: false
					};
					return acc;
				},
				{} as Record<keyof T, FormFieldState<T[keyof T]>>
			),
			isValid: true,
			isSubmitting: false,
			isDirty: false,
			submitCount: 0,
			errors: {} as Record<keyof T, string[]>,
			globalError: ''
		});
	}

	/**
	 * Submit form
	 */
	async function submit(): Promise<{ success: boolean; error?: string; result?: unknown }> {
		store.update((state) => ({ ...state, isSubmitting: true, globalError: '' }));

		try {
			// Validate before submission
			const isFormValid = validateAllFields();

			if (!isFormValid) {
				store.update((state) => ({
					...state,
					isSubmitting: false,
					globalError: 'Please correct the errors below'
				}));
				return { success: false, error: 'Validation failed' };
			}

			const currentData = get(data);

			if (submitHandler) {
				const result = await submitHandler(currentData);

				store.update((state) => ({
					...state,
					isSubmitting: false,
					submitCount: state.submitCount + 1,
					globalError: result.success ? '' : result.error || 'Submission failed'
				}));

				// Update submit result store
				submitResult.set(result);

				if (result.success && resetOnSubmit) {
					reset();
				}

				return result;
			}

			store.update((state) => ({
				...state,
				isSubmitting: false,
				submitCount: state.submitCount + 1
			}));

			return { success: true };
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : String(error);

			store.update((state) => ({
				...state,
				isSubmitting: false,
				globalError: errorMessage
			}));

			return { success: false, error: errorMessage };
		}
	}

	/**
	 * Set global error
	 */
	function setGlobalError(error: string): void {
		store.update((state) => ({ ...state, globalError: error }));
	}

	/**
	 * Clear global error
	 */
	function clearGlobalError(): void {
		store.update((state) => ({ ...state, globalError: '' }));
	}

	/**
	 * Get field state
	 */
	function getFieldState(fieldName: keyof T): FormFieldState<T[keyof T]> {
		const currentState = get(store);
		return (
			currentState.fields[fieldName] || {
				value: currentState.data[fieldName],
				errors: [],
				warnings: [],
				touched: false,
				focused: false,
				isValid: true,
				isValidating: false
			}
		);
	}

	// Handle form submission (wrapper around submit for form events)
	async function handleSubmit(event?: Event) {
		event?.preventDefault();
		return await submit();
	}

	return {
		// Stores
		subscribe: store.subscribe,
		data,
		isValid,
		isSubmitting,
		isDirty,
		errors,
		globalError,
		submitResult,

		// Actions
		setFieldValue,
		setFieldTouched,
		setFieldFocused,
		setFieldError,
		validateField: validateSingleField,
		validateAll: validateAllFields,
		reset,
		submit,
		handleSubmit,
		setGlobalError,
		clearGlobalError,
		getFieldState,

		// Utilities
		getValue: (fieldName: keyof T) => get(data)[fieldName],
		getError: (fieldName: keyof T) => get(errors)[fieldName] || [],
		getFieldConfig: (fieldName: keyof T) => validationSchema?.[fieldName]
	};
}

/**
 * Form hook for easier usage in components
 */
export function useForm<T extends Record<string, unknown> = Record<string, unknown>>(
	options: FormOptions<T> = {}
) {
	return createFormStore<T>(options);
}
