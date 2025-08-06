<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api, type GWAlertSchema } from '$lib/api';
	import SkyVisualization from '$lib/components/visualization/SkyVisualization.svelte';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import AsyncErrorBoundary from '$lib/components/ui/AsyncErrorBoundary.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import { errorHandler } from '$lib/utils/errorHandling';

	// Props from URL parameters
	let graceid = '';
	let pointingStatus = 'completed';
	let alertType = '';
	let renormPath = '';

	// Component state
	let alert: (GWAlertSchema & {
		far_human?: string;
		distance_with_error?: string;
		time_coincidence_far_human?: string;
		time_sky_position_coincidence_far_human?: string;
	}) | null = null;
	let alertExists = false;

	// Parse URL parameters
	$: {
		graceid = $page.url.searchParams.get('graceids') || '';
		pointingStatus = $page.url.searchParams.get('pointing_status') || 'completed';
		alertType = $page.url.searchParams.get('alert_type') || '';
		renormPath = $page.url.searchParams.get('normed_path') || '';
	}

	async function loadAlert() {
		if (!graceid || graceid === 'None') {
			alert = null;
			alertExists = false;
			return;
		}

		// Query for ALL alerts with this graceid (matching Flask logic)
		const alertsResponse = await api.alerts.queryAlerts({ graceid });

		if (alertsResponse.alerts && alertsResponse.alerts.length > 0) {
			// Replicate Flask's alert selection logic from forms.py:331-338
			console.log(`Found ${alertsResponse.alerts.length} alerts for ${graceid}`);

			// Filter out retractions and ExtCoinc alerts (like Flask does)
			const cleanedAlerts = alertsResponse.alerts.filter(
				(alert) => alert.alert_type !== 'Retraction' && !alert.alert_type?.includes('ExtCoinc')
			);

			let selectedAlert;
			if (cleanedAlerts.length > 0) {
				// Pick the most recent clean alert (last in chronological order)
				selectedAlert = cleanedAlerts[cleanedAlerts.length - 1];
				console.log(
					`Selected clean alert: ${selectedAlert.alert_type} (${selectedAlert.datecreated})`
				);
			} else {
				// Fallback to first alert if no clean alerts available
				selectedAlert = alertsResponse.alerts[0];
				console.log(`No clean alerts found, using fallback: ${selectedAlert.alert_type}`);
			}

			// Use the FastAPI /ajax_alerttype endpoint to get complete processed data
			// This endpoint provides the same data processing that Flask does
			const urlId = `${selectedAlert.id}_${selectedAlert.alert_type}`;
			
			try {
				const processedData = await api.ajax.getEventContour(urlId);
				
				// Map the processed data back to our alert object
				alert = {
					...selectedAlert,
					// Use processed fields where available
					far_human: processedData.alert_human_far,
					distance_with_error: processedData.alert_distance_plus_error,
					area_50: processedData.alert_area_50,
					area_90: processedData.alert_area_90,
					prob_bns: processedData.alert_prob_bns,
					prob_nsbh: processedData.alert_prob_nsbh,
					prob_gap: processedData.alert_prob_gap,
					prob_bbh: processedData.alert_prob_bbh,
					prob_terrestrial: processedData.alert_prob_terrestrial,
					prob_hasns: processedData.alert_prob_hasns,
					prob_hasremenant: processedData.alert_prob_hasremenant,
					time_coincidence_far_human: processedData.alert_time_coincidence_far,
					time_sky_position_coincidence_far_human: processedData.alert_time_sky_position_coincidence_far
				};
				console.log('Using processed alert data from FastAPI /ajax_alerttype endpoint');
			} catch (error) {
				console.warn('Error calling /ajax_alerttype endpoint, using basic processing:', error);
				alert = processAlertData(selectedAlert);
			}
			
			alertExists = true;
		} else {
			alert = null;
			alertExists = false;
		}
	}

	/**
	 * Process alert data to match Flask's processing logic
	 * Replicates the data transformation from forms.py:343-380
	 */
	function processAlertData(rawAlert: GWAlertSchema): GWAlertSchema {
		const processed = { ...rawAlert };

		// Round numerical values to match Flask precision
		if (processed.area_50 !== null && processed.area_50 !== undefined) {
			processed.area_50 = Math.round(processed.area_50 * 1000) / 1000; // 3 decimal places
		}
		if (processed.area_90 !== null && processed.area_90 !== undefined) {
			processed.area_90 = Math.round(processed.area_90 * 1000) / 1000; // 3 decimal places
		}
		if (processed.distance !== null && processed.distance !== undefined) {
			processed.distance = Math.round(processed.distance * 1000) / 1000; // 3 decimal places
		}
		if (processed.distance_error !== null && processed.distance_error !== undefined) {
			processed.distance_error = Math.round(processed.distance_error * 1000) / 1000; // 3 decimal places
		}

		// Round probability values to match Flask (5 decimal places)
		const probFields = [
			'prob_bns',
			'prob_nsbh',
			'prob_gap',
			'prob_bbh',
			'prob_terrestrial',
			'prob_hasns',
			'prob_hasremenant'
		];
		probFields.forEach((field) => {
			if (processed[field] !== null && processed[field] !== undefined) {
				processed[field] = Math.round(processed[field] * 100000) / 100000; // 5 decimal places
			}
		});

		console.log('Processed alert data:', processed);
		return processed;
	}

	onMount(() => {
		console.log('Alerts page onMount:', { graceid });
		console.log('External scripts availability:', {
			jQuery: typeof (window as any).$ !== 'undefined',
			Aladin: typeof (window as any).A !== 'undefined',
			Plotly: typeof (window as any).Plotly !== 'undefined'
		});
	});

	function isRetracted(alert: GWAlertSchema): boolean {
		return alert.alert_type?.toLowerCase().includes('retraction') || false;
	}

	function isTestEvent(graceid: string): boolean {
		return graceid.startsWith('MS');
	}

	function getGraceDbUrl(graceid: string): string {
		return `https://gracedb.ligo.org/superevents/${graceid}/view/`;
	}
</script>

<svelte:head>
	<title>Gravitational Wave Alerts - GWTM</title>
	<meta
		name="description"
		content="Gravitational wave alerts visualization and telescope pointing coordination"
	/>
</svelte:head>

<PageContainer padding="sm">
	<AsyncErrorBoundary
		asyncFunction={graceid && graceid !== 'None' ? loadAlert : undefined}
		loadingText="Loading gravitational wave alert..."
		errorFallback="Failed to load alert data. Please check the Grace ID and try again."
		autoLoad={graceid && graceid !== 'None'}
		let:captureError
	>
		{#if alertExists && alert}
			<!-- Alert Header -->
			<div class="mb-3">
				<h1 class="text-xl font-bold text-gray-900 mb-1">
					Gravitational Wave Localization and Pointings: {graceid}
					<a
						href={getGraceDbUrl(graceid)}
						target="_blank"
						rel="noopener noreferrer"
						class="text-blue-600 hover:text-blue-800 text-sm font-normal ml-2"
					>
						[GraceDB]
					</a>
				</h1>

				{#if isRetracted(alert)}
					<div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
						<h2 class="text-xl font-bold">⚠️ RETRACTED</h2>
					</div>
				{:else if isTestEvent(graceid)}
					<div class="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
						<h5 class="font-medium">
							This is a test event. These events and pointings are automatically deleted every 48
							hours
						</h5>
					</div>
				{/if}

				{#if graceid === 'S200219ac'}
					<div class="flex space-x-4 mb-4">
						<a
							href="/static/S200219ac_GBM_Event1_healpix.fit"
							download
							class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
						>
							Download GBM HEALPix FITS file
						</a>
						<a
							href="/static/S200219ac_GBM_Event1_skymap.png"
							download
							class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
						>
							Download GBM Skymap png file
						</a>
					</div>
				{/if}
			</div>

			<!-- Visualization Container -->
			<Card>
				<SkyVisualization {graceid} {alert} {pointingStatus} selectedAlertType={alertType} />
			</Card>
		{:else if graceid && graceid !== 'None'}
			<!-- Event not found -->
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
