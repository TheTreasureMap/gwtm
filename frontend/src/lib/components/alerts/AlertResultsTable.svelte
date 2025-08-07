<!--
AlertResultsTable.svelte - Alert search results table component
Extracted from alerts/select/+page.svelte to apply service-oriented architecture patterns.
Displays alert results with badges, pagination, and loading states.
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import LoadingState from '$lib/components/ui/LoadingState.svelte';

	// Event dispatcher for table interactions
	const dispatch = createEventDispatcher<{
		'per-page-change': { event: Event };
		'page-change': { page: number };
	}>();

	// Props
	export let loading: boolean = false;
	export let error: string | null = null;
	export let groupedAlerts: any[] = [];
	export let totalItems: number = 0;
	export let totalPages: number = 0;
	export let currentPage: number = 1;
	export let perPage: number = 25;
	export let hasNext: boolean = false;
	export let hasPrev: boolean = false;

	// Service functions passed as props
	export let getAlertTypeBadges: (alertTypes: string[]) => Array<{ color: string; icon: string }>;
	export let getDisplayPages: () => { pages: number[] };
	export let prevPage: () => void;
	export let nextPage: () => void;
	export let goToPage: (page: number) => void;

	// Per page options
	const perPageOptions = [
		{ value: 10, label: '10' },
		{ value: 25, label: '25' },
		{ value: 50, label: '50' },
		{ value: 100, label: '100' }
	];

	// Event handlers
	function handlePerPageChange(event: Event) {
		dispatch('per-page-change', { event });
	}
</script>

<!-- Loading State -->
{#if loading}
	<LoadingState message="Loading alerts..." />
{/if}

<!-- Error State -->
{#if error}
	<Card class="mb-6">
		<div class="bg-red-50 border border-red-200 rounded-lg p-4">
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
	</Card>
{/if}

<!-- Results Table -->
{#if !loading && !error}
	<Card class="overflow-hidden">
		<!-- Table Header -->
		<div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
			<h2 class="text-xl font-semibold">
				{totalItems} Alert{totalItems !== 1 ? 's' : ''} Found
				{#if totalItems > 0}
					<span class="text-sm font-normal text-gray-600">
						(showing {(currentPage - 1) * perPage + 1}-{Math.min(currentPage * perPage, totalItems)}
						of {totalItems})
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
					{#each perPageOptions as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
				<span class="text-sm text-gray-600">per page</span>
			</div>
		</div>

		{#if groupedAlerts.length === 0}
			<!-- Empty State -->
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
			<!-- Table Content -->
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
											{#each getAlertTypeBadges(groupedAlert.alert_types) as badge}
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
						on:click={() => prevPage()}
						disabled={!hasPrev}
						class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						Previous
					</button>

					<div class="flex items-center space-x-1">
						{#each getDisplayPages().pages as page}
							<button
								on:click={() => goToPage(page)}
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
								on:click={() => goToPage(totalPages)}
								class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
							>
								{totalPages}
							</button>
						{/if}
					</div>

					<button
						on:click={() => nextPage()}
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
	</Card>
{/if}
