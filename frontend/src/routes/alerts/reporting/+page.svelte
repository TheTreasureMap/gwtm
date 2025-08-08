<script lang="ts">
	import { api, type InstrumentSchema } from '$lib/api';
	import ReportingInstrumentsTable from '$lib/components/tables/ReportingInstrumentsTable.svelte';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import AsyncErrorBoundary from '$lib/components/ui/AsyncErrorBoundary.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	let instruments: InstrumentSchema[] = [];

	async function loadReportingInstruments() {
		instruments = await api.instruments.getReportingInstruments();
	}
</script>

<svelte:head>
	<title>Reporting Instruments - GWTM</title>
</svelte:head>

<PageContainer>
	<!-- Header -->
	<div class="mb-8">
		<PageHeader
			title="Reporting Instruments"
			description="Instruments that have reported completed pointings, ordered by activity level."
		/>
	</div>

	<!-- Data Loading with Error Boundary -->
	<AsyncErrorBoundary
		asyncFunction={loadReportingInstruments}
		loadingText="Loading reporting instruments..."
		errorFallback="Failed to load reporting instruments data. Please try again."
		let:executeAsync
	>
		<div class="flex justify-end mb-4">
			<Button on:click={executeAsync} variant="secondary">
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
					/>
				</svg>
				Refresh
			</Button>
		</div>

		<!-- Reporting Instruments Table -->
		<ReportingInstrumentsTable {instruments} loading={false} />
	</AsyncErrorBoundary>

	<!-- Quick Actions -->
	<div class="grid md:grid-cols-2 gap-6 mt-8">
		<Card>
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
		</Card>

		<Card>
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
		</Card>
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
</PageContainer>
