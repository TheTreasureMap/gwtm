<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { gwtmApi, type GWAlertSchema } from '$lib/api.js';
	import SkyVisualization from '$lib/components/visualization/SkyVisualization.svelte';
	import AlertSelector from '$lib/components/visualization/AlertSelector.svelte';

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
	<meta name="description" content="Gravitational wave alerts visualization and telescope pointing coordination" />
</svelte:head>

<div class="container mx-auto px-4 py-6">
	<!-- Alert Selector -->
	<AlertSelector currentGraceid={graceid} />

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
		<div class="mb-6">
			<h1 class="text-3xl font-bold text-gray-900 mb-2">
				Gravitational Wave Localization and Pointings: {graceid}
				<a 
					href={getGraceDbUrl(graceid)} 
					target="_blank" 
					rel="noopener noreferrer"
					class="text-blue-600 hover:text-blue-800 text-lg font-normal ml-2"
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
						This is a test event. These events and pointings are automatically deleted every 48 hours
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

		<!-- Alert Information Panel -->
		<div class="bg-white shadow-lg rounded-lg p-6 mb-6">
			<h2 class="text-xl font-semibold text-gray-800 mb-4">Alert Information</h2>
			
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#if alert.role}
					<div>
						<span class="font-medium text-gray-600">Role:</span>
						<span class="ml-2 text-gray-900">{alert.role}</span>
					</div>
				{/if}
				
				{#if alert.alert_type}
					<div>
						<span class="font-medium text-gray-600">Alert Type:</span>
						<span class="ml-2 text-gray-900">{alert.alert_type}</span>
					</div>
				{/if}
				
				{#if alert.time_of_signal}
					<div>
						<span class="font-medium text-gray-600">Time of Signal:</span>
						<span class="ml-2 text-gray-900">{new Date(alert.time_of_signal).toLocaleString()}</span>
					</div>
				{/if}
				
				{#if alert.detectors}
					<div>
						<span class="font-medium text-gray-600">Detectors:</span>
						<span class="ml-2 text-gray-900">{alert.detectors}</span>
					</div>
				{/if}
				
				{#if alert.distance}
					<div>
						<span class="font-medium text-gray-600">Distance:</span>
						<span class="ml-2 text-gray-900">{alert.distance.toFixed(1)} ± {alert.distance_error?.toFixed(1) || 'N/A'} Mpc</span>
					</div>
				{/if}
				
				{#if alert.far}
					<div>
						<span class="font-medium text-gray-600">FAR:</span>
						<span class="ml-2 text-gray-900">{alert.far.toExponential(2)} Hz</span>
					</div>
				{/if}
				
				{#if alert.area_50}
					<div>
						<span class="font-medium text-gray-600">50% Area:</span>
						<span class="ml-2 text-gray-900">{alert.area_50.toFixed(1)} deg²</span>
					</div>
				{/if}
				
				{#if alert.area_90}
					<div>
						<span class="font-medium text-gray-600">90% Area:</span>
						<span class="ml-2 text-gray-900">{alert.area_90.toFixed(1)} deg²</span>
					</div>
				{/if}
			</div>
			
			{#if alert.description}
				<div class="mt-4">
					<span class="font-medium text-gray-600">Description:</span>
					<p class="mt-1 text-gray-900">{alert.description}</p>
				</div>
			{/if}
		</div>

		<!-- Classification Probabilities -->
		{#if alert.prob_bns || alert.prob_nsbh || alert.prob_bbh || alert.prob_terrestrial}
			<div class="bg-white shadow-lg rounded-lg p-6 mb-6">
				<h2 class="text-xl font-semibold text-gray-800 mb-4">Classification Probabilities</h2>
				
				<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
					{#if alert.prob_bns}
						<div class="text-center">
							<div class="text-2xl font-bold text-blue-600">{(alert.prob_bns * 100).toFixed(1)}%</div>
							<div class="text-sm text-gray-600">BNS</div>
						</div>
					{/if}
					
					{#if alert.prob_nsbh}
						<div class="text-center">
							<div class="text-2xl font-bold text-green-600">{(alert.prob_nsbh * 100).toFixed(1)}%</div>
							<div class="text-sm text-gray-600">NSBH</div>
						</div>
					{/if}
					
					{#if alert.prob_bbh}
						<div class="text-center">
							<div class="text-2xl font-bold text-purple-600">{(alert.prob_bbh * 100).toFixed(1)}%</div>
							<div class="text-sm text-gray-600">BBH</div>
						</div>
					{/if}
					
					{#if alert.prob_terrestrial}
						<div class="text-center">
							<div class="text-2xl font-bold text-red-600">{(alert.prob_terrestrial * 100).toFixed(1)}%</div>
							<div class="text-sm text-gray-600">Terrestrial</div>
						</div>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Visualization Container -->
		<div class="bg-white shadow-lg rounded-lg p-6">
			<h2 class="text-xl font-semibold text-gray-800 mb-4">Sky Localization and Telescope Pointings</h2>
			
			<SkyVisualization 
				{graceid} 
				{alert} 
				{pointingStatus}
			/>
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
				Use the URL parameter <code class="bg-gray-100 px-2 py-1 rounded">?graceids=GRACEID</code> to specify an event.
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