<script lang="ts">
	/**
	 * @component TimeField
	 * @description A specialized datetime input field with proper formatting and validation
	 * @category Forms
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 */

	import { createEventDispatcher } from 'svelte';
	import FormField from './FormField.svelte';
	import type { ValidatorFunction } from '$lib/validation/validators';
	import { validators } from '$lib/validation/validators';

	const dispatch = createEventDispatcher<{
		change: { name: string; value: string | null };
		validate: { name: string; isValid: boolean; errors: string[] };
	}>();

	/**
	 * Field name/id
	 * @type {string}
	 */
	export let name: string;

	/**
	 * Field label
	 * @type {string}
	 */
	export let label: string;

	/**
	 * The datetime value as ISO string
	 * @type {string | null}
	 */
	export let value: string | null = null;

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
	 * Help text for the field
	 * @type {string}
	 * @default ''
	 */
	export let helpText: string = '';

	/**
	 * Custom CSS classes
	 * @type {string}
	 * @default ''
	 */
	export let className: string = '';

	/**
	 * Minimum date/time allowed
	 * @type {string | null}
	 */
	export let min: string | null = null;

	/**
	 * Maximum date/time allowed
	 * @type {string | null}
	 */
	export let max: string | null = null;

	// Internal formatted value for the datetime-local input
	let formattedValue: string = '';

	// Validation
	const timeValidators: ValidatorFunction[] = [
		validators.date('Invalid datetime format'),
		...(min ? [validators.minDate(new Date(min), `Date must be after ${formatDisplayDate(min)}`)] : []),
		...(max ? [validators.maxDate(new Date(max), `Date must be before ${formatDisplayDate(max)}`)] : [])
	];

	// Format ISO string to datetime-local format (YYYY-MM-DDTHH:mm:ss.sss)
	function formatToDatetimeLocal(isoString: string | null): string {
		if (!isoString) return '';
		
		try {
			const date = new Date(isoString);
			if (isNaN(date.getTime())) return '';
			
			// Format to YYYY-MM-DDTHH:mm:ss.sss
			const year = date.getFullYear();
			const month = String(date.getMonth() + 1).padStart(2, '0');
			const day = String(date.getDate()).padStart(2, '0');
			const hours = String(date.getHours()).padStart(2, '0');
			const minutes = String(date.getMinutes()).padStart(2, '0');
			const seconds = String(date.getSeconds()).padStart(2, '0');
			const ms = String(date.getMilliseconds()).padStart(3, '0');
			
			return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}.${ms}`;
		} catch {
			return '';
		}
	}

	// Convert datetime-local format to ISO string
	function formatToISO(datetimeLocal: string): string | null {
		if (!datetimeLocal) return null;
		
		try {
			// Parse the datetime-local format and convert to ISO
			const date = new Date(datetimeLocal);
			if (isNaN(date.getTime())) return null;
			
			return date.toISOString();
		} catch {
			return null;
		}
	}

	// Format date for display in validation messages
	function formatDisplayDate(isoString: string): string {
		try {
			return new Date(isoString).toLocaleString();
		} catch {
			return isoString;
		}
	}

	// Handle input changes
	function handleChange(event: CustomEvent) {
		formattedValue = event.detail.value;
		value = formatToISO(formattedValue);
		
		dispatch('change', { name, value });
	}

	function handleValidate(event: CustomEvent) {
		dispatch('validate', {
			name,
			isValid: event.detail.isValid,
			errors: event.detail.errors
		});
	}

	// Update formatted value when value prop changes
	$: formattedValue = formatToDatetimeLocal(value);

	// Current time helper for setting default values
	export function setCurrentTime() {
		const now = new Date();
		value = now.toISOString();
		formattedValue = formatToDatetimeLocal(value);
	}

	// Validation helpers
	$: placeholder = 'YYYY-MM-DDTHH:MM:SS.sss (e.g., 2001-01-01T12:30:15.500)';
	$: finalHelpText = helpText || 'Enter date and time in the format shown';
</script>

<div class="time-field {className}">
	<FormField
		{name}
		{label}
		type="text"
		bind:value={formattedValue}
		{required}
		{disabled}
		validators={timeValidators}
		{placeholder}
		helpText={finalHelpText}
		on:change={handleChange}
		on:validate={handleValidate}
	/>

	<!-- Additional controls -->
	<div class="time-controls">
		<button
			type="button"
			class="btn-secondary btn-sm"
			on:click={setCurrentTime}
			{disabled}
		>
			Set Current Time
		</button>

		{#if value}
			<button
				type="button"
				class="btn-secondary btn-sm"
				on:click={() => {
					value = null;
					formattedValue = '';
				}}
				{disabled}
			>
				Clear
			</button>
		{/if}
	</div>

	<!-- Display parsed time for confirmation -->
	{#if value && formattedValue}
		<div class="time-display">
			<p class="parsed-time">
				Parsed: {new Date(value).toLocaleString()}
			</p>
		</div>
	{/if}
</div>

<style>
	.time-field {
		margin-bottom: 1rem;
	}

	.time-controls {
		display: flex;
		gap: 0.5rem;
		margin-top: 0.5rem;
	}

	.btn-secondary {
		padding: 0.375rem 0.75rem;
		font-size: 0.875rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		background-color: #f9fafb;
		color: #374151;
		cursor: pointer;
		transition: all 0.15s ease-in-out;
	}

	.btn-secondary:hover:not(:disabled) {
		background-color: #f3f4f6;
		border-color: #9ca3af;
	}

	.btn-secondary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
	}

	.time-display {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background-color: #f0f9ff;
		border: 1px solid #bae6fd;
		border-radius: 0.375rem;
	}

	.parsed-time {
		font-size: 0.875rem;
		color: #0369a1;
		font-weight: 500;
		margin: 0;
	}

	/* Focus styles */
	.btn-secondary:focus {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
	}
</style>