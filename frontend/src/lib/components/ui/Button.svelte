<script lang="ts">
	/**
	 * @component Button
	 * @description A versatile button component with multiple variants, sizes, and states
	 * @category UI
	 * @version 1.2.0
	 * @author GWTM Team
	 * @since 2024-01-15
	 *
	 * @accessibility
	 * - Fully keyboard accessible with proper focus management
	 * - Screen reader compatible with semantic HTML
	 * - ARIA attributes for loading and disabled states
	 * - Supports high contrast mode
	 *
	 * @performance
	 * - Minimal CSS-in-JS overhead with computed classes
	 * - Efficient event handling without unnecessary re-renders
	 * - Optimized for both button and link rendering
	 *
	 * @example
	 * ```svelte
	 * <!-- Basic usage -->
	 * <Button variant="primary" on:click={handleClick}>
	 *   Click me
	 * </Button>
	 *
	 * <!-- With loading state -->
	 * <Button loading={isLoading} disabled={isLoading}>
	 *   {isLoading ? 'Processing...' : 'Submit'}
	 * </Button>
	 *
	 * <!-- As link -->
	 * <Button href="/dashboard" variant="secondary">
	 *   Go to Dashboard
	 * </Button>
	 *
	 * <!-- Full width with danger variant -->
	 * <Button variant="danger" fullWidth on:click={deleteItem}>
	 *   Delete Item
	 * </Button>
	 * ```
	 *
	 * @see Card - For container-style clickable elements
	 * @see ErrorMessage - For error state messaging
	 */

	/**
	 * Visual style variant of the button
	 * @type {'primary' | 'secondary' | 'ghost' | 'outline' | 'danger'}
	 * @default 'primary'
	 */
	export let variant: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' = 'primary';

	/**
	 * Size of the button
	 * @type {'sm' | 'md' | 'lg'}
	 * @default 'md'
	 */
	export let size: 'sm' | 'md' | 'lg' = 'md';

	/**
	 * Whether the button is disabled
	 * @type {boolean}
	 * @default false
	 */
	export let disabled: boolean = false;

	/**
	 * Whether the button is in a loading state (shows spinner)
	 * @type {boolean}
	 * @default false
	 */
	export let loading: boolean = false;

	/**
	 * Whether the button should take full width of container
	 * @type {boolean}
	 * @default false
	 */
	export let fullWidth: boolean = false;

	/**
	 * HTML button type attribute (only applies when rendered as button)
	 * @type {'button' | 'submit' | 'reset'}
	 * @default 'button'
	 */
	export let type: 'button' | 'submit' | 'reset' = 'button';

	/**
	 * When provided, renders as a link instead of button
	 * @type {string}
	 * @optional
	 */
	export let href: string | undefined = undefined;

	import { classBuilder } from '$lib/design-system';

	$: buttonClass = [
		classBuilder.button(variant, size, fullWidth),
		disabled || loading ? 'opacity-50 cursor-not-allowed' : '',
		loading ? 'pointer-events-none' : ''
	]
		.filter(Boolean)
		.join(' ');
</script>

<!--
@slot default - Button content (text, icons, etc.)
@slot {boolean} loading - Current loading state
@slot {boolean} disabled - Current disabled state
@slot {string} variant - Current variant
@slot {string} size - Current size
-->
{#if href && !disabled && !loading}
	<a {href} class={buttonClass} on:click role="button" aria-disabled={disabled} aria-busy={loading}>
		{#if loading}
			<svg
				class="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
				fill="none"
				viewBox="0 0 24 24"
				aria-hidden="true"
			>
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				/>
			</svg>
		{/if}
		<slot {loading} {disabled} {variant} {size} />
	</a>
{:else}
	<button {type} {disabled} class={buttonClass} on:click aria-busy={loading}>
		{#if loading}
			<svg
				class="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
				fill="none"
				viewBox="0 0 24 24"
				aria-hidden="true"
			>
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				/>
			</svg>
		{/if}
		<slot {loading} {disabled} {variant} {size} />
	</button>
{/if}
