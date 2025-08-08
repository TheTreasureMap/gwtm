<!--
@component Table
@description A reusable table component with sorting, pagination, and consistent styling
@category UI Primitives  
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<Table 
  data={instruments} 
  columns={tableColumns}
  sortable={true}
  paginated={true}
  pageSize={10}
  let:item
  let:column
>
  <svelte:fragment slot="cell" let:item let:column>
    {#if column.key === 'status'}
      <StatusBadge variant="success" label={item[column.key]} />
    {:else}
      {item[column.key]}
    {/if}
  </svelte:fragment>
</Table>
```

@prop {Array} data - Array of data objects to display
@prop {Array} columns - Column configuration array
@prop {boolean} sortable - Whether columns are sortable
@prop {boolean} paginated - Whether to enable pagination
@prop {number} pageSize - Number of items per page
@prop {string} emptyMessage - Message to show when no data
@prop {boolean} loading - Whether table is loading
@prop {string} class - Additional CSS classes

@slot cell - Custom cell content (receives item and column)
@slot empty - Custom empty state content
@slot loading - Custom loading state content

@event sort - Fired when column is sorted
@event page-change - Fired when page changes
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import LoadingState from './LoadingState.svelte';
	import Button from './Button.svelte';

	const dispatch = createEventDispatcher<{
		sort: { column: string; direction: 'asc' | 'desc' };
		'page-change': { page: number };
	}>();

	/**
	 * Array of data objects to display
	 * @type {Array<Record<string, any>>}
	 * @default []
	 */
	export let data: Array<Record<string, any>> = [];

	/**
	 * Column configuration array
	 * @type {Array<{key: string, label: string, sortable?: boolean, width?: string}>}
	 * @default []
	 */
	export let columns: Array<{
		key: string;
		label: string;
		sortable?: boolean;
		width?: string;
	}> = [];

	/**
	 * Whether columns are sortable
	 * @type {boolean}
	 * @default false
	 */
	export let sortable: boolean = false;

	/**
	 * Whether to enable pagination
	 * @type {boolean}
	 * @default false
	 */
	export let paginated: boolean = false;

	/**
	 * Number of items per page
	 * @type {number}
	 * @default 10
	 */
	export let pageSize: number = 10;

	/**
	 * Message to show when no data
	 * @type {string}
	 * @default 'No data available'
	 */
	export let emptyMessage: string = 'No data available';

	/**
	 * Whether table is loading
	 * @type {boolean}
	 * @default false
	 */
	export let loading: boolean = false;

	/**
	 * Additional CSS classes
	 * @type {string}
	 * @default ''
	 */
	let className: string = '';
	export { className as class };

	// Internal state
	let sortColumn: string = '';
	let sortDirection: 'asc' | 'desc' = 'asc';
	let currentPage: number = 1;

	// Reactive calculations
	$: sortedData =
		sortable && sortColumn
			? [...data].sort((a, b) => {
					const aVal = a[sortColumn];
					const bVal = b[sortColumn];

					if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
					if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
					return 0;
				})
			: data;

	$: totalPages = paginated ? Math.ceil(sortedData.length / pageSize) : 1;

	$: displayData = paginated
		? sortedData.slice((currentPage - 1) * pageSize, currentPage * pageSize)
		: sortedData;

	$: tableClass = ['min-w-full divide-y divide-gray-200', className].filter(Boolean).join(' ');

	function handleSort(column: (typeof columns)[0]) {
		if (!sortable || !column.sortable) return;

		if (sortColumn === column.key) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column.key;
			sortDirection = 'asc';
		}

		dispatch('sort', { column: column.key, direction: sortDirection });
	}

	function handlePageChange(page: number) {
		currentPage = page;
		dispatch('page-change', { page });
	}

	function getSortIcon(column: (typeof columns)[0]) {
		if (!sortable || !column.sortable) return '';
		if (sortColumn !== column.key) return '↕️';
		return sortDirection === 'asc' ? '↑' : '↓';
	}
</script>

<div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
	{#if loading}
		<div class="p-8">
			<slot name="loading">
				<LoadingState message="Loading table data..." />
			</slot>
		</div>
	{:else if displayData.length === 0}
		<div class="p-8 text-center text-gray-500">
			<slot name="empty">
				{emptyMessage}
			</slot>
		</div>
	{:else}
		<table class={tableClass}>
			<thead class="bg-gray-50">
				<tr>
					{#each columns as column}
						<th
							scope="col"
							class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
							class:cursor-pointer={sortable && column.sortable}
							style={column.width ? `width: ${column.width}` : ''}
							on:click={() => handleSort(column)}
							on:keydown={(e) => e.key === 'Enter' && handleSort(column)}
							tabindex={sortable && column.sortable ? 0 : -1}
						>
							<div class="flex items-center gap-1">
								{column.label}
								{#if sortable && column.sortable}
									<span class="text-gray-400" aria-hidden="true">
										{getSortIcon(column)}
									</span>
								{/if}
							</div>
						</th>
					{/each}
				</tr>
			</thead>
			<tbody class="bg-white divide-y divide-gray-200">
				{#each displayData as item, index}
					<tr class="hover:bg-gray-50">
						{#each columns as column}
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
								<slot name="cell" {item} {column} {index}>
									{item[column.key] || '—'}
								</slot>
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>

		{#if paginated && totalPages > 1}
			<div
				class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6"
			>
				<div class="flex-1 flex justify-between sm:hidden">
					<Button
						variant="secondary"
						disabled={currentPage === 1}
						on:click={() => handlePageChange(currentPage - 1)}
					>
						Previous
					</Button>
					<Button
						variant="secondary"
						disabled={currentPage === totalPages}
						on:click={() => handlePageChange(currentPage + 1)}
					>
						Next
					</Button>
				</div>
				<div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
					<div>
						<p class="text-sm text-gray-700">
							Showing
							<span class="font-medium">{(currentPage - 1) * pageSize + 1}</span>
							to
							<span class="font-medium">{Math.min(currentPage * pageSize, sortedData.length)}</span>
							of
							<span class="font-medium">{sortedData.length}</span>
							results
						</p>
					</div>
					<div>
						<nav
							class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px"
							aria-label="Pagination"
						>
							<Button
								variant="secondary"
								size="sm"
								disabled={currentPage === 1}
								on:click={() => handlePageChange(currentPage - 1)}
							>
								Previous
							</Button>

							{#each Array.from({ length: totalPages }, (_, i) => i + 1) as page}
								{#if page === 1 || page === totalPages || (page >= currentPage - 1 && page <= currentPage + 1)}
									<Button
										variant={page === currentPage ? 'primary' : 'secondary'}
										size="sm"
										on:click={() => handlePageChange(page)}
									>
										{page}
									</Button>
								{:else if page === currentPage - 2 || page === currentPage + 2}
									<span class="px-2 py-1 text-gray-500">...</span>
								{/if}
							{/each}

							<Button
								variant="secondary"
								size="sm"
								disabled={currentPage === totalPages}
								on:click={() => handlePageChange(currentPage + 1)}
							>
								Next
							</Button>
						</nav>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>
