<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Table from '$lib/components/ui/Table.svelte';
	import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	const dispatch = createEventDispatcher<{
		'selection-change': { selectedPointings: Set<number> };
		'select-all': { checked: boolean };
	}>();

	export let pointings: any[] = [];
	export let loading: boolean = false;
	export let allowSelection: boolean = false;
	export let selectedPointings: Set<number> = new Set();

	// Table configuration
	const columns = [
		{ key: 'checkbox', label: '', sortable: false, width: '50px' },
		{ key: 'id', label: 'ID', sortable: true, width: '80px' },
		{ key: 'position', label: 'Position (RA, DEC)', sortable: false, width: '200px' },
		{ key: 'status', label: 'Status', sortable: true, width: '120px' },
		{ key: 'instrument_name', label: 'Instrument', sortable: true, width: '150px' },
		{ key: 'band', label: 'Band', sortable: true, width: '80px' },
		{ key: 'depth', label: 'Depth', sortable: true, width: '100px' },
		{ key: 'pos_angle', label: 'Position Angle', sortable: true, width: '120px' },
		{ key: 'time', label: 'Time', sortable: true, width: '180px' },
		{ key: 'username', label: 'Submitter', sortable: true, width: '120px' },
		{ key: 'doi_url', label: 'DOI', sortable: false, width: '200px' }
	];

	function canSelectPointing(pointing: any): boolean {
		// Only allow selection if:
		// 1. Selection is allowed (allowSelection is true, which means myPointsOnly is true)
		// 2. Status is 'completed'
		// 3. No DOI URL already exists
		return allowSelection && pointing.status === 'completed' && !pointing.doi_url;
	}

	function togglePointingSelection(pointingId: number) {
		if (selectedPointings.has(pointingId)) {
			selectedPointings.delete(pointingId);
		} else {
			selectedPointings.add(pointingId);
		}
		selectedPointings = selectedPointings; // Trigger reactivity
		dispatch('selection-change', { selectedPointings });
	}

	function toggleAllSelection(event: Event) {
		const target = event.target as HTMLInputElement;
		const checked = target.checked;
		
		if (checked) {
			// Select all selectable pointings
			pointings.forEach(pointing => {
				if (canSelectPointing(pointing)) {
					selectedPointings.add(pointing.id);
				}
			});
		} else {
			selectedPointings.clear();
		}
		selectedPointings = selectedPointings; // Trigger reactivity
		dispatch('selection-change', { selectedPointings });
		dispatch('select-all', { checked });
	}

	function formatPosition(position: string): string {
		// Format POINT(ra dec) string to "ra, dec"
		if (position && position.startsWith('POINT(')) {
			const coords = position.slice(6, -1); // Remove "POINT(" and ")"
			return coords.replace(' ', ', ');
		}
		return position || '—';
	}

	function formatTime(time: string): string {
		// Format ISO timestamp to readable format
		try {
			return new Date(time).toLocaleString();
		} catch {
			return time || '—';
		}
	}

	function getStatusVariant(status: string): 'success' | 'warning' | 'error' | 'info' {
		switch (status?.toLowerCase()) {
			case 'completed':
				return 'success';
			case 'planned':
				return 'warning';
			case 'cancelled':
				return 'error';
			default:
				return 'info';
		}
	}

	// Compute if "select all" checkbox should be checked/indeterminate
	$: selectablePointings = pointings.filter(canSelectPointing);
	$: allSelectableSelected = selectablePointings.length > 0 && 
		selectablePointings.every(p => selectedPointings.has(p.id));
	$: someSelected = selectedPointings.size > 0;
	$: selectAllIndeterminate = someSelected && !allSelectableSelected;
</script>

<div class="bg-white shadow-md rounded-lg overflow-hidden">
	<Table 
		data={pointings} 
		{columns} 
		{loading}
		sortable={true}
		paginated={true}
		pageSize={25}
		emptyMessage="No pointings found for the selected criteria."
		let:item
		let:column
	>
		<svelte:fragment slot="cell" let:item let:column>
			{#if column.key === 'checkbox'}
				{#if allowSelection}
					<input
						type="checkbox"
						checked={selectedPointings.has(item.id)}
						disabled={!canSelectPointing(item)}
						on:change={() => togglePointingSelection(item.id)}
						class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded disabled:opacity-50"
					/>
				{:else}
					<input
						type="checkbox"
						disabled
						class="h-4 w-4 text-gray-400 border-gray-300 rounded opacity-50"
					/>
				{/if}
				
			{:else if column.key === 'position'}
				{formatPosition(item[column.key])}
				
			{:else if column.key === 'status'}
				<StatusBadge
					variant={getStatusVariant(item[column.key])}
					label={item[column.key] || 'Unknown'}
				/>
				
			{:else if column.key === 'time'}
				{formatTime(item[column.key])}
				
			{:else if column.key === 'doi_url'}
				{#if item[column.key]}
					<a 
						href={item[column.key]} 
						target="_blank" 
						class="text-indigo-600 hover:text-indigo-900 underline text-sm"
					>
						{item[column.key]}
					</a>
				{:else}
					—
				{/if}
				
			{:else if column.key === 'depth' || column.key === 'pos_angle'}
				{item[column.key] || '—'}
				
			{:else}
				{item[column.key] || '—'}
			{/if}
		</svelte:fragment>

		<!-- Custom header for checkbox column -->
		<svelte:fragment slot="header" let:column>
			{#if column.key === 'checkbox'}
				<input
					type="checkbox"
					checked={allSelectableSelected}
					indeterminate={selectAllIndeterminate}
					disabled={!allowSelection || selectablePointings.length === 0}
					on:change={toggleAllSelection}
					class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded disabled:opacity-50"
				/>
			{:else}
				{column.label}
			{/if}
		</svelte:fragment>
	</Table>
	
	<!-- Selection Summary -->
	{#if allowSelection && selectedPointings.size > 0}
		<div class="bg-indigo-50 px-6 py-3 border-t border-gray-200">
			<div class="flex items-center justify-between">
				<span class="text-sm text-indigo-700">
					{selectedPointings.size} pointing{selectedPointings.size === 1 ? '' : 's'} selected
				</span>
				<Button
					variant="ghost"
					size="small"
					on:click={() => {
						selectedPointings.clear();
						selectedPointings = selectedPointings;
						dispatch('selection-change', { selectedPointings });
					}}
				>
					Clear Selection
				</Button>
			</div>
		</div>
	{/if}
</div>