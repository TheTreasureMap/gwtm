<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import type { ValidationSchema } from '$lib/validation/validators';
	import { validateSchema } from '$lib/validation/validators';
	import Button from '$lib/components/ui/Button.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';

	/**
	 * @event {CustomEvent<{data: any, isValid: boolean}>} change - Fired when form data changes
	 * @event {CustomEvent<{data: any}>} submit - Fired when form is submitted (before onSubmit)
	 * @event {CustomEvent<{result: any}>} success - Fired when submission succeeds
	 * @event {CustomEvent<{error: Error | string}>} error - Fired when submission fails
	 * @event {CustomEvent<{field: string, value: any, isValid: boolean}>} fieldChange - Fired when individual field changes
	 */
	const dispatch = createEventDispatcher<{
		change: { data: any; isValid: boolean };
		submit: { data: any };
		success: { result: any };
		error: { error: Error | string };
		fieldChange: { field: string; value: any; isValid: boolean };
	}>();

	// ================================================================================================
	// PROPS
	// ================================================================================================

	/**
	 * Form data object
	 * @type {Record<string, any>}
	 * @default {}
	 */
	export let data: Record<string, any> = {};

	/**
	 * Validation schema for the form
	 * @type {ValidationSchema}
	 * @optional
	 */
	export let schema: ValidationSchema | undefined = undefined;

	/**
	 * Function called when form is submitted
	 * @type {(data: any) => Promise<{success: boolean, error?: string, result?: any}>}
	 * @optional
	 */
	export let onSubmit:
		| ((data: any) => Promise<{ success: boolean; error?: string; result?: any }>)
		| undefined = undefined;

	/**
	 * Text for the submit button
	 * @type {string}
	 * @default 'Submit'
	 */
	export let submitText: string = 'Submit';

	/**
	 * Text for the submit button when loading
	 * @type {string}
	 * @optional
	 */
	export let submitLoadingText: string = '';

	/**
	 * Whether to show a submit button
	 * @type {boolean}
	 * @default true
	 */
	export let showSubmitButton: boolean = true;

	/**
	 * Submit button variant
	 * @type {'primary' | 'secondary' | 'ghost' | 'outline' | 'danger'}
	 * @default 'primary'
	 */
	export let submitVariant: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' = 'primary';

	/**
	 * Whether to validate on input
	 * @type {boolean}
	 * @default true
	 */
	export let validateOnInput: boolean = true;

	/**
	 * Whether to validate on blur
	 * @type {boolean}
	 * @default true
	 */
	export const validateOnBlur: boolean = true;

	/**
	 * Whether to prevent submission of invalid forms
	 * @type {boolean}
	 * @default true
	 */
	export let preventInvalidSubmission: boolean = true;

	/**
	 * Custom CSS classes for the form
	 * @type {string}
	 * @default ''
	 * @optional
	 */
	export let className: string = '';

	/**
	 * Whether to reset form after successful submission
	 * @type {boolean}
	 * @default false
	 */
	export let resetOnSuccess: boolean = false;

	/**
	 * Initial values for the form
	 * @type {Record<string, any>}
	 * @optional
	 */
	export let initialValues: Record<string, any> = {};

	// ================================================================================================
	// STATE
	// ================================================================================================

	let isSubmitting = false;
	let submitError = '';
	let fieldErrors: Record<string, string[]> = {};
	let fieldValidationStates: Record<string, boolean> = {};
	let formElement: HTMLFormElement;

	// Computed states
	$: isValid =
		Object.values(fieldValidationStates).every(Boolean) && Object.keys(fieldErrors).length === 0;

	// Form classes
	$: formClasses = ['space-y-6', className].filter(Boolean).join(' ');

	// ================================================================================================
	// METHODS
	// ================================================================================================

	/**
	 * Validate the entire form
	 */
	export function validate(): boolean {
		if (!schema) return true;

		const results = validateSchema(data, schema);
		fieldErrors = {};

		// Extract field errors
		for (const [fieldName, result] of Object.entries(results)) {
			if (fieldName !== 'isValid' && !result.isValid) {
				fieldErrors[fieldName] = result.errors;
			}
		}

		// Update validation states
		for (const fieldName of Object.keys(schema)) {
			fieldValidationStates[fieldName] = results[fieldName]?.isValid ?? true;
		}

		dispatch('change', { data, isValid: results.isValid });
		return results.isValid;
	}

	/**
	 * Reset the form to initial values
	 */
	export function reset() {
		data = { ...initialValues };
		fieldErrors = {};
		fieldValidationStates = {};
		submitError = '';
		isSubmitting = false;
	}

	/**
	 * Get validation config for a specific field
	 */
	export function getFieldConfig(fieldName: string) {
		return schema?.[fieldName] || {};
	}

	/**
	 * Handle field validation events
	 */
	function handleFieldValidation(
		event: CustomEvent<{ name: string; value: any; isValid: boolean; errors: string[] }>
	) {
		const { name, value, isValid, errors } = event.detail;

		// Update field validation state
		fieldValidationStates[name] = isValid;

		// Update field errors
		if (errors.length > 0) {
			fieldErrors[name] = errors;
		} else {
			delete fieldErrors[name];
		}

		// Update data
		data[name] = value;

		// Trigger reactive updates
		fieldErrors = { ...fieldErrors };
		fieldValidationStates = { ...fieldValidationStates };

		dispatch('fieldChange', { field: name, value, isValid });
		dispatch('change', { data, isValid });
	}

	/**
	 * Handle form submission
	 */
	async function handleSubmit(event: Event) {
		event.preventDefault();

		submitError = '';

		// Validate form before submission
		if (preventInvalidSubmission && !validate()) {
			// Focus first invalid field
			const firstErrorField = Object.keys(fieldErrors)[0];
			if (firstErrorField) {
				const fieldElement = formElement.querySelector(
					`[name="${firstErrorField}"]`
				) as HTMLElement;
				fieldElement?.focus();
			}
			return;
		}

		dispatch('submit', { data });

		if (!onSubmit) return;

		isSubmitting = true;

		try {
			const result = await onSubmit(data);

			if (result.success) {
				dispatch('success', { result: result.result });

				if (resetOnSuccess) {
					reset();
				}
			} else {
				submitError = result.error || 'Submission failed';
				dispatch('error', { error: submitError });
			}
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : String(error);
			submitError = errorMessage;
			dispatch('error', { error: errorMessage });
		} finally {
			isSubmitting = false;
		}
	}

	// ================================================================================================
	// LIFECYCLE
	// ================================================================================================

	onMount(() => {
		// Initialize form data with initial values
		if (Object.keys(initialValues).length > 0) {
			data = { ...initialValues, ...data };
		}

		// Initial validation if schema exists
		if (schema) {
			validate();
		}
	});

	// Reactive validation when data changes
	$: if (schema && validateOnInput) {
		validate();
	}
</script>

<!--
@slot default - Form content (fields and other elements)
@slot footer - Custom footer content (overrides default submit button)
@slot {Record<string, any>} data - Current form data
@slot {boolean} isValid - Whether form is currently valid
@slot {boolean} isSubmitting - Whether form is currently being submitted
@slot {Record<string, string[]>} fieldErrors - Current field validation errors
@slot {string} submitError - Current submission error
@slot {function} field - Function to get field configuration
@slot {function} validate - Function to manually validate form
@slot {function} reset - Function to reset form
-->

<form
	bind:this={formElement}
	class={formClasses}
	on:submit={handleSubmit}
	novalidate
	aria-label="Form"
>
	<!-- Form Content -->
	<div class="form-content">
		<slot
			{data}
			{isValid}
			{isSubmitting}
			{fieldErrors}
			{submitError}
			field={getFieldConfig}
			{validate}
			{reset}
		/>
	</div>

	<!-- Global Form Error -->
	{#if submitError}
		<ErrorMessage message={submitError} title="Submission Error" type="error" />
	{/if}

	<!-- Form Footer -->
	<div class="form-footer">
		{#if $$slots.footer}
			<slot
				name="footer"
				{data}
				{isValid}
				{isSubmitting}
				{fieldErrors}
				{submitError}
				{validate}
				{reset}
			/>
		{:else if showSubmitButton}
			<Button
				type="submit"
				variant={submitVariant}
				loading={isSubmitting}
				disabled={preventInvalidSubmission ? !isValid || isSubmitting : isSubmitting}
				fullWidth
			>
				{#if isSubmitting && submitLoadingText}
					{submitLoadingText}
				{:else if isSubmitting}
					Submitting...
				{:else}
					{submitText}
				{/if}
			</Button>
		{/if}
	</div>
</form>

<!-- Field validation event handling -->
<svelte:window on:field-validate={handleFieldValidation} />

<style>
	.form-content {
		display: contents;
	}

	.form-footer {
		margin-top: 1.5rem;
	}

	/* Ensure proper spacing between form elements */
	.form-content > :global(.form-field:not(:last-child)) {
		margin-bottom: 1rem;
	}

	/* Focus management for accessibility */
	form:focus-within {
		outline: none;
	}

	/* High contrast mode support */
	@media (prefers-contrast: high) {
		form {
			border: 1px solid;
			padding: 1rem;
			border-radius: 0.375rem;
		}
	}
</style>
