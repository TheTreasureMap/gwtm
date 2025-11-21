<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { type GWAlertSchema } from '$lib/api';
	import SkyVisualization from '$lib/components/visualization/SkyVisualization.svelte';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import AsyncErrorBoundary from '$lib/components/ui/AsyncErrorBoundary.svelte';
	import Card from '$lib/components/ui/Card.svelte';

	// Service components
	import AlertDataProcessingService from '$lib/components/alerts/services/AlertDataProcessingService.svelte';
	import UrlParameterService from '$lib/components/alerts/services/UrlParameterService.svelte';
	import AlertHeaderComponent from '$lib/components/alerts/AlertHeaderComponent.svelte';

	// Service component references
	let dataProcessingService: AlertDataProcessingService;
	let urlParameterService: UrlParameterService;

	// URL parameters managed by service
	let graceid = '';
	let pointingStatus = 'completed';
	let alertType = '';
	let renormPath = '';

	// Component state
	let alert:
		| (GWAlertSchema & {
				far_human?: string;
				distance_with_error?: string;
				time_coincidence_far_human?: string;
				time_sky_position_coincidence_far_human?: string;
		  })
		| null = null;
	let alertExists = false;
	let alertLoading = false;

	// Initialize URL parameter parsing
	$: {
		urlParameterService?.parseUrlParameters(page);
	}

	// Auto-load alert when graceid becomes available
	$: if (graceid && graceid !== 'None' && dataProcessingService) {
		loadAlert();
	}

	// Alert loading handled by service
	async function loadAlert() {
		if (dataProcessingService && urlParameterService?.hasValidParameters()) {
			await dataProcessingService.loadAlert(graceid);
		} else {
			alert = null;
			alertExists = false;
		}
	}

	// Event handlers for service integration
	function handleParametersUpdated(event: CustomEvent) {
		const params = event.detail;
		graceid = params.graceid;
		pointingStatus = params.pointingStatus;
		alertType = params.alertType;
		renormPath = params.renormPath;

		// Reload alert when parameters change
		loadAlert();
	}

	function handleAlertLoaded(event: CustomEvent) {
		const { alert: loadedAlert, alertExists: exists } = event.detail;
		alert = loadedAlert;
		alertExists = exists;
	}

	function handleAlertCleared() {
		alert = null;
		alertExists = false;
		alertLoading = false;
	}

	function handleAlertError(event: CustomEvent) {
		console.error('Alert loading error:', event.detail.error);
		alert = null;
		alertExists = false;
		alertLoading = false;
	}

	function handleAlertLoadingStart() {
		alertLoading = true;
	}

	function handleAlertLoadingEnd() {
		alertLoading = false;
	}

	onMount(() => {
		console.log('Alerts page onMount:', { graceid });
		console.log('External scripts availability:', {
			jQuery: typeof (window as Record<string, unknown>).$ !== 'undefined',
			Aladin: typeof (window as Record<string, unknown>).A !== 'undefined',
			Plotly: typeof (window as Record<string, unknown>).Plotly !== 'undefined'
		});

		// Load alert on mount if we have valid parameters
		if (urlParameterService?.hasValidParameters()) {
			loadAlert();
		}
	});

	// These utility functions are now handled by AlertStatusService
</script>

<!-- Service Components -->
<AlertDataProcessingService
	bind:this={dataProcessingService}
	on:alert-loaded={handleAlertLoaded}
	on:alert-cleared={handleAlertCleared}
	on:alert-error={handleAlertError}
	on:alert-loading-start={handleAlertLoadingStart}
	on:alert-loading-end={handleAlertLoadingEnd}
/>

<UrlParameterService
	bind:this={urlParameterService}
	bind:graceid
	bind:pointingStatus
	bind:alertType
	bind:renormPath
	on:parameters-updated={handleParametersUpdated}
/>

<svelte:head>
	<title>Gravitational Wave Alerts - GWTM</title>
	<meta
		name="description"
		content="Gravitational wave alerts visualization and telescope pointing coordination"
	/>
</svelte:head>

<PageContainer padding="sm">
	<AsyncErrorBoundary
		loadingText="Loading gravitational wave alert..."
		errorFallback="Failed to load alert data. Please check the Grace ID and try again."
	>
		{#if alertExists && alert}
			<!-- Alert Header Component -->
			<AlertHeaderComponent {graceid} {alert} />

			<!-- Visualization Container -->
			<Card>
				<SkyVisualization {graceid} {alert} {pointingStatus} selectedAlertType={alertType} />
			</Card>
		{:else if alertLoading}
			<!-- Loading state -->
			<div class="text-center py-12">
				<div class="inline-flex items-center">
					<svg
						class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					<h3 class="text-lg font-medium text-gray-900">
						Loading event <span class="text-blue-600 italic">{graceid}</span>...
					</h3>
				</div>
			</div>
		{:else if urlParameterService?.hasValidParameters() && !alertLoading}
			<!-- Event not found (only show if not loading) -->
			<div class="text-center py-12">
				<h3 class="text-2xl font-semibold text-gray-900 mb-2">
					Event <span class="text-red-600 italic">{graceid}</span> does not exist
				</h3>
			</div>
		{:else}
			<!-- No event selected -->
			<div class="text-center py-12">
				<h3 class="text-2xl font-semibold text-gray-600 mb-4">
					Select a gravitational wave event to view its details
				</h3>
				<p class="text-gray-500">
					Use the URL parameter <code class="bg-gray-100 px-2 py-1 rounded">?graceids=GRACEID</code>
					to specify an event.
				</p>
			</div>
		{/if}
	</AsyncErrorBoundary>
</PageContainer>

<style>
	/* Custom styles for the alerts page */

	code {
		font-family: 'Courier New', monospace;
	}
</style>
