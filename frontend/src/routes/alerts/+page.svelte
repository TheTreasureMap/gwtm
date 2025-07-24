<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { gwtmApi, type GWAlertSchema } from '$lib/api.js';
	import SkyVisualization from '$lib/components/visualization/SkyVisualization.svelte';

	// Props from URL parameters
	let graceid = '';
	let pointingStatus = 'completed';
	let alertType = '';
	let renormPath = '';

	// Component state
	let alert: GWAlertSchema | null = null;
	let loading = true;
	let error = '';
	let alertExists = false;

	// Parse URL parameters
	$: {
		graceid = $page.url.searchParams.get('graceids') || '';
		pointingStatus = $page.url.searchParams.get('pointing_status') || 'completed';
		alertType = $page.url.searchParams.get('alert_type') || '';
		renormPath = $page.url.searchParams.get('normed_path') || '';
	}

	// Load alert data when graceid changes
	$: if (graceid && graceid !== 'None') {
		loadAlert();
	} else {
		alert = null;
		alertExists = false;
		loading = false;
	}

	async function loadAlert() {
		if (!graceid || graceid === 'None') return;

		loading = true;
		error = '';

		try {
			// Query for the specific alert
			const alertsResponse = await gwtmApi.queryAlerts({ graceid });

			if (alertsResponse.alerts && alertsResponse.alerts.length > 0) {
				alert = alertsResponse.alerts[0];
				alertExists = true;
			} else {
				alert = null;
				alertExists = false;
			}
		} catch (err) {
			console.error('Failed to load alert:', err);
			error = 'Failed to load alert data';
			alert = null;
			alertExists = false;
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		console.log('Alerts page onMount:', { graceid });
		console.log('External scripts availability:', {
			jQuery: typeof (window as any).$ !== 'undefined',
			Aladin: typeof (window as any).A !== 'undefined',
			Plotly: typeof (window as any).Plotly !== 'undefined'
		});

		if (graceid && graceid !== 'None') {
			loadAlert();
		} else {
			loading = false;
		}
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

<div class="container mx-auto px-4 py-2">
	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div class="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
		</div>
	{:else if error}
		<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
			<strong class="font-bold">Error:</strong>
			<span class="block sm:inline">{error}</span>
		</div>
	{:else if alertExists && alert}
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
		<div class="bg-white shadow-lg rounded-lg p-6">
			<SkyVisualization {graceid} {alert} {pointingStatus} selectedAlertType={alertType} />
		</div>
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
				Use the URL parameter <code class="bg-gray-100 px-2 py-1 rounded">?graceids=GRACEID</code> to
				specify an event.
			</p>
		</div>
	{/if}
</div>

<style>
	/* Custom styles for the alerts page */
	.container {
		max-width: 1200px;
	}

	code {
		font-family: 'Courier New', monospace;
	}
</style>
