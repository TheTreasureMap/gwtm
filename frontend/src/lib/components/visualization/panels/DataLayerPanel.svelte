<!--
@component DataLayerPanel
@description Reusable panel for displaying and controlling data layers (galaxies, candidates, icecube)
@category Visualization Components
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<DataLayerPanel
  title="Galaxies"
  data={galaxyData}
  expanded={showGalaxies}
  loading={galaxiesLoading}
  on:toggle={handleToggleGalaxies}
  on:loadData={handleLoadGalaxies}
  on:toggleMarkerGroup={handleToggleMarkerGroup}
  on:animateToMarker={handleAnimateToMarker}
/>
```

@prop {string} title - Panel title
@prop {any[]} data - Array of data items
@prop {boolean} expanded - Whether panel is expanded
@prop {boolean} loading - Whether data is loading
@prop {boolean} hasData - Whether data has been loaded
@prop {string} dataType - Type of data for event dispatching

@event toggle - Panel expanded/collapsed
@event loadData - Request to load data
@event toggleMarkerGroup - Toggle marker group visibility
@event animateToMarker - Animate to specific marker
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { LoadingState } from '$lib/components/ui';

	const dispatch = createEventDispatcher<{
		toggle: { expanded: boolean };
		loadData: { dataType: string };
		toggleMarkerGroup: { groupName: string; checked: boolean; dataType: string };
		animateToMarker: { markerName: string; dataType: string };
	}>();

	/**
	 * Panel title
	 * @type {string}
	 * @default ''
	 */
	export let title: string = '';

	/**
	 * Array of data items
	 * @type {any[]}
	 * @default []
	 */
	export let data: any[] = [];

	/**
	 * Whether panel is expanded
	 * @type {boolean}
	 * @default false
	 */
	export let expanded: boolean = false;

	/**
	 * Whether data is loading
	 * @type {boolean}
	 * @default false
	 */
	export let loading: boolean = false;

	/**
	 * Whether data has been loaded
	 * @type {boolean}
	 * @default false
	 */
	export let hasData: boolean = false;

	/**
	 * Type of data for event dispatching
	 * @type {string}
	 * @default ''
	 */
	export let dataType: string = '';

	// Per-group collapse state (all collapsed by default, matching Flask behaviour)
	let expandedGroups: Record<string, boolean> = {};

	function toggleGroupExpand(groupName: string) {
		expandedGroups[groupName] = !expandedGroups[groupName];
		expandedGroups = expandedGroups; // trigger reactivity
	}

	function handleToggle() {
		expanded = !expanded;
		dispatch('toggle', { expanded });
	}

	function handleLoadData() {
		dispatch('loadData', { dataType });
	}

	function handleShowHide() {
		if (!hasData && !expanded) {
			// Load data first
			handleLoadData();
		} else if (hasData) {
			// Toggle all markers
			dispatch('toggleMarkerGroup', {
				groupName: 'all',
				checked: !expanded,
				dataType
			});
		}
		handleToggle();
	}

	function handleMarkerGroupToggle(groupName: string, checked: boolean) {
		dispatch('toggleMarkerGroup', { groupName, checked, dataType });
	}

	function handleMarkerClick(markerName: string) {
		dispatch('animateToMarker', { markerName, dataType });
	}

	$: buttonText = hasData ? (expanded ? 'Hide' : 'Show') : 'Get';
</script>

<div class="data-layer-panel mb-4">
	<!-- Panel Header -->
	<div class="flex items-center gap-2 mb-2">
		<button
			class="toggle-btn w-4 h-4 bg-blue-600 rounded-sm flex items-center justify-center text-white text-xs"
			class:expanded
			on:click={handleToggle}
			aria-label="Toggle {title} panel"
		>
			<span class="transform transition-transform duration-200" class:rotate-90={expanded}>
				▶
			</span>
		</button>

		<button
			class="action-btn px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
			on:click={handleShowHide}
		>
			{buttonText}
		</button>

		<h4 class="text-sm font-medium text-gray-900 flex-1">
			{title}
			{#if loading}
				<span class="text-gray-500 text-xs ml-1">...Loading...</span>
			{/if}
		</h4>
	</div>

	<!-- Panel Content -->
	{#if expanded}
		<div class="panel-content bg-gray-50 rounded border p-3 max-h-64 overflow-y-auto">
			{#if loading}
				<LoadingState message="Loading {title.toLowerCase()}..." size="small" />
			{:else if !data || data.length === 0}
				<p class="text-sm text-gray-600">No {title.toLowerCase()} data available</p>
			{:else}
				{#each data as group}
					<div class="marker-group mb-2">
						<!-- Group header: collapse arrow + checkbox + group name -->
						<div class="flex items-center gap-1 mb-1">
							<button
								class="text-gray-500 hover:text-gray-700 w-4 text-xs"
								on:click={() => toggleGroupExpand(group.name)}
								aria-label="Toggle {group.name}"
							>
								{expandedGroups[group.name] ? '▼' : '▶'}
							</button>
							<input
								type="checkbox"
								checked={true}
								on:change={(e) => handleMarkerGroupToggle(group.name, e.target?.checked)}
								class="w-3 h-3"
							/>
							{#if group.color}
								<span class="w-3 h-3 rounded-full inline-block flex-shrink-0" style="background-color: {group.color}"></span>
							{/if}
							<span class="text-xs font-medium text-gray-700">{group.name}</span>
						</div>

						<!-- Individual markers (collapsible) -->
						{#if expandedGroups[group.name] && group.markers}
							<div class="marker-list space-y-0.5 ml-5">
								{#each group.markers as marker}
									<button
										class="block w-full text-left px-1 py-0.5 text-xs text-blue-700 hover:bg-blue-100 rounded transition-colors"
										on:click={() => handleMarkerClick(marker.name)}
									>
										{marker.name}
									</button>
								{/each}
							</div>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	{/if}
</div>

<style>
	.toggle-btn.expanded {
		background-color: #1d4ed8;
	}

	.panel-content {
		animation: slideDown 0.2s ease-out;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			max-height: 0;
		}
		to {
			opacity: 1;
			max-height: 16rem;
		}
	}

	.marker-list button:hover {
		background-color: #dbeafe;
	}
</style>
