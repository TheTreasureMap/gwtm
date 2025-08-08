<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import ErrorMessage from './ErrorMessage.svelte';

	export let fallback: string = 'Something went wrong. Please try again.';
	export let showRetry: boolean = true;
	export let resetOnPropsChange: boolean = true;
	export let onError: ((error: Error) => void) | undefined = undefined;

	let hasError = false;
	let errorMessage = '';
	let errorDetails = '';
	let retryCount = 0;
	const maxRetries = 3;

	const dispatch = createEventDispatcher<{
		error: { error: Error; retry: () => void };
		retry: { count: number };
		reset: {};
	}>();

	export function reset() {
		hasError = false;
		errorMessage = '';
		errorDetails = '';
		dispatch('reset', {});
	}

	export function captureError(error: Error, context?: string) {
		console.error('ErrorBoundary caught error:', error);

		hasError = true;
		errorMessage = error.message || fallback;
		errorDetails = context || '';

		if (onError) {
			onError(error);
		}

		dispatch('error', {
			error,
			retry: () => retry()
		});
	}

	function retry() {
		if (retryCount < maxRetries) {
			retryCount++;
			reset();
			dispatch('retry', { count: retryCount });
		}
	}

	// Reset error state when props change (if enabled)
	$: if (resetOnPropsChange && hasError) {
		reset();
	}

	onMount(() => {
		// Reset retry count on mount
		retryCount = 0;
	});
</script>

{#if hasError}
	<div class="error-boundary" role="alert">
		<ErrorMessage message={errorMessage} title="Something went wrong" type="error" />

		{#if errorDetails}
			<details class="mt-3 text-sm text-gray-600">
				<summary class="cursor-pointer hover:text-gray-800">Technical details</summary>
				<pre class="mt-2 whitespace-pre-wrap bg-gray-50 p-2 rounded text-xs">{errorDetails}</pre>
			</details>
		{/if}

		{#if showRetry && retryCount < maxRetries}
			<div class="mt-4">
				<button
					on:click={retry}
					class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
				>
					Try Again {retryCount > 0 ? `(${retryCount}/${maxRetries})` : ''}
				</button>
			</div>
		{:else if retryCount >= maxRetries}
			<div class="mt-4 text-sm text-gray-600">
				Maximum retry attempts reached. Please refresh the page or contact support.
			</div>
		{/if}
	</div>
{:else}
	<slot {captureError} {reset} />
{/if}

<style>
	.error-boundary {
		min-height: 100px;
		padding: 1rem;
	}
</style>
