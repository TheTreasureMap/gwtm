<script lang="ts">
	/**
	 * @component FormField
	 * @description A reusable form field component with built-in validation and consistent styling
	 * @category Forms
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 *
	 * @accessibility
	 * - Proper label association with input fields
	 * - ARIA attributes for validation states
	 * - Screen reader accessible error messages
	 * - Keyboard navigation support
	 *
	 * @performance
	 * - Debounced validation to prevent excessive re-renders
	 * - Efficient error state management
	 * - Minimal DOM updates with reactive statements
	 *
	 * @example
	 * ```svelte
	 * <!-- Basic text input -->
	 * <FormField
	 *   name="email"
	 *   label="Email Address"
	 *   type="email"
	 *   bind:value={formData.email}
	 *   validators={[validators.required(), validators.email()]}
	 *   placeholder="Enter your email"
	 * />
	 *
	 * <!-- Required field with custom validation -->
	 * <FormField
	 *   name="username"
	 *   label="Username"
	 *   bind:value={formData.username}
	 *   required
	 *   validators={[validators.minLength(3), validators.pattern(/^[a-zA-Z0-9_]+$/)]}
	 *   helpText="Username can only contain letters, numbers, and underscores"
	 * />
	 *
	 * <!-- Select dropdown -->
	 * <FormField
	 *   name="category"
	 *   label="Category"
	 *   type="select"
	 *   bind:value={formData.category}
	 *   options={categoryOptions}
	 *   required
	 * />
	 *
	 * <!-- Textarea with validation -->
	 * <FormField
	 *   name="description"
	 *   label="Description"
	 *   type="textarea"
	 *   bind:value={formData.description}
	 *   validators={[validators.maxLength(500)]}
	 *   rows={4}
	 * />
	 * ```
	 *
	 * @see Form - For complete form management
	 * @see validators - For available validation functions
	 */

	import { createEventDispatcher, onMount } from 'svelte';
	import type { ValidatorFunction, ValidationResult } from '$lib/validation/validators';
	import { validateField } from '$lib/validation/validators';

	/**
	 * @event {CustomEvent<{name: string, value: unknown, isValid: boolean}>} validate - Fired when field validation changes
	 * @event {CustomEvent<{name: string, value: unknown}>} change - Fired when field value changes
	 * @event {CustomEvent<{name: string}>} focus - Fired when field receives focus
	 * @event {CustomEvent<{name: string}>} blur - Fired when field loses focus
	 */
	const dispatch = createEventDispatcher<{
		validate: { name: string; value: unknown; isValid: boolean; errors: string[] };
		change: { name: string; value: unknown };
		focus: { name: string };
		blur: { name: string };
	}>();

	// ================================================================================================
	// PROPS
	// ================================================================================================

	/**
	 * The name/id of the form field
	 * @type {string}
	 */
	export let name: string;

	/**
	 * Custom id for the form field (overrides auto-generated id)
	 * @type {string}
	 * @optional
	 */
	export let id: string = '';

	/**
	 * The label text for the field
	 * @type {string}
	 */
	export let label: string;

	/**
	 * The input type
	 * @type {'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search' | 'textarea' | 'select' | 'checkbox' | 'radio'}
	 * @default 'text'
	 */
	export let type:
		| 'text'
		| 'email'
		| 'password'
		| 'number'
		| 'tel'
		| 'url'
		| 'search'
		| 'textarea'
		| 'select'
		| 'checkbox'
		| 'radio' = 'text';

	/**
	 * The field value
	 * @type {unknown}
	 * @default ''
	 */
	export let value: unknown = '';

	/**
	 * Placeholder text
	 * @type {string}
	 * @default ''
	 * @optional
	 */
	export let placeholder: string = '';

	/**
	 * Whether the field is required
	 * @type {boolean}
	 * @default false
	 */
	export let required: boolean = false;

	/**
	 * Whether the field is disabled
	 * @type {boolean}
	 * @default false
	 */
	export let disabled: boolean = false;

	/**
	 * Whether the field is readonly
	 * @type {boolean}
	 * @default false
	 */
	export let readonly: boolean = false;

	/**
	 * Array of validation functions
	 * @type {ValidatorFunction[]}
	 * @default []
	 * @optional
	 */
	export let validators: ValidatorFunction[] = [];

	/**
	 * Help text to display below the field
	 * @type {string}
	 * @default ''
	 * @optional
	 */
	export let helpText: string = '';

	/**
	 * Options for select/radio fields
	 * @type {Array<{value: unknown, label: string, disabled?: boolean}>}
	 * @default []
	 * @optional
	 */
	export let options: Array<{ value: unknown; label: string; disabled?: boolean }> = [];

	/**
	 * Number of rows for textarea
	 * @type {number}
	 * @default 3
	 * @optional
	 */
	export let rows: number = 3;

	/**
	 * Custom CSS classes
	 * @type {string}
	 * @default ''
	 * @optional
	 */
	export let className: string = '';

	/**
	 * Whether to validate on input (live validation)
	 * @type {boolean}
	 * @default true
	 */
	export let validateOnInput: boolean = true;

	/**
	 * Whether to validate on blur
	 * @type {boolean}
	 * @default true
	 */
	export let validateOnBlur: boolean = true;

	/**
	 * External validation errors (from form-level validation)
	 * @type {string[]}
	 * @default []
	 * @optional
	 */
	export let externalErrors: string[] = [];

	/**
	 * Context data for validation (e.g., other form fields)
	 * @type {Record<string, unknown>}
	 * @optional
	 */
	export let validationContext: Record<string, unknown> = {};

	// ================================================================================================
	// STATE
	// ================================================================================================

	let validationResult: ValidationResult = { isValid: true, errors: [] };
	let touched = false;
	let validationTimeout: ReturnType<typeof setTimeout>;

	// Computed states
	$: hasError = !validationResult.isValid || externalErrors.length > 0;
	$: allErrors = [...validationResult.errors, ...externalErrors];
	$: showErrors = touched && hasError;
	$: fieldId = id || `field-${name}`;
	$: helpId = `${fieldId}-help`;
	$: errorId = `${fieldId}-error`;

	// Input classes
	$: inputClasses = [
		'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset',
		'placeholder:text-gray-400 focus:ring-2 focus:ring-inset sm:text-sm sm:leading-6',
		hasError && touched
			? 'ring-red-500 focus:ring-red-500 text-red-900'
			: 'ring-gray-300 focus:ring-blue-600',
		disabled ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : 'bg-white',
		readonly ? 'bg-gray-50' : '',
		className
	]
		.filter(Boolean)
		.join(' ');

	// Label classes
	$: labelClasses = [
		'block text-sm font-medium leading-6',
		hasError && touched ? 'text-red-700' : 'text-gray-900'
	].join(' ');

	// ================================================================================================
	// METHODS
	// ================================================================================================

	/**
	 * Validate the field value
	 */
	function validate() {
		const fieldConfig = {
			required,
			validators: validators
		};

		validationResult = validateField(value, fieldConfig, validationContext, name);

		dispatch('validate', {
			name,
			value,
			isValid: validationResult.isValid && externalErrors.length === 0,
			errors: allErrors
		});
	}

	/**
	 * Debounced validation for input events
	 */
	function debouncedValidate() {
		clearTimeout(validationTimeout);
		validationTimeout = setTimeout(validate, 300);
	}

	/**
	 * Handle input events
	 */
	function handleInput(event: Event) {
		const target = event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;

		if (type === 'checkbox') {
			value = (target as HTMLInputElement).checked;
		} else if (type === 'number') {
			value = target.value === '' ? '' : Number(target.value);
		} else {
			value = target.value;
		}

		dispatch('change', { name, value });

		if (validateOnInput) {
			debouncedValidate();
		}
	}

	/**
	 * Handle focus events
	 */
	function handleFocus() {
		dispatch('focus', { name });
	}

	/**
	 * Handle blur events
	 */
	function handleBlur() {
		touched = true;

		dispatch('blur', { name });

		if (validateOnBlur) {
			validate();
		}
	}

	// ================================================================================================
	// LIFECYCLE
	// ================================================================================================

	onMount(() => {
		// Initial validation if field has a value
		if (value !== '' && value !== null && value !== undefined) {
			validate();
		}

		return () => {
			clearTimeout(validationTimeout);
		};
	});

	// Reactive validation when external factors change
	$: if (validators.length > 0 || required) {
		validate();
	}
</script>

<!--
@slot label - Custom label content (overrides label prop)
@slot help - Custom help text content (overrides helpText prop)
@slot {string} name - Field name
@slot {any} value - Current field value
@slot {boolean} hasError - Whether field has validation errors
@slot {string[]} errors - Current validation errors
@slot {boolean} required - Whether field is required
@slot {boolean} disabled - Whether field is disabled
-->

<div class="form-field">
	<!-- Label -->
	<label for={fieldId} class={labelClasses}>
		{#if $$slots.label}
			<slot
				name="label"
				fieldName={name}
				fieldValue={value}
				fieldHasError={hasError}
				fieldErrors={allErrors}
				fieldRequired={required}
				fieldDisabled={disabled}
			/>
		{:else}
			{label}
			{#if required}
				<span class="text-red-500 ml-1" aria-label="required">*</span>
			{/if}
		{/if}
	</label>

	<!-- Input Field -->
	<div class="mt-2">
		{#if type === 'textarea'}
			<textarea
				id={fieldId}
				{name}
				{rows}
				{placeholder}
				{disabled}
				{readonly}
				{required}
				class={inputClasses}
				bind:value
				on:input={handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
				aria-describedby={helpText || showErrors ? `${helpId} ${errorId}` : undefined}
				aria-invalid={hasError}
			></textarea>
		{:else if type === 'select'}
			<select
				id={fieldId}
				{name}
				{disabled}
				{required}
				class={inputClasses}
				bind:value
				on:change={handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
				aria-describedby={helpText || showErrors ? `${helpId} ${errorId}` : undefined}
				aria-invalid={hasError}
			>
				{#if placeholder}
					<option value="" disabled selected>{placeholder}</option>
				{/if}
				{#each options as option, index (index)}
					<option value={option.value} disabled={option.disabled}>
						{option.label}
					</option>
				{/each}
			</select>
		{:else if type === 'checkbox'}
			<div class="flex items-center">
				<input
					id={fieldId}
					{name}
					type="checkbox"
					{disabled}
					{required}
					class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600"
					bind:checked={value}
					on:change={handleInput}
					on:focus={handleFocus}
					on:blur={handleBlur}
					aria-describedby={helpText || showErrors ? `${helpId} ${errorId}` : undefined}
					aria-invalid={hasError}
				/>
				<label for={fieldId} class="ml-3 block text-sm font-medium leading-6 text-gray-900">
					{label}
					{#if required}
						<span class="text-red-500 ml-1" aria-label="required">*</span>
					{/if}
				</label>
			</div>
		{:else if type === 'radio'}
			<fieldset class="space-y-2">
				<legend class="sr-only">{label}</legend>
				{#each options as option, index (index)}
					<div class="flex items-center">
						<input
							id="{fieldId}-{option.value}"
							{name}
							type="radio"
							value={option.value}
							{disabled}
							{required}
							class="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-600"
							bind:group={value}
							on:change={handleInput}
							on:focus={handleFocus}
							on:blur={handleBlur}
							aria-describedby={helpText || showErrors ? `${helpId} ${errorId}` : undefined}
						/>
						<label
							for="{fieldId}-{option.value}"
							class="ml-3 block text-sm font-medium leading-6 text-gray-900"
						>
							{option.label}
						</label>
					</div>
				{/each}
			</fieldset>
		{:else}
			<input
				id={fieldId}
				{name}
				{type}
				{placeholder}
				{disabled}
				{readonly}
				{required}
				step={type === 'number' ? 'any' : undefined}
				class={inputClasses}
				bind:value
				on:input={handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
				aria-describedby={helpText || showErrors ? `${helpId} ${errorId}` : undefined}
				aria-invalid={hasError}
			/>
		{/if}
	</div>

	<!-- Help Text -->
	{#if helpText || $$slots.help}
		<div id={helpId} class="mt-2 text-sm text-gray-600">
			{#if $$slots.help}
				<slot
					name="help"
					fieldName={name}
					fieldValue={value}
					fieldHasError={hasError}
					fieldErrors={allErrors}
				/>
			{:else}
				{helpText}
			{/if}
		</div>
	{/if}

	<!-- Error Messages -->
	{#if showErrors}
		<div id={errorId} class="mt-2 space-y-1" role="alert" aria-live="polite">
			{#each allErrors as error, index (index)}
				<p class="text-sm text-red-600">{error}</p>
			{/each}
		</div>
	{/if}

	<!-- Validation Warnings -->
	{#if validationResult.warnings && validationResult.warnings.length > 0}
		<div class="mt-2 space-y-1">
			{#each validationResult.warnings as warning, index (index)}
				<p class="text-sm text-yellow-600">{warning}</p>
			{/each}
		</div>
	{/if}
</div>

<style>
	.form-field {
		margin-bottom: 1rem;
	}

	/* Focus styles for better accessibility */
	.form-field input:focus,
	.form-field textarea:focus,
	.form-field select:focus {
		outline: 2px solid transparent;
		outline-offset: 2px;
	}

	/* High contrast mode support */
	@media (prefers-contrast: high) {
		.form-field input,
		.form-field textarea,
		.form-field select {
			border-width: 2px;
		}
	}

	/* Reduced motion support */
	@media (prefers-reduced-motion: reduce) {
		.form-field * {
			transition: none;
		}
	}
</style>
