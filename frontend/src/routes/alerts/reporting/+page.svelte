<script lang="ts">
	import { onMount } from 'svelte';
	import { gwtmApi, type InstrumentSchema } from '$lib/api';
	import ReportingInstrumentsTable from '$lib/components/tables/ReportingInstrumentsTable.svelte';

	let instruments: InstrumentSchema[] = [];
	let loading = false;
	let error: string | null = null;

	onMount(() => {
		loadReportingInstruments();
	});

	async function loadReportingInstruments() {
		loading = true;
		error = null;

		try {
			instruments = await gwtmApi.getReportingInstruments();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load reporting instruments';
			console.error('Error loading reporting instruments:', err);
		} finally {
			loading = false;
		}
	}

	function handleRefresh() {
		loadReportingInstruments();
	}
</script>

<svelte:head>
	<title>Reporting Instruments - GWTM</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-4xl font-bold text-gray-900 mb-4">Reporting Instruments</h1>
				<p class="text-lg text-gray-600">
					Instruments that have reported completed pointings, ordered by activity level.
				</p>
			</div>
			<button
				on:click={handleRefresh}
				disabled={loading}
				class="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
			>
				<svg
					class="w-4 h-4 mr-2 {loading ? 'animate-spin' : ''}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
					/>
				</svg>
				Refresh
			</button>
		</div>
	</div>

	<!-- Error State -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
			<div class="flex items-center">
				<svg
					class="w-6 h-6 text-red-600 mr-3"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
					/>
				</svg>
				<div>
					<h3 class="text-lg font-semibold text-red-800">Error Loading Reporting Instruments</h3>
					<p class="text-red-700">{error}</p>
					<button
						on:click={handleRefresh}
						class="mt-2 text-sm text-red-600 hover:text-red-800 underline"
					>
						Try again
					</button>
				</div>
			</div>
		</div>
	{:else}
		<!-- Reporting Instruments Table -->
		<ReportingInstrumentsTable {instruments} {loading} />
	{/if}

	<!-- Quick Actions -->
	<div class="grid md:grid-cols-2 gap-6 mt-8">
		<div class="bg-white rounded-lg shadow-lg p-6">
			<h3 class="text-xl font-semibold mb-4 flex items-center">
				<svg
					class="w-6 h-6 mr-2 text-blue-600"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					/>
				</svg>
				Search All Instruments
			</h3>
			<p class="text-gray-600 mb-4">
				Browse and search all registered instruments in the database.
			</p>
			<a
				href="/search/instruments"
				class="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
			>
				Search Instruments →
			</a>
		</div>

		<div class="bg-white rounded-lg shadow-lg p-6">
			<h3 class="text-xl font-semibold mb-4 flex items-center">
				<svg
					class="w-6 h-6 mr-2 text-green-600"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 4v16m8-8H4"
					/>
				</svg>
				Submit New Instrument
			</h3>
			<p class="text-gray-600 mb-4">
				Register your telescope or instrument for GW follow-up coordination.
			</p>
			<a
				href="/submit/instrument"
				class="inline-block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
			>
				Submit Instrument →
			</a>
		</div>
	</div>

	<!-- Back Navigation -->
	<div class="mt-8">
		<a href="/alerts/select" class="inline-flex items-center text-blue-600 hover:text-blue-800">
			<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
			</svg>
			Back to GW Events
		</a>
	</div>
</div>
