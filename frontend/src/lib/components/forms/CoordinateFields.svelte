<script lang="ts">
	/**
	 * @component CoordinateFields
	 * @description A specialized component for RA/Dec coordinate input with validation
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
		change: { ra: number | null; dec: number | null };
		validate: { isValid: boolean; errors: string[] };
	}>();

	/**
	 * Right Ascension value (0-360 degrees)
	 * @type {number | null}
	 */
	export let ra: number | null = null;

	/**
	 * Declination value (-90 to +90 degrees)
	 * @type {number | null}
	 */
	export let dec: number | null = null;

	/**
	 * Whether the coordinates are required
	 * @type {boolean}
	 * @default true
	 */
	export let required: boolean = true;

	/**
	 * Whether the fields are disabled
	 * @type {boolean}
	 * @default false
	 */
	export let disabled: boolean = false;

	/**
	 * Custom CSS classes
	 * @type {string}
	 * @default ''
	 */
	export let className: string = '';

	/**
	 * Help text for the coordinate fields
	 * @type {string}
	 * @default ''
	 */
	export let helpText: string = 'Enter coordinates in decimal degrees';

	// Validation state
	let raValid = true;
	let decValid = true;
	let raErrors: string[] = [];
	let decErrors: string[] = [];

	// RA validators (0-360 degrees)
	const raValidators: ValidatorFunction[] = [
		validators.number(),
		validators.min(0, 'RA must be between 0 and 360 degrees'),
		validators.max(360, 'RA must be between 0 and 360 degrees')
	];

	// Dec validators (-90 to +90 degrees)
	const decValidators: ValidatorFunction[] = [
		validators.number(),
		validators.min(-90, 'Dec must be between -90 and +90 degrees'),
		validators.max(90, 'Dec must be between -90 and +90 degrees')
	];

	// Handle field changes and validation
	function handleRaChange(event: CustomEvent) {
		ra = event.detail.value;
		raValid = event.detail.isValid;
		raErrors = event.detail.errors;
		dispatchChange();
	}

	function handleDecChange(event: CustomEvent) {
		dec = event.detail.value;
		decValid = event.detail.isValid;
		decErrors = event.detail.errors;
		dispatchChange();
	}

	function dispatchChange() {
		const isValid = raValid && decValid;
		const allErrors = [...(raErrors || []), ...(decErrors || [])];

		dispatch('change', { ra, dec });
		dispatch('validate', { isValid, errors: allErrors });
	}

	// Computed properties
	$: isValid = raValid && decValid;
	$: allErrors = [...(raErrors || []), ...(decErrors || [])];
</script>

<div class="coordinate-fields {className}">
	<div class="coordinate-grid">
		<FormField
			name="ra"
			label="Right Ascension (RA)"
			type="number"
			bind:value={ra}
			{required}
			{disabled}
			validators={raValidators}
			placeholder="0.0 - 360.0"
			helpText="Degrees (0-360)"
			on:change={handleRaChange}
			on:validate={handleRaChange}
		/>

		<FormField
			name="dec"
			label="Declination (Dec)"
			type="number"
			bind:value={dec}
			{required}
			{disabled}
			validators={decValidators}
			placeholder="-90.0 - +90.0"
			helpText="Degrees (-90 to +90)"
			on:change={handleDecChange}
			on:validate={handleDecChange}
		/>
	</div>

	{#if helpText && (ra !== null || dec !== null)}
		<div class="coordinate-info">
			<p class="info-text">{helpText}</p>
			{#if ra !== null && dec !== null}
				<p class="coordinate-display">
					Coordinates: RA {ra.toFixed(6)}°, Dec {dec >= 0 ? '+' : ''}{dec.toFixed(6)}°
				</p>
			{/if}
		</div>
	{/if}

	<!-- Validation summary -->
	{#if !isValid && allErrors.length > 0}
		<div class="coordinate-errors" role="alert">
			{#each allErrors as error, index (index)}
				<p class="error-text">{error}</p>
			{/each}
		</div>
	{/if}
</div>

<style>
	.coordinate-fields {
		margin-bottom: 1rem;
	}

	.coordinate-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.coordinate-info {
		margin-top: 0.5rem;
		padding: 0.75rem;
		background-color: #f3f4f6;
		border-radius: 0.375rem;
		border: 1px solid #d1d5db;
	}

	.info-text {
		font-size: 0.875rem;
		color: #6b7280;
		margin: 0 0 0.25rem 0;
	}

	.coordinate-display {
		font-size: 0.875rem;
		font-weight: 600;
		color: #374151;
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		margin: 0;
	}

	.coordinate-errors {
		margin-top: 0.5rem;
		padding: 0.75rem;
		background-color: #fef2f2;
		border: 1px solid #fca5a5;
		border-radius: 0.375rem;
	}

	.error-text {
		font-size: 0.875rem;
		color: #dc2626;
		margin: 0;
	}

	.error-text:not(:last-child) {
		margin-bottom: 0.25rem;
	}

	/* Responsive design */
	@media (max-width: 640px) {
		.coordinate-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
