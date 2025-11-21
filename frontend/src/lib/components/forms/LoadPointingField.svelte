<script lang="ts">
	/**
	 * @component LoadPointingField
	 * @description A specialized field that loads existing pointing data when a pointing ID is entered
	 * @category Forms
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 */

	import { createEventDispatcher } from 'svelte';
	import { onMount } from 'svelte';
	import FormField from './FormField.svelte';
	import type { ValidatorFunction } from '$lib/validation/validators';
	import { validators } from '$lib/validation/validators';

	const dispatch = createEventDispatcher<{
		load: { pointingId: number; data: any };
		change: { name: string; value: number | null };
		validate: { name: string; isValid: boolean; errors: string[] };
		error: { message: string };
	}>();

	/**
	 * Field name/id
	 * @type {string}
	 */
	export let name: string = 'loadid';

	/**
	 * Field label
	 * @type {string}
	 */
	export let label: string = 'Load Existing Pointing ID';

	/**
	 * The pointing ID value
	 * @type {number | null}
	 */
	export let value: number | null = null;

	/**
	 * Whether the field is disabled
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
	 * Help text for the field
	 * @type {string}
	 * @default ''
	 */
	export let helpText: string = '';

	/**
	 * API base URL for loading pointing data (unused - kept for external reference)
	 * @type {string}
	 * @default '/api/v1'
	 */
	export const apiBaseUrl: string = '/api/v1';

	// Internal state
	let loading = false;
	let lastLoadedId: number | null = null;
	let loadError: string | null = null;
	let loadTimeout: ReturnType<typeof setTimeout>;

	// Validation
	const idValidators: ValidatorFunction[] = [
		validators.number('Must be a valid pointing ID'),
		validators.min(1, 'Pointing ID must be greater than 0')
	];

	// Load pointing data from API
	async function loadPointingData(pointingId: number) {
		if (pointingId === lastLoadedId) return; // Already loaded

		loading = true;
		loadError = null;

		try {
			const response = await fetch(`/ajax_pointingfromid?id=${pointingId}`, {
				headers: {
					Authorization: `Bearer ${localStorage.getItem('access_token')}`
				}
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => null);
				const errorMessage = errorData?.detail || response.statusText;

				if (response.status === 404) {
					throw new Error(errorMessage);
				} else if (response.status === 403) {
					throw new Error(errorMessage);
				} else if (response.status === 400) {
					throw new Error(errorMessage);
				}
				throw new Error(`Failed to load pointing: ${errorMessage}`);
			}

			const data = await response.json();
			lastLoadedId = pointingId;

			dispatch('load', { pointingId, data });
		} catch (error) {
			loadError = error instanceof Error ? error.message : 'Failed to load pointing data';
			dispatch('error', { message: loadError });
		} finally {
			loading = false;
		}
	}

	// Debounced load function
	function debouncedLoad(pointingId: number) {
		clearTimeout(loadTimeout);
		loadTimeout = setTimeout(() => {
			loadPointingData(pointingId);
		}, 500); // 500ms delay
	}

	// Handle field changes
	function handleChange(event: CustomEvent) {
		value = event.detail.value;
		dispatch('change', { name, value });

		// Clear previous error
		loadError = null;

		// Auto-load if we have a valid ID
		if (value && value > 0) {
			debouncedLoad(value);
		}
	}

	function handleValidate(event: CustomEvent) {
		dispatch('validate', {
			name,
			isValid: event.detail.isValid,
			errors: event.detail.errors
		});
	}

	// Manual load button handler
	function handleManualLoad() {
		if (value && value > 0) {
			loadPointingData(value);
		}
	}

	// Clear loaded data
	function handleClear() {
		value = null;
		lastLoadedId = null;
		loadError = null;
		dispatch('change', { name, value });
	}

	// Cleanup timeout on destroy
	onMount(() => {
		return () => {
			clearTimeout(loadTimeout);
		};
	});

	// Help text based on state
	$: dynamicHelpText = loading
		? 'Loading pointing data...'
		: helpText || 'Enter a pointing ID to pre-load existing data';
</script>

<div class="load-pointing-field {className}">
	<FormField
		{name}
		{label}
		type="number"
		bind:value
		{disabled}
		validators={idValidators}
		placeholder="Enter pointing ID"
		helpText={dynamicHelpText}
		on:change={handleChange}
		on:validate={handleValidate}
	/>

	<!-- Controls -->
	<div class="load-controls">
		<button
			type="button"
			class="btn-primary btn-sm"
			on:click={handleManualLoad}
			disabled={!value || value <= 0 || loading || disabled}
		>
			{#if loading}
				<span class="spinner"></span>
				Loading...
			{:else}
				Load Data
			{/if}
		</button>

		{#if value}
			<button type="button" class="btn-secondary btn-sm" on:click={handleClear} {disabled}>
				Clear
			</button>
		{/if}
	</div>

	<!-- Load status -->
	{#if lastLoadedId}
		<div class="load-success">
			<p class="success-text">
				✓ Loaded data from pointing ID {lastLoadedId}
			</p>
		</div>
	{/if}

	<!-- Error display -->
	{#if loadError}
		<div class="load-error" role="alert">
			<p class="error-text">{loadError}</p>
		</div>
	{/if}
</div>

<style>
	.load-pointing-field {
		margin-bottom: 1rem;
	}

	.load-controls {
		display: flex;
		gap: 0.5rem;
		margin-top: 0.5rem;
	}

	.btn-primary,
	.btn-secondary {
		padding: 0.375rem 0.75rem;
		font-size: 0.875rem;
		border-radius: 0.375rem;
		cursor: pointer;
		transition: all 0.15s ease-in-out;
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.btn-primary {
		background-color: #3b82f6;
		color: white;
		border: 1px solid #3b82f6;
	}

	.btn-primary:hover:not(:disabled) {
		background-color: #2563eb;
		border-color: #2563eb;
	}

	.btn-primary:disabled {
		background-color: #9ca3af;
		border-color: #9ca3af;
		cursor: not-allowed;
	}

	.btn-secondary {
		background-color: #f9fafb;
		color: #374151;
		border: 1px solid #d1d5db;
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

	.spinner {
		width: 0.75rem;
		height: 0.75rem;
		border: 2px solid transparent;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.load-success {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background-color: #ecfdf5;
		border: 1px solid #86efac;
		border-radius: 0.375rem;
	}

	.success-text {
		font-size: 0.875rem;
		color: #059669;
		margin: 0;
		font-weight: 500;
	}

	.load-error {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background-color: #fef2f2;
		border: 1px solid #fca5a5;
		border-radius: 0.375rem;
	}

	.error-text {
		font-size: 0.875rem;
		color: #dc2626;
		margin: 0;
	}

	/* Focus styles */
	.btn-primary:focus,
	.btn-secondary:focus {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
	}
</style>
