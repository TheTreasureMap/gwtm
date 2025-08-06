<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import LoadingState from '$lib/components/ui/LoadingState.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import PointingsSearchForm from '$lib/components/search/PointingsSearchForm.svelte';
	import DoiRequestPanel from '$lib/components/search/DoiRequestPanel.svelte';
	import PointingsTable from '$lib/components/search/PointingsTable.svelte';

	// State
	let searchResults: any[] = [];
	let selectedPointings: Set<number> = new Set();
	let isSearching = false;
	let hasSearched = false;
	let searchError = '';
	let lastSearchParams: any = null;

	// Handle search form submission
	async function handleSearch(event: CustomEvent) {
		const { graceid, bands, statuses, my_points_only } = event.detail;
		
		isSearching = true;
		searchError = '';
		lastSearchParams = event.detail;

		try {
			const searchParams = {
				graceid,
				bands: bands.length ? bands : undefined,
				statuses: statuses.length ? statuses : undefined,
				my_points_only
			};

			// Get the pointing results (now includes instrument_name and username from API)
			const results = await api.search.searchPointings(searchParams);
			console.log('Search results with joined data:', results);
			
			// Process results to extract RA/DEC if needed
			if (results && results.length > 0) {
				searchResults = results.map(pointing => {
					// Extract ra/dec from position if not already present
					if (pointing.position && !pointing.ra && !pointing.dec) {
						const coords = extractRaDecFromPosition(pointing.position);
						return { ...pointing, ra: coords.ra, dec: coords.dec };
					}
					return pointing;
				});
			} else {
				searchResults = results || [];
			}
			
			hasSearched = true;
			selectedPointings.clear();
			selectedPointings = selectedPointings; // Trigger reactivity
		} catch (err) {
			console.error('Search failed:', err);
			searchError = err instanceof Error ? err.message : 'Search failed. Please try again.';
			searchResults = [];
		} finally {
			isSearching = false;
		}
	}

	function extractRaDecFromPosition(position: string): { ra?: number, dec?: number } {
		// Extract RA/DEC from POINT(ra dec) string
		if (position && position.startsWith('POINT(')) {
			try {
				const coords = position.slice(6, -1); // Remove "POINT(" and ")"
				const [ra, dec] = coords.split(' ').map(Number);
				if (!isNaN(ra) && !isNaN(dec)) {
					return { ra, dec };
				}
			} catch (err) {
				console.warn('Failed to parse position:', position, err);
			}
		}
		return {};
	}

	// Handle DOI request
	async function handleDoiRequest(event: CustomEvent) {
		const { pointing_ids, graceid, doi_group_id, doi_url } = event.detail;

		try {
			const result = await api.search.requestDoi({
				pointing_ids,
				graceid,
				doi_group_id,
				doi_url
			});

			// Update the results table with the new DOI URL
			searchResults = searchResults.map(pointing => {
				if (pointing_ids.includes(pointing.id)) {
					return { ...pointing, doi_url: result.doi_url };
				}
				return pointing;
			});

			// Clear selections
			selectedPointings.clear();
			selectedPointings = selectedPointings;

			// Show success message (you could add a toast notification here)
			alert('DOI request completed successfully');
		} catch (err) {
			console.error('DOI request failed:', err);
			const errorMessage = err instanceof Error ? err.message : 'DOI request failed. Please try again.';
			alert(errorMessage);
		}
	}

	// Handle selection changes from table
	function handleSelectionChange(event: CustomEvent) {
		selectedPointings = event.detail.selectedPointings;
	}
</script>

<svelte:head>
	<title>Search Pointings - GWTM</title>
</svelte:head>

<PageContainer>
	<PageHeader 
		title="Search Pointings"
		description="Search and manage telescope pointing observations for gravitational wave events"
	/>

	<div class="space-y-6">
		<!-- Search Form -->
		<PointingsSearchForm on:search={handleSearch} />

		<!-- Search Error -->
		{#if searchError}
			<ErrorMessage 
				title="Search Error"
				message={searchError}
				type="error"
			/>
		{/if}

		<!-- DOI Request Panel -->
		{#if hasSearched && lastSearchParams?.my_points_only}
			<DoiRequestPanel
				{selectedPointings}
				graceid={lastSearchParams.graceid}
				visible={true}
				on:doi-request={handleDoiRequest}
			/>
		{/if}

		<!-- Loading State -->
		{#if isSearching}
			<div class="bg-white rounded-lg shadow p-8">
				<LoadingState message="Searching pointings..." />
			</div>
		{/if}

		<!-- Results -->
		{#if hasSearched && !isSearching}
			<div class="space-y-4">
				<!-- Results Summary -->
				<div class="bg-white rounded-lg border border-gray-200 px-6 py-4">
					<div class="flex items-center justify-between">
						<h3 class="text-lg font-medium text-gray-900">
							Search Results
						</h3>
						<span class="text-sm text-gray-500">
							{searchResults.length} pointing{searchResults.length === 1 ? '' : 's'} found
						</span>
					</div>
					
					{#if lastSearchParams}
						<div class="mt-2 text-sm text-gray-600">
							<strong>Grace ID:</strong> {lastSearchParams.graceid}
							{#if lastSearchParams.bands.length > 0}
								• <strong>Bands:</strong> {lastSearchParams.bands.join(', ')}
							{/if}
							{#if lastSearchParams.statuses.length > 0}
								• <strong>Status:</strong> {lastSearchParams.statuses.join(', ')}
							{/if}
							{#if lastSearchParams.my_points_only}
								• <strong>My pointings only</strong>
							{/if}
						</div>
					{/if}
				</div>

				<!-- Results Table -->
				<PointingsTable
					pointings={searchResults}
					loading={false}
					allowSelection={lastSearchParams?.my_points_only || false}
					{selectedPointings}
					on:selection-change={handleSelectionChange}
				/>
			</div>
		{/if}

		<!-- Initial State -->
		{#if !hasSearched && !isSearching}
			<div class="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
				<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<h3 class="mt-2 text-sm font-medium text-gray-900">No search performed yet</h3>
				<p class="mt-1 text-sm text-gray-500">
					Select a Grace ID and other filters, then click Search to find pointings.
				</p>
			</div>
		{/if}
	</div>
</PageContainer>