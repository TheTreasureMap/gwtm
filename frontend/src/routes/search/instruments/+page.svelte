<script lang="ts">
	import { api, type InstrumentSchema } from '$lib/api';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import Table from '$lib/components/ui/Table.svelte';
	import LoadingState from '$lib/components/ui/LoadingState.svelte';
	import { errorHandler } from '$lib/utils/errorHandling';

	// Form state
	let searchName: string = '';
	let selectedType: string = 'all';
	
	// Results state
	let searchResults: InstrumentSchema[] = [];
	let isSearching = false;
	let hasSearched = false;

	// Instrument type options (matching Flask enum)
	const instrumentTypeOptions = [
		{ value: 'all', label: 'All Types' },
		{ value: '1', label: 'Photometric' },
		{ value: '2', label: 'Spectroscopic' }
	];

	// Table configuration
	const columns = [
		{
			key: 'id',
			label: 'ID',
			sortable: true,
			width: '80px'
		},
		{
			key: 'instrument_name',
			label: 'Instrument Name',
			sortable: true
		},
		{
			key: 'nickname',
			label: 'Short Name',
			sortable: true
		},
		{
			key: 'instrument_type',
			label: 'Type',
			sortable: true,
			width: '150px'
		}
	];

	// Transform instrument type number to readable name
	function getInstrumentTypeName(type: number): string {
		switch (type) {
			case 1:
				return 'Photometric';
			case 2:
				return 'Spectroscopic';
			default:
				return 'Unknown';
		}
	}

	// Transform data for table display
	$: tableData = searchResults.map((instrument) => ({
		...instrument,
		instrument_type_name: getInstrumentTypeName(instrument.instrument_type),
		nickname: instrument.nickname || '—'
	}));

	async function handleSearch() {
		if (!searchName.trim() && selectedType === 'all') {
			errorHandler.showToast('Please enter an instrument name or select a type to search.', { type: 'warning' });
			return;
		}

		isSearching = true;
		hasSearched = true;

		try {
			// Build search filters (matching Flask logic)
			const filters: any = {};

			// Name filter (partial match like Flask's ilike)
			if (searchName.trim()) {
				filters.name = searchName.trim();
			}

			// Type filter
			if (selectedType !== 'all') {
				filters.type = parseInt(selectedType);
			}

			console.log('Searching instruments with filters:', filters);
			searchResults = await api.instruments.getInstruments(filters);
			
			console.log(`Found ${searchResults.length} instruments`);
		} catch (error) {
			console.error('Error searching instruments:', error);
			errorHandler.showToast('Failed to search instruments. Please try again.', { type: 'error' });
			searchResults = [];
		} finally {
			isSearching = false;
		}
	}

	function handleReset() {
		searchName = '';
		selectedType = 'all';
		searchResults = [];
		hasSearched = false;
	}
</script>

<svelte:head>
	<title>Search Instruments - GWTM</title>
	<meta name="description" content="Search and browse registered instruments in the GWTM database" />
</svelte:head>

<PageContainer>
	<!-- Header -->
	<div class="mb-8">
		<PageHeader
			title="Search Instruments"
			description="Search and browse instruments registered in the database."
		/>
	</div>

	<!-- Search Form -->
	<Card class="mb-8">
		<h3 class="text-lg font-semibold text-gray-900 mb-6">Search Filters</h3>
		
		<form on:submit|preventDefault={handleSearch} class="space-y-4">
			<div class="grid md:grid-cols-2 gap-4">
				<!-- Instrument Name -->
				<FormField
					label="Instrument Name"
					id="search-name"
					type="text"
					bind:value={searchName}
					placeholder="e.g., ZTF, Swift, GOTO..."
					help="Search by instrument name or nickname (case-insensitive, partial matches)"
				/>

				<!-- Instrument Type -->
				<FormField
					label="Instrument Type"
					id="search-type"
					type="select"
					bind:value={selectedType}
					options={instrumentTypeOptions}
					help="Filter by instrument type"
				/>
			</div>

			<!-- Action buttons -->
			<div class="flex gap-4 pt-4">
				<Button
					type="submit"
					loading={isSearching}
					disabled={isSearching}
				>
					<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					{isSearching ? 'Searching...' : 'Search'}
				</Button>
				
				<Button
					type="button"
					variant="secondary"
					on:click={handleReset}
					disabled={isSearching}
				>
					<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
					Reset
				</Button>
			</div>
		</form>
	</Card>

	<!-- Search Results -->
	{#if hasSearched}
		<Card>
			<div class="flex items-center justify-between mb-6">
				<h3 class="text-lg font-semibold text-gray-900">
					Search Results
					{#if !isSearching}
						<span class="text-sm font-normal text-gray-600">
							({searchResults.length} instrument{searchResults.length !== 1 ? 's' : ''} found)
						</span>
					{/if}
				</h3>
			</div>

			{#if isSearching}
				<LoadingState message="Searching instruments..." />
			{:else}
				<Table
					data={tableData}
					{columns}
					loading={false}
					sortable={true}
					emptyMessage="No instruments found matching your search criteria."
				>
					<!-- Custom cell rendering -->
					<svelte:fragment slot="cell" let:item let:column>
						{#if column.key === 'instrument_name'}
							<a
								href="/instrument/{item.id}"
								class="text-blue-600 hover:text-blue-800 hover:underline font-medium"
							>
								{item.instrument_name}
							</a>
						{:else if column.key === 'instrument_type'}
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
								{getInstrumentTypeName(item.instrument_type)}
							</span>
						{:else if column.key === 'nickname'}
							<span class="text-gray-600">
								{item.nickname || '—'}
							</span>
						{:else}
							{item[column.key] || '—'}
						{/if}
					</svelte:fragment>
				</Table>
			{/if}
		</Card>
	{/if}

	<!-- Quick Actions -->
	<div class="grid md:grid-cols-2 gap-6 mt-8">
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

		<Card>
			<h3 class="text-xl font-semibold mb-4 flex items-center">
				<svg
					class="w-6 h-6 mr-2 text-purple-600"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
					/>
				</svg>
				Reporting Instruments
			</h3>
			<p class="text-gray-600 mb-4">
				View instruments that have reported completed pointings for GW events.
			</p>
			<a
				href="/alerts/reporting"
				class="inline-block bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition-colors"
			>
				View Reporting →
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