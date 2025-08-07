<script lang="ts">
	import { onMount } from 'svelte';
	import FilterManagementService from '$lib/components/alerts/services/FilterManagementService.svelte';
	import AlertSearchService from '$lib/components/alerts/services/AlertSearchService.svelte';
	import AlertDataService from '$lib/components/alerts/services/AlertDataService.svelte';
	import PaginationService from '$lib/components/alerts/services/PaginationService.svelte';
	import SearchFiltersForm from '$lib/components/alerts/SearchFiltersForm.svelte';
	import AlertResultsTable from '$lib/components/alerts/AlertResultsTable.svelte';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';

	// Service component references
	let filterService: FilterManagementService;
	let searchService: AlertSearchService;
	let dataService: AlertDataService;
	let paginationService: PaginationService;

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

	// Event handlers for form integration
	function handleSearchInputChange(event: CustomEvent) {
		const target = event.detail.event.target as HTMLInputElement;
		filters.graceid = target.value;
		filterService.updateFilter('graceid', target.value);
		searchService.handleSearchInput(target.value);
	}

	function handleSuggestionSelect(event: CustomEvent) {
		const suggestion = event.detail.suggestion;
		filters.graceid = suggestion;
		filterService.updateFilter('graceid', suggestion);
		searchService.selectSuggestion(suggestion);
		handleSearch();
	}

	function handlePerPageChange(event: CustomEvent) {
		const target = event.detail.event.target as HTMLSelectElement;
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

<PageContainer>
	<!-- Header -->
	<div class="mb-8">
		<PageHeader
			title="Gravitational Wave Events"
			description="Search and browse gravitational wave events and telescope observations"
		/>
	</div>

	<!-- Search Filters Form -->
	<SearchFiltersForm
		bind:filters
		bind:filterOptions
		bind:filterOptionsLoading
		bind:searchSuggestions
		bind:showSuggestions
		hideSuggestions={() => searchService.hideSuggestions()}
		showSuggestionsIfReady={(value) => searchService.showSuggestionsIfReady(value)}
		on:filter-change={handleFilterChange}
		on:has-pointings-change={handleHasPointingsChange}
		on:search-input-change={handleSearchInputChange}
		on:suggestion-select={handleSuggestionSelect}
		on:search={handleSearch}
		on:clear-filters={clearFilters}
	/>

	<!-- Alert Results Table -->
	<AlertResultsTable
		bind:loading
		bind:error
		bind:groupedAlerts
		bind:totalItems
		bind:totalPages
		bind:currentPage
		bind:perPage
		bind:hasNext
		bind:hasPrev
		getAlertTypeBadges={(alertTypes) => dataService.getAlertTypeBadges(alertTypes)}
		getDisplayPages={() => paginationService.getDisplayPages()}
		prevPage={() => paginationService.prevPage()}
		nextPage={() => paginationService.nextPage()}
		goToPage={(page) => paginationService.goToPage(page)}
		on:per-page-change={handlePerPageChange}
	/>
</PageContainer>
