<!--
@component LoadingState
@description A reusable loading state component with consistent styling and customizable content
@category UI Primitives
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<LoadingState message="Loading data..." />
<LoadingState size="large" showSpinner={false} />
<LoadingState>
  <p>Custom loading content</p>
</LoadingState>
```

@prop {string} message - Loading message to display
@prop {'small' | 'medium' | 'large'} size - Size of the loading spinner
@prop {boolean} showSpinner - Whether to show the spinner animation
@prop {boolean} inline - Whether to display inline vs block
@prop {string} class - Additional CSS classes
@prop {string} spinnerClass - Additional CSS classes for spinner

@slot default - Custom content to display instead of message
-->
<script lang="ts">
	/**
	 * Loading message to display
	 * @type {string}
	 * @default 'Loading...'
	 */
	export let message: string = 'Loading...';

	/**
	 * Size of the loading spinner
	 * @type {'small' | 'medium' | 'large'}
	 * @default 'medium'
	 */
	export let size: 'small' | 'medium' | 'large' = 'medium';

	/**
	 * Whether to show the spinner animation
	 * @type {boolean}
	 * @default true
	 */
	export let showSpinner: boolean = true;

	/**
	 * Whether to display inline vs block
	 * @type {boolean}
	 * @default false
	 */
	export let inline: boolean = false;

	/**
	 * Additional CSS classes for the container
	 * @type {string}
	 * @default ''
	 */
	let className: string = '';
	export { className as class };

	/**
	 * Additional CSS classes for the spinner
	 * @type {string}
	 * @default ''
	 */
	export let spinnerClass: string = '';

	// Reactive styles based on props
	$: containerClass = [
		inline ? 'inline-flex' : 'flex',
		'items-center justify-center gap-3',
		inline ? '' : 'flex-col',
		className
	]
		.filter(Boolean)
		.join(' ');

	$: spinnerSize = {
		small: 'h-4 w-4',
		medium: 'h-8 w-8',
		large: 'h-12 w-12'
	}[size];

	$: textSize = {
		small: 'text-sm',
		medium: 'text-base',
		large: 'text-lg'
	}[size];
</script>

<div class={containerClass} role="status" aria-live="polite" aria-label={message}>
	{#if showSpinner}
		<div
			class="animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 {spinnerSize} {spinnerClass}"
			aria-hidden="true"
		></div>
	{/if}

	<div class="text-gray-600 {textSize}">
		<slot>
			{message}
		</slot>
	</div>
</div>

<style>
	/* Ensure smooth animation */
	.animate-spin {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}
</style>
