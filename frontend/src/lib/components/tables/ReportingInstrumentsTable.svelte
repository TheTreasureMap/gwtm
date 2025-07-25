<!--
@component ReportingInstrumentsTable
@description Table displaying instruments that have reported completed pointings
@category Tables
@version 2.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<ReportingInstrumentsTable {instruments} {loading} />
```

@prop {InstrumentSchema[]} instruments - Array of instruments to display
@prop {boolean} loading - Whether data is loading
-->
<script lang="ts">
	import type { InstrumentSchema } from '$lib/api';
	import { Table, StatusBadge, LoadingState } from '$lib/components/ui';

	/**
	 * Array of instruments to display
	 * @type {InstrumentSchema[]}
	 * @default []
	 */
	export let instruments: InstrumentSchema[] = [];

	/**
	 * Whether data is loading
	 * @type {boolean}
	 * @default false
	 */
	export let loading: boolean = false;

	// Table configuration
	$: columns = [
		{
			key: 'instrument_name',
			label: 'Instrument Name',
			sortable: true
		},
		{
			key: 'num_pointings',
			label: 'Number of pointings reported',
			sortable: true,
			width: '200px'
		}
	];

	// Transform data for table component
	$: tableData = instruments.map((instrument) => ({
		...instrument,
		// Ensure num_pointings is always a number for sorting
		num_pointings: instrument.num_pointings || 0
	}));
</script>

<div class="bg-white rounded-lg shadow-lg overflow-hidden">
	<Table
		data={tableData}
		{columns}
		{loading}
		sortable={true}
		emptyMessage="No instruments have reported completed pointings yet."
	>
		<!-- Custom loading state -->
		<LoadingState slot="loading" message="Loading reporting instruments..." />

		<!-- Custom empty state -->
		<div slot="empty" class="p-8 text-center">
			<svg
				class="mx-auto h-12 w-12 text-gray-400"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				aria-hidden="true"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
				/>
			</svg>
			<h3 class="mt-2 text-sm font-medium text-gray-900">No reporting instruments found</h3>
			<p class="mt-1 text-sm text-gray-500">
				No instruments have reported completed pointings yet.
			</p>
		</div>

		<!-- Custom cell rendering -->
		<svelte:fragment slot="cell" let:item let:column>
			{#if column.key === 'instrument_name'}
				<a
					href="/instrument/{item.id}"
					class="text-blue-600 hover:text-blue-800 hover:underline font-medium"
				>
					{item.instrument_name}
					{#if item.nickname}
						<span class="text-gray-500 font-normal ml-1">({item.nickname})</span>
					{/if}
				</a>
			{:else if column.key === 'num_pointings'}
				<StatusBadge variant="success" label={item.num_pointings.toString()} size="small" />
			{:else}
				{item[column.key] || '—'}
			{/if}
		</svelte:fragment>
	</Table>

	<!-- Footer with summary info -->
	<div class="bg-gray-50 px-6 py-3">
		<div class="flex items-center justify-between">
			<div class="text-sm text-gray-700">
				Showing <span class="font-medium">{instruments.length}</span> reporting instrument{instruments.length !==
				1
					? 's'
					: ''}
			</div>
			<div class="text-xs text-gray-500">Click instrument name to view details</div>
		</div>
	</div>
</div>
