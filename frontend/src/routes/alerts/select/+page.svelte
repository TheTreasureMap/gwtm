<script lang="ts">
	import { onMount } from 'svelte';
	import FilterManagementService from '$lib/components/alerts/services/FilterManagementService.svelte';
	import AlertSearchService from '$lib/components/alerts/services/AlertSearchService.svelte';
	import AlertDataService from '$lib/components/alerts/services/AlertDataService.svelte';
	import PaginationService from '$lib/components/alerts/services/PaginationService.svelte';

	// Service component references
	let filterService: FilterManagementService;
	let searchService: AlertSearchService;
	let dataService: AlertDataService;
	let paginationService: PaginationService;

	// Component state
	let searchInput: HTMLInputElement;

	// Data state (managed by services)
	let filters = {
		graceid: '',
		alert_type: '',
		role: 'observation',
		observing_run: 'O4',
		far: 'significant',
		has_pointings: false
	};
	let filterOptions: {
		observing_runs: string[];
		roles: string[];
		alert_types: string[];
	} = {
		observing_runs: [],
		roles: [],
		alert_types: []
	};
	let filterOptionsLoading: boolean = true;
	let alerts: any[] = [];
	let groupedAlerts: any[] = [];
	let loading: boolean = true;
	let error: string | null = null;
	let searchSuggestions: string[] = [];
	let showSuggestions: boolean = false;
	let currentPage: number = 1;
	let perPage: number = 25;
	let totalItems: number = 0;
	let totalPages: number = 0;
	let hasNext: boolean = false;
	let hasPrev: boolean = false;

	async function loadAlerts() {
		const params = filterService.buildQueryParams({
			page: currentPage,
			per_page: perPage
		});

		try {
			const result = await dataService.loadAlerts(params);
			paginationService.updatePaginationState(result);
		} catch (err) {
			// Error handling is managed by the service
		}
	}

	function handleSearch() {
		paginationService.resetToFirstPage();
	}

	function clearFilters() {
		filterService.clearFilters();
	}

	// Event handlers for service integration
	function handleFilterChange() {
		paginationService.resetToFirstPage();
		loadAlerts();
	}

	function handleHasPointingsChange() {
		filterService.updateFilter('has_pointings', filters.has_pointings);
		handleFilterChange();
	}

	function handleSearchInputChange(event: Event) {
		const target = event.target as HTMLInputElement;
		filters.graceid = target.value;
		filterService.updateFilter('graceid', target.value);
		searchService.handleSearchInput(target.value);
	}

	function handleSuggestionSelect(suggestion: string) {
		filters.graceid = suggestion;
		filterService.updateFilter('graceid', suggestion);
		searchService.selectSuggestion(suggestion);
		handleSearch();
	}

	function handlePerPageChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		paginationService.changePerPage(parseInt(target.value));
	}

	// Service event handlers
	function handleAlertsLoaded(event: CustomEvent) {
		const { alerts: newAlerts, groupedAlerts: newGroupedAlerts, pagination } = event.detail;
		alerts = newAlerts;
		groupedAlerts = newGroupedAlerts;
		totalItems = pagination.total;
		totalPages = pagination.totalPages;
		hasNext = pagination.hasNext;
		hasPrev = pagination.hasPrev;
		currentPage = pagination.currentPage;
	}

	function handleAlertsError(event: CustomEvent) {
		error = event.detail.error;
	}

	function handleFilterOptionsLoaded(event: CustomEvent) {
		filterOptions = event.detail.filterOptions;
	}

	function handleFiltersUpdated(event: CustomEvent) {
		filters = event.detail.filters;
	}

	function handleSuggestionsUpdated(event: CustomEvent) {
		searchSuggestions = event.detail.suggestions;
		showSuggestions = event.detail.show;
	}

	function handlePageChange(event: CustomEvent) {
		currentPage = event.detail.page;
		perPage = event.detail.perPage;
		loadAlerts();
	}

	onMount(async () => {
		// Apply URL parameters first
		filterService.applyUrlParams();

		// Load filter options
		await filterService.loadFilterOptions();

		// Load alerts with applied filters
		loadAlerts();
	});
</script>

<!-- Service Components -->
<FilterManagementService
	bind:this={filterService}
	bind:filters
	bind:filterOptions
	bind:filterOptionsLoading
	on:filters-updated={handleFiltersUpdated}
	on:filter-options-loaded={handleFilterOptionsLoaded}
	on:filters-cleared={handleFilterChange}
	on:filter-changed={handleFilterChange}
/>

<AlertSearchService
	bind:this={searchService}
	bind:searchSuggestions
	bind:showSuggestions
	{filters}
	on:suggestions-updated={handleSuggestionsUpdated}
	on:suggestion-selected={(e) => handleSuggestionSelect(e.detail.suggestion)}
/>

<AlertDataService
	bind:this={dataService}
	bind:alerts
	bind:groupedAlerts
	bind:loading
	bind:error
	on:alerts-loaded={handleAlertsLoaded}
	on:alerts-error={handleAlertsError}
/>

<PaginationService
	bind:this={paginationService}
	bind:currentPage
	bind:perPage
	bind:totalItems
	bind:totalPages
	bind:hasNext
	bind:hasPrev
	on:page-changed={handlePageChange}
/>

<svelte:head>
	<title>GW Events - GWTM</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-4xl font-bold text-gray-900 mb-4">Gravitational Wave Events</h1>
	</div>

	<!-- Search Filters -->
	<div class="bg-white rounded-lg shadow-lg p-6 mb-6">
		<h2 class="text-xl font-semibold mb-4">Search Filters</h2>

		<!-- First row of filters -->
		<div class="grid md:grid-cols-5 gap-4 mb-4">
			<div>
				<label for="observing_run" class="block text-sm font-medium text-gray-700 mb-2">
					<strong>Observing Run</strong>
				</label>
				<select
					id="observing_run"
					bind:value={filters.observing_run}
					on:change={handleFilterChange}
					disabled={filterOptionsLoading}
					class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
				>
					<option value="all">All</option>
					{#each filterOptions.observing_runs as run}
						<option value={run}>{run}</option>
					{/each}
				</select>
			</div>

			<div>
				<label for="role" class="block text-sm font-medium text-gray-700 mb-2">
					<strong>Role</strong>
				</label>
				<select
					id="role"
					bind:value={filters.role}
					on:change={handleFilterChange}
					disabled={filterOptionsLoading}
					class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
				>
					<option value="all">All</option>
					{#each filterOptions.roles as role}
						<option value={role}>{role.charAt(0).toUpperCase() + role.slice(1)}</option>
					{/each}
				</select>
			</div>

			<div>
				<label for="far" class="block text-sm font-medium text-gray-700 mb-2">
					<strong>FAR</strong>
				</label>
				<select
					id="far"
					bind:value={filters.far}
					on:change={handleFilterChange}
					class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="all">All</option>
					<option value="significant">Significant</option>
					<option value="subthreshold">Subthreshold</option>
				</select>
			</div>

			<div>
				<label class="flex items-center mt-7">
					<input
						type="checkbox"
						bind:checked={filters.has_pointings}
						on:change={handleHasPointingsChange}
						class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
					/>
					<span class="text-sm font-medium text-gray-700"><strong>Has Pointings</strong></span>
				</label>
			</div>

			<div class="flex items-end space-x-2">
				<button
					on:click={handleSearch}
					class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					Search
				</button>
				<button
					on:click={clearFilters}
					class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
				>
					Clear
				</button>
			</div>
		</div>

		<!-- Test alert warning -->
		{#if filters.role === 'test' || filters.role === 'all'}
			<div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
				<p class="text-center text-red-700 font-medium">
					All ingested test alerts (MS...) are deleted within 48 hours
				</p>
			</div>
		{/if}

		<!-- Second row: Search box with autocomplete -->
		<div class="mb-4 relative">
			<p class="text-sm text-gray-600 mb-2">
				Type something in the input field to search for GW Event Names (autocomplete suggestions
				appear after 3+ characters):
			</p>
			<div class="relative">
				<input
					bind:this={searchInput}
					id="search"
					type="text"
					bind:value={filters.graceid}
					on:input={handleSearchInputChange}
					on:blur={() => searchService.hideSuggestions()}
					on:focus={() => searchService.showSuggestionsIfReady(filters.graceid)}
					placeholder="Search for graceid (e.g., S190425z, GW190521)..."
					class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					autocomplete="off"
				/>

				<!-- Autocomplete suggestions dropdown -->
				{#if showSuggestions && searchSuggestions.length > 0}
					<div
						class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto"
					>
						{#each searchSuggestions as suggestion}
							<button
								class="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
								on:click={() => handleSuggestionSelect(suggestion)}
							>
								<span class="text-sm text-gray-900">{suggestion}</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
			<br /><br />
			<p class="text-sm text-gray-600">Click on an alert name to see its visualization</p>
		</div>
	</div>

	<!-- Loading State -->
	{#if loading}
		<div class="text-center py-8">
			<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<p class="mt-2 text-gray-600">Loading alerts...</p>
		</div>
	{/if}

	<!-- Error State -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
			<div class="flex">
				<svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
					<path
						fill-rule="evenodd"
						d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
						clip-rule="evenodd"
					/>
				</svg>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800">Error loading alerts</h3>
					<p class="mt-1 text-sm text-red-700">{error}</p>
				</div>
			</div>
		</div>
	{/if}

	<!-- Results -->
	{#if !loading && !error}
		<div class="bg-white rounded-lg shadow-lg overflow-hidden">
			<div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
				<h2 class="text-xl font-semibold">
					{totalItems} Alert{totalItems !== 1 ? 's' : ''} Found
					{#if totalItems > 0}
						<span class="text-sm font-normal text-gray-600">
							(showing {(currentPage - 1) * perPage + 1}-{Math.min(
								currentPage * perPage,
								totalItems
							)} of {totalItems})
						</span>
					{/if}
				</h2>

				<!-- Per page selector -->
				<div class="flex items-center space-x-2">
					<label for="perPage" class="text-sm text-gray-600">Show:</label>
					<select
						id="perPage"
						bind:value={perPage}
						on:change={handlePerPageChange}
						class="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						<option value={10}>10</option>
						<option value={25}>25</option>
						<option value={50}>50</option>
						<option value={100}>100</option>
					</select>
					<span class="text-sm text-gray-600">per page</span>
				</div>
			</div>

			{#if groupedAlerts.length === 0}
				<div class="text-center py-8">
					<svg
						class="mx-auto h-12 w-12 text-gray-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
					<h3 class="mt-2 text-sm font-medium text-gray-900">No alerts found</h3>
					<p class="mt-1 text-sm text-gray-500">Try adjusting your search filters.</p>
				</div>
			{:else}
				<div class="overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									Alert
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									Classification
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									Distance (Mpc)
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									# Pointings
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							{#each groupedAlerts as groupedAlert}
								<tr class="hover:bg-gray-50">
									<!-- Alert column with name and type badges -->
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="flex items-center space-x-2">
											<div class="text-sm font-medium text-blue-600">
												<a
													href="/alerts?graceids={groupedAlert.alertname}"
													class="hover:text-blue-800"
												>
													{groupedAlert.alertname}
												</a>
											</div>
											<div class="flex space-x-1">
												{#each dataService.getAlertTypeBadges(groupedAlert.alert_types) as badge}
													<span
														class="inline-flex px-1 py-0.5 text-xs font-semibold rounded-full {badge.color}"
													>
														{badge.icon}
													</span>
												{/each}
												{#if groupedAlert.has_icecube}
													<span class="inline-flex items-center">
														<svg
															class="w-4 h-4 text-blue-500"
															fill="currentColor"
															viewBox="0 0 20 20"
														>
															<path
																d="M10 2L3 7v6c0 5.55 3.84 9.74 9 11 5.16-1.26 9-5.45 9-11V7l-7-5z"
															/>
														</svg>
													</span>
												{/if}
											</div>
										</div>
									</td>

									<!-- Classification column -->
									<td class="px-6 py-4 whitespace-nowrap">
										<span class="text-sm text-gray-900">{groupedAlert.classification}</span>
									</td>

									<!-- Distance column -->
									<td class="px-6 py-4 whitespace-nowrap">
										<span class="text-sm text-gray-900">{groupedAlert.distance}</span>
									</td>

									<!-- Pointings count column -->
									<td class="px-6 py-4 whitespace-nowrap">
										<span class="text-sm text-gray-900">{groupedAlert.pcounts}</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}

			<!-- Pagination Controls -->
			{#if totalPages > 1}
				<div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
					<div class="flex items-center space-x-2">
						<button
							on:click={() => paginationService.prevPage()}
							disabled={!hasPrev}
							class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							Previous
						</button>

						<div class="flex items-center space-x-1">
							{#each paginationService.getDisplayPages().pages as page}
								<button
									on:click={() => paginationService.goToPage(page)}
									class="px-3 py-2 border rounded-md text-sm font-medium
                    {page === currentPage
										? 'bg-blue-600 text-white border-blue-600'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
								>
									{page}
								</button>
							{/each}

							{#if totalPages > 5 && currentPage < totalPages - 2}
								<span class="px-2 text-gray-500">...</span>
								<button
									on:click={() => paginationService.goToPage(totalPages)}
									class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
								>
									{totalPages}
								</button>
							{/if}
						</div>

						<button
							on:click={() => paginationService.nextPage()}
							disabled={!hasNext}
							class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							Next
						</button>
					</div>

					<div class="text-sm text-gray-600">
						Page {currentPage} of {totalPages}
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
