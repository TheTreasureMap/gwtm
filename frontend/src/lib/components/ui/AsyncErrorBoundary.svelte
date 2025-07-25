<script lang="ts">
	import { onMount } from 'svelte';
	import ErrorBoundary from './ErrorBoundary.svelte';
	import LoadingSpinner from './LoadingSpinner.svelte';

	export let loadingText: string = 'Loading...';
	export let errorFallback: string = 'Failed to load data. Please try again.';
	export let asyncFunction: (() => Promise<void>) | undefined = undefined;
	export let autoLoad: boolean = true;
	export let showRetry: boolean = true;

	let errorBoundary: ErrorBoundary;
	let loading = false;
	let loaded = false;

	async function executeAsync() {
		if (!asyncFunction) return;

		loading = true;

		try {
			await asyncFunction();
			loaded = true;
		} catch (error) {
			console.error('AsyncErrorBoundary caught async error:', error);
			errorBoundary?.captureError(
				error instanceof Error ? error : new Error(String(error)),
				'Async operation failed'
			);
		} finally {
			loading = false;
		}
	}

	function handleRetry() {
		loaded = false;
		executeAsync();
	}

	onMount(() => {
		if (autoLoad && asyncFunction) {
			executeAsync();
		}
	});

	// Expose load function for manual triggering
	export function load() {
		executeAsync();
	}
</script>

<ErrorBoundary
	bind:this={errorBoundary}
	fallback={errorFallback}
	{showRetry}
	on:retry={handleRetry}
	let:captureError
	let:reset
>
	{#if loading}
		<LoadingSpinner text={loadingText} />
	{:else if loaded || !asyncFunction}
		<slot {captureError} {reset} {executeAsync} />
	{:else}
		<!-- Initial state, waiting to load -->
		<div class="text-center py-8 text-gray-500">
			<button
				on:click={executeAsync}
				class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
			>
				Load Data
			</button>
		</div>
	{/if}
</ErrorBoundary>
