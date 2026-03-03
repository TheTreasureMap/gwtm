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
	import type { AnyValidatorFunction, ValidationResult } from '$lib/validation/validators';
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
	export let validators: AnyValidatorFunction[] = [];

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
	 * Custom CSS classes for the wrapper element
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

	/**
	 * Step attribute for number inputs
	 * @type {string}
	 * @default 'any'
	 * @optional
	 */
	export let step: string = 'any';

	/**
	 * External error override (for backward compatibility)
	 * @type {string}
	 * @default ''
	 * @optional
	 */
	export let error: string = '';

	/**
	 * Min attribute for number inputs
	 * @type {string}
	 * @default undefined
	 * @optional
	 */
	export let min: string | undefined = undefined;

	// ================================================================================================
	// STATE
	// ================================================================================================

	let validationResult: ValidationResult = { isValid: true, errors: [] };
	let touched = false;
	let validationTimeout: ReturnType<typeof setTimeout>;

	// Computed states
	$: hasError = !validationResult.isValid || externalErrors.length > 0 || error !== '';
	$: allErrors = [...validationResult.errors, ...externalErrors, ...(error ? [error] : [])];
	$: showErrors = touched && hasError;
	$: fieldId = id || `field-${name}`;
	$: helpId = `${fieldId}-help`;
	$: errorId = `${fieldId}-error`;

	// DaisyUI input classes
	$: inputBaseClass =
		type === 'select'
			? 'select select-bordered w-full'
			: type === 'textarea'
				? 'textarea textarea-bordered w-full'
				: type === 'checkbox' || type === 'radio'
					? ''
					: 'input input-bordered w-full';

	$: inputErrorClass = hasError && touched ? 'input-error select-error textarea-error' : '';

	$: disabledClass = disabled ? 'opacity-50 cursor-not-allowed' : '';

	$: inputClass = [inputBaseClass, inputErrorClass, disabledClass].filter(Boolean).join(' ');

	$: labelTextClass = hasError && touched ? 'label-text text-error' : 'label-text';

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

<div class="form-control mb-4 {className}">
	{#if type !== 'checkbox'}
		<!-- Label -->
		<label for={fieldId} class="label">
			<span class={labelTextClass}>
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
						<span class="text-error ml-1" aria-label="required">*</span>
					{/if}
				{/if}
			</span>
		</label>
	{/if}

	<!-- Input Field -->
	{#if type === 'textarea'}
		<textarea
			id={fieldId}
			{name}
			{rows}
			{placeholder}
			{disabled}
			{readonly}
			{required}
			class={inputClass}
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
			class={inputClass}
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
		<label for={fieldId} class="label cursor-pointer justify-start gap-3">
			<input
				id={fieldId}
				{name}
				type="checkbox"
				{disabled}
				{required}
				class="checkbox {disabledClass}"
				bind:checked={value as boolean}
				on:change={handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
				aria-describedby={helpText || showErrors ? `${helpId} ${errorId}` : undefined}
				aria-invalid={hasError}
			/>
			<span class="label-text">
				{label}
				{#if required}
					<span class="text-error ml-1" aria-label="required">*</span>
				{/if}
			</span>
		</label>
	{:else if type === 'radio'}
		<fieldset class="space-y-2">
			<legend class="sr-only">{label}</legend>
			{#each options as option, index (index)}
				<div class="form-control">
					<label for="{fieldId}-{option.value}" class="label cursor-pointer justify-start gap-3">
						<input
							id="{fieldId}-{option.value}"
							{name}
							type="radio"
							value={option.value}
							{disabled}
							{required}
							class="radio {disabledClass}"
							bind:group={value}
							on:change={handleInput}
							on:focus={handleFocus}
							on:blur={handleBlur}
							aria-describedby={helpText || showErrors ? `${helpId} ${errorId}` : undefined}
						/>
						<span class="label-text">{option.label}</span>
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
			step={type === 'number' ? step : undefined}
			min={type === 'number' ? min : undefined}
			class={inputClass}
			bind:value
			on:input={handleInput}
			on:focus={handleFocus}
			on:blur={handleBlur}
			aria-describedby={helpText || showErrors ? `${helpId} ${errorId}` : undefined}
			aria-invalid={hasError}
		/>
	{/if}

	<!-- Help Text -->
	{#if helpText || $$slots.help}
		<div id={helpId} class="label">
			<span class="label-text-alt">
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
			</span>
		</div>
	{/if}

	<!-- Error Messages -->
	{#if showErrors}
		<div id={errorId} role="alert" aria-live="polite">
			{#each allErrors as errorMsg, index (index)}
				<div class="label">
					<span class="label-text-alt text-error">{errorMsg}</span>
				</div>
			{/each}
		</div>
	{/if}

	<!-- Validation Warnings -->
	{#if validationResult.warnings && validationResult.warnings.length > 0}
		<div>
			{#each validationResult.warnings as warning, index (index)}
				<div class="label">
					<span class="label-text-alt text-warning">{warning}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>
