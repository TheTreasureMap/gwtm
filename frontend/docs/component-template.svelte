<script lang="ts">
	/**
	 * @component ComponentTemplate
	 * @description Template for creating new documented components
	 * @category Template
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 *
	 * @accessibility
	 * - [List accessibility features]
	 * - [Keyboard support details]
	 * - [Screen reader compatibility]
	 * - [ARIA implementation notes]
	 *
	 * @performance
	 * - [Performance characteristics]
	 * - [Optimization techniques used]
	 * - [Resource usage notes]
	 *
	 * @example
	 * ```svelte
	 * <!-- Basic usage -->
	 * <ComponentTemplate
	 *   prop1="value"
	 *   prop2={variable}
	 *   on:event={handler}
	 * >
	 *   Default slot content
	 * </ComponentTemplate>
	 *
	 * <!-- Advanced usage -->
	 * <ComponentTemplate bind:value {options} let:item>
	 *   <div slot="header">Custom header</div>
	 *   <CustomItem {item} />
	 *   <div slot="footer">Custom footer</div>
	 * </ComponentTemplate>
	 * ```
	 *
	 * @see RelatedComponent - Brief description of relationship
	 * @see AnotherComponent - Another related component
	 */

	import { createEventDispatcher, onMount } from 'svelte';
	import { writable } from 'svelte/store';

	/**
	 * @event {CustomEvent<{value: string}>} change - Fired when the value changes
	 * @event {CustomEvent<{item: any}>} select - Fired when an item is selected
	 * @event {CustomEvent<{error: Error}>} error - Fired when an error occurs
	 */
	const dispatch = createEventDispatcher<{
		change: { value: string };
		select: { item: any };
		error: { error: Error };
	}>();

	// ================================================================================================
	// PROPS - Document all exported properties
	// ================================================================================================

	/**
	 * Main value of the component
	 * @type {string}
	 * @default ''
	 */
	export let value: string = '';

	/**
	 * Visual variant of the component
	 * @type {'primary' | 'secondary' | 'tertiary'}
	 * @default 'primary'
	 */
	export let variant: 'primary' | 'secondary' | 'tertiary' = 'primary';

	/**
	 * Size of the component
	 * @type {'sm' | 'md' | 'lg'}
	 * @default 'md'
	 */
	export let size: 'sm' | 'md' | 'lg' = 'md';

	/**
	 * Whether the component is disabled
	 * @type {boolean}
	 * @default false
	 */
	export let disabled: boolean = false;

	/**
	 * Whether the component is in loading state
	 * @type {boolean}
	 * @default false
	 */
	export let loading: boolean = false;

	/**
	 * Additional CSS classes to apply
	 * @type {string}
	 * @default ''
	 * @optional
	 */
	export let className: string = '';

	/**
	 * Configuration options for the component
	 * @type {Object}
	 * @optional
	 */
	export let options: Record<string, any> = {};

	/**
	 * Error message to display
	 * @type {string}
	 * @optional
	 */
	export let error: string = '';

	/**
	 * Help text to display
	 * @type {string}
	 * @optional
	 */
	export let helpText: string = '';

	/**
	 * ARIA label for accessibility
	 * @type {string}
	 * @optional
	 */
	export let ariaLabel: string = '';

	// ================================================================================================
	// INTERNAL STATE - Document complex internal state
	// ================================================================================================

	/**
	 * Internal state store for component data
	 * @internal
	 */
	const internalState = writable({
		isInitialized: false,
		hasError: false,
		lastUpdated: null as Date | null
	});

	/**
	 * Computed CSS classes based on props
	 * @internal
	 */
	$: componentClasses = [
		'component-base',
		`component-${variant}`,
		`component-${size}`,
		disabled ? 'component-disabled' : '',
		loading ? 'component-loading' : '',
		error ? 'component-error' : '',
		className
	]
		.filter(Boolean)
		.join(' ');

	/**
	 * Whether the component should show loading indicator
	 * @internal
	 */
	$: showLoading = loading && !disabled;

	// ================================================================================================
	// METHODS - Document public methods
	// ================================================================================================

	/**
	 * Focus the component
	 * @public
	 * @returns {void}
	 */
	export function focus(): void {
		// Implementation
	}

	/**
	 * Reset the component to initial state
	 * @public
	 * @returns {void}
	 */
	export function reset(): void {
		value = '';
		error = '';
		internalState.update((state) => ({
			...state,
			hasError: false,
			lastUpdated: new Date()
		}));
	}

	/**
	 * Validate the current value
	 * @public
	 * @returns {boolean} Whether the value is valid
	 */
	export function validate(): boolean {
		// Implementation
		return true;
	}

	// ================================================================================================
	// EVENT HANDLERS - Document internal event handlers
	// ================================================================================================

	/**
	 * Handle value changes
	 * @internal
	 * @param {string} newValue - The new value
	 */
	function handleValueChange(newValue: string): void {
		value = newValue;
		dispatch('change', { value: newValue });
	}

	/**
	 * Handle item selection
	 * @internal
	 * @param {any} item - The selected item
	 */
	function handleItemSelect(item: any): void {
		dispatch('select', { item });
	}

	/**
	 * Handle errors
	 * @internal
	 * @param {Error} err - The error that occurred
	 */
	function handleError(err: Error): void {
		error = err.message;
		dispatch('error', { error: err });
	}

	// ================================================================================================
	// LIFECYCLE - Document lifecycle methods
	// ================================================================================================

	/**
	 * Initialize component on mount
	 * @internal
	 */
	onMount(() => {
		internalState.update((state) => ({
			...state,
			isInitialized: true,
			lastUpdated: new Date()
		}));

		// Cleanup function
		return () => {
			// Cleanup logic here
		};
	});
</script>

<!--
Component template with documented slots

@slot default - Main content area
@slot header - Header content (optional)
@slot footer - Footer content (optional)
@slot loading - Custom loading indicator (optional)
@slot error - Custom error display (optional)
@slot {string} value - Current value
@slot {boolean} loading - Current loading state  
@slot {boolean} disabled - Current disabled state
@slot {any} item - Current item (for list components)
-->

<div
	class={componentClasses}
	role="region"
	aria-label={ariaLabel}
	aria-busy={loading}
	aria-invalid={!!error}
>
	<!-- Header slot -->
	{#if $$slots.header}
		<header class="component-header">
			<slot name="header" {value} {loading} {disabled} />
		</header>
	{/if}

	<!-- Main content -->
	<main class="component-main">
		{#if showLoading && $$slots.loading}
			<slot name="loading" />
		{:else if error && $$slots.error}
			<slot name="error" {error} />
		{:else}
			<slot {value} {loading} {disabled} />
		{/if}
	</main>

	<!-- Footer slot -->
	{#if $$slots.footer}
		<footer class="component-footer">
			<slot name="footer" {value} {loading} {disabled} />
		</footer>
	{/if}

	<!-- Help text -->
	{#if helpText}
		<div class="component-help" aria-describedby="help-text">
			{helpText}
		</div>
	{/if}

	<!-- Error message -->
	{#if error && !$$slots.error}
		<div class="component-error-message" role="alert">
			{error}
		</div>
	{/if}
</div>

<style>
	/*
	Component styles with documentation
	
	CSS custom properties for theming:
	--component-bg: Background color
	--component-text: Text color
	--component-border: Border color
	--component-radius: Border radius
	--component-shadow: Box shadow
	*/

	.component-base {
		/* Base styles */
		display: block;
		background: var(--component-bg, #fff);
		color: var(--component-text, #1f2937);
		border: 1px solid var(--component-border, #d1d5db);
		border-radius: var(--component-radius, 0.375rem);
		box-shadow: var(--component-shadow, 0 1px 2px 0 rgba(0, 0, 0, 0.05));
		transition: all 0.2s ease-in-out;
	}

	/* Variant styles */
	.component-primary {
		--component-bg: #3b82f6;
		--component-text: #ffffff;
		--component-border: #2563eb;
	}

	.component-secondary {
		--component-bg: #6b7280;
		--component-text: #ffffff;
		--component-border: #4b5563;
	}

	/* Size styles */
	.component-sm {
		padding: 0.5rem;
		font-size: 0.875rem;
	}

	.component-md {
		padding: 0.75rem;
		font-size: 1rem;
	}

	.component-lg {
		padding: 1rem;
		font-size: 1.125rem;
	}

	/* State styles */
	.component-disabled {
		opacity: 0.5;
		cursor: not-allowed;
		pointer-events: none;
	}

	.component-loading {
		position: relative;
		pointer-events: none;
	}

	.component-error {
		--component-border: #ef4444;
		--component-bg: #fef2f2;
	}

	/* Layout styles */
	.component-header {
		margin-bottom: 0.5rem;
	}

	.component-main {
		flex: 1;
	}

	.component-footer {
		margin-top: 0.5rem;
	}

	.component-help {
		margin-top: 0.25rem;
		font-size: 0.875rem;
		color: #6b7280;
	}

	.component-error-message {
		margin-top: 0.25rem;
		font-size: 0.875rem;
		color: #ef4444;
	}

	/* Responsive styles */
	@media (max-width: 640px) {
		.component-base {
			--component-radius: 0.25rem;
		}
	}

	/* Focus styles */
	.component-base:focus-within {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
	}

	/* High contrast mode support */
	@media (prefers-contrast: high) {
		.component-base {
			border-width: 2px;
		}
	}

	/* Reduced motion support */
	@media (prefers-reduced-motion: reduce) {
		.component-base {
			transition: none;
		}
	}
</style>
