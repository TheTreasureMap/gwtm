<script lang="ts">
	/**
	 * @component LoadingSpinner
	 * @description A customizable loading spinner component with optional text message
	 * @category Feedback
	 * @version 1.1.0
	 * @author GWTM Team
	 * @since 2024-01-15
	 *
	 * @accessibility
	 * - Uses aria-label for screen reader accessibility
	 * - Semantic role="status" for loading announcements
	 * - Hidden from screen readers when decorative
	 * - Proper color contrast with blue spinner
	 *
	 * @performance
	 * - CSS-based animation for smooth performance
	 * - Minimal DOM footprint with single element spinner
	 * - No JavaScript animation overhead
	 *
	 * @example
	 * ```svelte
	 * <!-- Basic spinner -->
	 * <LoadingSpinner />
	 *
	 * <!-- With custom message -->
	 * <LoadingSpinner message="Loading instruments..." />
	 *
	 * <!-- Different sizes -->
	 * <LoadingSpinner size="sm" />
	 * <LoadingSpinner size="lg" message="Processing large dataset..." />
	 *
	 * <!-- Inline spinner (not centered) -->
	 * <LoadingSpinner size="sm" centered={false} />
	 *
	 * <!-- With custom content slot -->
	 * <LoadingSpinner message="Loading...">
	 *   <Button variant="secondary" on:click={cancel}>Cancel</Button>
	 * </LoadingSpinner>
	 * ```
	 *
	 * @see AsyncErrorBoundary - For loading states with error handling
	 * @see Button - For loading button states
	 */

	/**
	 * Size of the spinner
	 * @type {'sm' | 'md' | 'lg' | 'xl'}
	 * @default 'md'
	 */
	export let size: 'sm' | 'md' | 'lg' | 'xl' = 'md';

	/**
	 * Optional message to display below the spinner
	 * @type {string}
	 * @default ''
	 * @optional
	 */
	export let message: string = '';

	/**
	 * Whether to center the spinner in its container
	 * @type {boolean}
	 * @default true
	 */
	export let centered: boolean = true;

	const sizeClasses = {
		sm: 'h-4 w-4',
		md: 'h-8 w-8',
		lg: 'h-16 w-16',
		xl: 'h-32 w-32'
	};

	$: spinnerClass = `animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses[size]}`;
	$: containerClass = centered ? 'flex justify-center items-center py-12' : '';
</script>

<!--
@slot default - Additional content to display below the spinner and message
@slot {string} message - Current message text
@slot {string} size - Current spinner size
@slot {boolean} centered - Whether spinner is centered
-->
<div class={containerClass}>
	<div class="text-center" role="status" aria-live="polite">
		<div
			class={spinnerClass}
			aria-label={message || 'Loading'}
			aria-hidden={!message && $$slots.default ? 'true' : 'false'}
		></div>
		{#if message}
			<p class="mt-2 text-gray-600" id="loading-message">
				{message}
			</p>
		{/if}
		<slot {message} {size} {centered} />
	</div>
</div>
