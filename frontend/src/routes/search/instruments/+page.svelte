<script lang="ts">
	import { api, type InstrumentSchema } from '$lib/api';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Form from '$lib/components/forms/Form.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import Table from '$lib/components/ui/Table.svelte';
	import LoadingState from '$lib/components/ui/LoadingState.svelte';
	import QuickActionCard from '$lib/components/ui/QuickActionCard.svelte';
	import BackLink from '$lib/components/ui/BackLink.svelte';

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

	async function handleSearch(_: Record<string, unknown>) {
		if (!searchName.trim() && selectedType === 'all') {
			return {
				success: false,
				error: 'Please enter an instrument name or select a type to search.'
			};
		}

		isSearching = true;
		hasSearched = true;

		try {
			// Build search filters (matching Flask logic)
			const filters: Record<string, unknown> = {};

			// Name filter (partial match like Flask's ilike)
			if (searchName.trim()) {
				filters.name = searchName.trim();
			}

			// Type filter
			if (selectedType !== 'all') {
				filters.type = parseInt(selectedType);
			}

			searchResults = await api.instruments.getInstruments(filters);
			return { success: true };
		} catch (_error) {
			searchResults = [];
			return { success: false, error: 'Failed to search instruments. Please try again.' };
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
	<meta
		name="description"
		content="Search and browse registered instruments in the GWTM database"
	/>
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

		<Form onSubmit={handleSearch} submitText="Search">
			<div class="grid md:grid-cols-2 gap-4">
				<!-- Instrument Name -->
				<FormField
					name="search-name"
					label="Instrument Name"
					id="search-name"
					type="text"
					bind:value={searchName}
					placeholder="e.g., ZTF, Swift, GOTO..."
					helpText="Search by instrument name or nickname (case-insensitive, partial matches)"
				/>

				<!-- Instrument Type -->
				<FormField
					name="search-type"
					label="Instrument Type"
					id="search-type"
					type="select"
					bind:value={selectedType}
					options={instrumentTypeOptions}
					helpText="Filter by instrument type"
				/>
			</div>

			<!-- Custom action buttons -->
			<svelte:fragment slot="footer" let:isSubmitting>
				<div class="flex gap-4 pt-4">
					<Button type="submit" loading={isSubmitting} disabled={isSubmitting}>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
							/>
						</svg>
						{isSubmitting ? 'Searching...' : 'Search'}
					</Button>

					<Button type="button" variant="secondary" on:click={handleReset} disabled={isSubmitting}>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
							/>
						</svg>
						Reset
					</Button>
				</div>
			</svelte:fragment>
		</Form>
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
							<span class="badge badge-ghost">{getInstrumentTypeName(item.instrument_type)}</span>
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
		<QuickActionCard
			title="Submit New Instrument"
			description="Register your telescope or instrument for GW follow-up coordination."
			href="/submit/instrument"
			linkText="Submit Instrument"
			btnClass="btn btn-success"
		>
			<svg
				slot="icon"
				class="w-6 h-6 mr-2 text-green-600"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
		</QuickActionCard>

		<QuickActionCard
			title="Reporting Instruments"
			description="View instruments that have reported completed pointings for GW events."
			href="/alerts/reporting"
			linkText="View Reporting"
			btnClass="btn btn-secondary"
		>
			<svg
				slot="icon"
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
		</QuickActionCard>
	</div>

	<!-- Back Navigation -->
	<BackLink href="/alerts/select">Back to GW Events</BackLink>
</PageContainer>
