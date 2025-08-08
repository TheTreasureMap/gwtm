<!--
SearchFiltersForm.svelte - Alert search filters form component
Extracted from alerts/select/+page.svelte to apply service-oriented architecture patterns.
Handles all filter inputs with autocomplete search functionality.
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';

	// Event dispatcher for form interactions
	const dispatch = createEventDispatcher<{
		'filter-change': {};
		'has-pointings-change': {};
		'search-input-change': { event: Event };
		'suggestion-select': { suggestion: string };
		search: {};
		'clear-filters': {};
	}>();

	// Props
	export let filters: {
		graceid: string;
		alert_type: string;
		role: string;
		observing_run: string;
		far: string;
		has_pointings: boolean;
	};

	export let filterOptions: {
		observing_runs: string[];
		roles: string[];
		alert_types: string[];
	};

	export let filterOptionsLoading: boolean;
	export let searchSuggestions: string[] = [];
	export let showSuggestions: boolean = false;

	// Service functions passed as props
	export let hideSuggestions: () => void;
	export let showSuggestionsIfReady: (value: string) => void;

	// Local component references
	let searchInput: HTMLInputElement;

	// Filter options with proper typing
	const farOptions = [
		{ value: 'all', label: 'All' },
		{ value: 'significant', label: 'Significant' },
		{ value: 'subthreshold', label: 'Subthreshold' }
	];

	// Computed observing run options
	$: observingRunOptions = [
		{ value: 'all', label: 'All' },
		...filterOptions.observing_runs.map((run) => ({ value: run, label: run }))
	];

	// Computed role options
	$: roleOptions = [
		{ value: 'all', label: 'All' },
		...filterOptions.roles.map((role) => ({
			value: role,
			label: role.charAt(0).toUpperCase() + role.slice(1)
		}))
	];

	// Event handlers
	function handleFilterChange() {
		dispatch('filter-change', {});
	}

	function handleHasPointingsChange() {
		dispatch('has-pointings-change', {});
	}

	function handleSearchInputChange(event: Event) {
		dispatch('search-input-change', { event });
	}

	function handleSuggestionSelect(suggestion: string) {
		dispatch('suggestion-select', { suggestion });
	}

	function handleSearch() {
		dispatch('search', {});
	}

	function handleClearFilters() {
		dispatch('clear-filters', {});
	}
</script>

<Card class="mb-6">
	<h2 class="text-xl font-semibold mb-6">Search Filters</h2>

	<form on:submit|preventDefault={handleSearch} class="space-y-6">
		<!-- First row of filters -->
		<div class="grid md:grid-cols-5 gap-4">
			<!-- Observing Run -->
			<FormField
				name="observing_run"
				label="Observing Run"
				id="observing_run"
				type="select"
				bind:value={filters.observing_run}
				options={observingRunOptions}
				disabled={filterOptionsLoading}
				on:change={handleFilterChange}
				required
			/>

			<!-- Role -->
			<FormField
				name="role"
				label="Role"
				id="role"
				type="select"
				bind:value={filters.role}
				options={roleOptions}
				disabled={filterOptionsLoading}
				on:change={handleFilterChange}
				required
			/>

			<!-- FAR -->
			<FormField
				name="far"\n\t\t\t\tlabel="FAR"
				id="far"
				type="select"
				bind:value={filters.far}
				options={farOptions}
				on:change={handleFilterChange}
				required
			/>

			<!-- Has Pointings Checkbox -->
			<div class="flex items-end">
				<label class="flex items-center">
					<input
						type="checkbox"
						bind:checked={filters.has_pointings}
						on:change={handleHasPointingsChange}
						class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
					/>
					<span class="text-sm font-medium text-gray-700"><strong>Has Pointings</strong></span>
				</label>
			</div>

			<!-- Action Buttons -->
			<div class="flex items-end space-x-2">
				<Button type="submit" variant="primary">
					<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
					Search
				</Button>
				<Button type="button" variant="secondary" on:click={handleClearFilters}>
					<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
						/>
					</svg>
					Clear
				</Button>
			</div>
		</div>

		<!-- Test alert warning -->
		{#if filters.role === 'test' || filters.role === 'all'}
			<div class="p-4 bg-red-50 border border-red-200 rounded-lg">
				<p class="text-center text-red-700 font-medium">
					All ingested test alerts (MS...) are deleted within 48 hours
				</p>
			</div>
		{/if}

		<!-- Search box with autocomplete -->
		<div class="relative">
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
					on:blur={() => hideSuggestions()}
					on:focus={() => showSuggestionsIfReady(filters.graceid)}
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
								type="button"
								class="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
								on:click={() => handleSuggestionSelect(suggestion)}
							>
								<span class="text-sm text-gray-900">{suggestion}</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<p class="text-sm text-gray-600 mt-4">Click on an alert name to see its visualization</p>
		</div>
	</form>
</Card>
