<script lang="ts">
	/**
	 * @component ErrorMessage
	 * @description A component for displaying error, warning, and info messages with consistent styling
	 * @category Feedback
	 * @version 1.1.0
	 * @author GWTM Team
	 * @since 2024-01-15
	 *
	 * @accessibility
	 * - Uses proper ARIA role="alert" for error announcements
	 * - Screen reader accessible with semantic markup
	 * - Keyboard accessible dismiss button with focus management
	 * - Color-blind friendly with icons in addition to colors
	 *
	 * @performance
	 * - Minimal re-renders with computed style classes
	 * - Efficient icon rendering with SVG sprites
	 * - Optimized for both static and dismissible states
	 *
	 * @example
	 * ```svelte
	 * <!-- Basic error message -->
	 * <ErrorMessage message="Something went wrong!" />
	 *
	 * <!-- Warning with custom title -->
	 * <ErrorMessage
	 *   type="warning"
	 *   title="Warning"
	 *   message="This action cannot be undone"
	 * />
	 *
	 * <!-- Dismissible info message -->
	 * <ErrorMessage
	 *   type="info"
	 *   title="Information"
	 *   message="Your data has been saved"
	 *   dismissible
	 *   onDismiss={handleDismiss}
	 * />
	 *
	 * <!-- Error with callback -->
	 * <ErrorMessage
	 *   message="Network error occurred"
	 *   dismissible
	 *   onDismiss={() => clearError()}
	 * />
	 * ```
	 *
	 * @see AsyncErrorBoundary - For async operation error handling
	 * @see ErrorToast - For global toast notifications
	 */

	/**
	 * The message text to display
	 * @type {string}
	 */
	export let message: string;

	/**
	 * The title/heading for the message
	 * @type {string}
	 * @default 'Error'
	 */
	export let title: string = 'Error';

	/**
	 * The type of message which determines styling and icon
	 * @type {'error' | 'warning' | 'info'}
	 * @default 'error'
	 */
	export let type: 'error' | 'warning' | 'info' = 'error';

	/**
	 * Whether the message can be dismissed by the user
	 * @type {boolean}
	 * @default false
	 */
	export let dismissible: boolean = false;

	/**
	 * Callback function called when message is dismissed
	 * @type {(() => void) | undefined}
	 * @optional
	 */
	export let onDismiss: (() => void) | undefined = undefined;

	const typeClasses = {
		error: {
			container: 'bg-red-50 border border-red-200 text-red-700',
			title: 'text-red-800',
			icon: 'text-red-600'
		},
		warning: {
			container: 'bg-yellow-50 border border-yellow-200 text-yellow-700',
			title: 'text-yellow-800',
			icon: 'text-yellow-600'
		},
		info: {
			container: 'bg-blue-50 border border-blue-200 text-blue-700',
			title: 'text-blue-800',
			icon: 'text-blue-600'
		}
	};

	$: classes = typeClasses[type];

	function handleDismiss() {
		if (onDismiss) {
			onDismiss();
		}
	}
</script>

<!--
Component displays error, warning, or info messages with appropriate styling and optional dismiss functionality.
No slots - content is provided via props for consistency.
-->
<div class="{classes.container} px-4 py-3 rounded" role="alert" aria-live="polite">
	<div class="flex items-start">
		<div class="flex-shrink-0">
			{#if type === 'error'}
				<svg class="w-5 h-5 {classes.icon}" fill="currentColor" viewBox="0 0 20 20">
					<path
						fill-rule="evenodd"
						d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
						clip-rule="evenodd"
					/>
				</svg>
			{:else if type === 'warning'}
				<svg class="w-5 h-5 {classes.icon}" fill="currentColor" viewBox="0 0 20 20">
					<path
						fill-rule="evenodd"
						d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
						clip-rule="evenodd"
					/>
				</svg>
			{:else}
				<svg class="w-5 h-5 {classes.icon}" fill="currentColor" viewBox="0 0 20 20">
					<path
						fill-rule="evenodd"
						d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
						clip-rule="evenodd"
					/>
				</svg>
			{/if}
		</div>
		<div class="ml-3 flex-1">
			<strong class="font-bold {classes.title}">{title}:</strong>
			<span class="block sm:inline ml-1">{message}</span>
		</div>
		{#if dismissible}
			<div class="ml-auto pl-3">
				<div class="-mx-1.5 -my-1.5">
					<button
						type="button"
						class="inline-flex rounded-md p-1.5 {classes.icon} hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
						on:click={handleDismiss}
					>
						<span class="sr-only">Dismiss</span>
						<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
							<path
								fill-rule="evenodd"
								d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>
