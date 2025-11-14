<!--
@component FollowUpControls
@description Follow-up control panel for telescope observations and data layers
@category Visualization Components
@version 2.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<FollowUpControls
  footprintData={instruments}
  galaxyData={galaxies}
  candidateData={candidates}
  icecubeData={icecube}
  {hasIceCubeData}
  {hasCandidateData}
  bind:showFootprints
  bind:showGalaxies
  bind:showCandidates
  bind:showIceCube
  on:toggleInstrument={handleToggleInstrument}
  on:toggleAllInstruments={handleToggleAll}
  on:toggleMarkerGroup={handleToggleMarkerGroup}
  on:animateToMarker={handleAnimateToMarker}
  on:loadData={handleLoadData}
/>
```

@prop {any} footprintData - Telescope footprint data
@prop {any[]} galaxyData - Galaxy marker data
@prop {any[]} candidateData - Candidate object data
@prop {any[]} icecubeData - IceCube neutrino data
@prop {boolean} hasIceCubeData - Whether IceCube data exists
@prop {boolean} hasCandidateData - Whether candidate data exists
@prop {boolean} showFootprints - Show instrument footprints
@prop {boolean} showGrbCoverage - Show GRB coverage
@prop {boolean} showGalaxies - Show galaxy markers
@prop {boolean} showCandidates - Show candidate markers
@prop {boolean} showIceCube - Show IceCube markers
@prop {any} overlayLists - Overlay management data

@event toggleInstrument - Individual instrument toggled
@event toggleAllInstruments - All instruments toggled
@event toggleMarkerGroup - Marker group toggled
@event animateToMarker - Animate to specific marker
@event loadData - Request to load data
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import InstrumentPanel from './panels/InstrumentPanel.svelte';
	import DataLayerPanel from './panels/DataLayerPanel.svelte';

	export let footprintData: any = null;
	export let galaxyData: any[] = [];
	export let candidateData: any[] = [];
	export let icecubeData: any[] = [];
	export let hasIceCubeData: boolean = false;
	export let hasCandidateData: boolean = false;
	export let showFootprints: boolean = true;
	export let showGrbCoverage: boolean = true;
	export let showGalaxies: boolean = false;
	export let showCandidates: boolean = false;
	export let showIceCube: boolean = false;
	export const overlayLists: any = {};

	const dispatch = createEventDispatcher();

	// Instrument panel event handlers
	function handleToggleFootprints(event: CustomEvent) {
		showFootprints = event.detail.expanded;
	}

	function handleToggleInstrument(event: CustomEvent) {
		dispatch('toggleInstrument', event.detail);
	}

	function handleToggleAllInstruments(event: CustomEvent) {
		dispatch('toggleAllInstruments', event.detail);
	}

	// Data layer event handlers
	function handleToggleGalaxies(event: CustomEvent) {
		showGalaxies = event.detail.expanded;
	}

	function handleToggleCandidates(event: CustomEvent) {
		showCandidates = event.detail.expanded;
	}

	function handleToggleIceCube(event: CustomEvent) {
		showIceCube = event.detail.expanded;
	}

	function handleToggleGrbCoverage() {
		showGrbCoverage = !showGrbCoverage;
	}

	function handleToggleMarkerGroup(event: CustomEvent) {
		dispatch('toggleMarkerGroup', event.detail);
	}

	function handleAnimateToMarker(event: CustomEvent) {
		dispatch('animateToMarker', event.detail);
	}

	function handleLoadData(event: CustomEvent) {
		dispatch('loadData', event.detail);
	}
</script>

<!-- Follow-up controls panel with modern component architecture -->
<div class="follow-up-controls w-full max-w-sm space-y-4">
	<!-- Header -->
	<div class="border-b pb-2">
		<h3 class="text-lg font-semibold text-gray-900">Follow-Up</h3>
	</div>

	<!-- Instrument Controls -->
	<InstrumentPanel
		{footprintData}
		expanded={showFootprints}
		on:toggle={handleToggleFootprints}
		on:toggleInstrument={handleToggleInstrument}
		on:toggleAllInstruments={handleToggleAllInstruments}
	/>

	<!-- GRB Coverage Controls -->
	<div class="grb-coverage-panel mb-4">
		<div class="flex items-center gap-2 mb-2">
			<button
				class="toggle-btn w-4 h-4 bg-blue-600 rounded-sm flex items-center justify-center text-white text-xs"
				class:expanded={showGrbCoverage}
				on:click={handleToggleGrbCoverage}
				aria-label="Toggle GRB coverage panel"
			>
				<span class="transform transition-transform duration-200" class:rotate-90={showGrbCoverage}>
					▶
				</span>
			</button>

			<button
				class="action-btn px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
				on:click={handleToggleGrbCoverage}
			>
				{showGrbCoverage ? 'Hide' : 'Show'}
			</button>

			<h4 class="text-sm font-medium text-gray-900 flex-1">GRB Coverage</h4>
		</div>

		{#if showGrbCoverage}
			<div class="panel-content bg-gray-50 rounded border p-3 min-h-12">
				<p class="text-sm text-gray-600">No GRB coverage data available</p>
			</div>
		{/if}
	</div>

	<!-- Sources Section Header -->
	<div class="border-b pb-2">
		<h3 class="text-lg font-semibold text-gray-900">Sources</h3>
	</div>

	<!-- Galaxy Data Layer -->
	<DataLayerPanel
		title="Galaxies"
		data={galaxyData}
		expanded={showGalaxies}
		loading={false}
		hasData={galaxyData.length > 0}
		dataType="galaxies"
		on:toggle={handleToggleGalaxies}
		on:loadData={handleLoadData}
		on:toggleMarkerGroup={handleToggleMarkerGroup}
		on:animateToMarker={handleAnimateToMarker}
	/>

	<!-- IceCube Data Layer -->
	{#if hasIceCubeData}
		<DataLayerPanel
			title="ICECUBE Notice"
			data={icecubeData}
			expanded={showIceCube}
			loading={false}
			hasData={icecubeData.length > 0}
			dataType="icecube"
			on:toggle={handleToggleIceCube}
			on:loadData={handleLoadData}
			on:toggleMarkerGroup={handleToggleMarkerGroup}
			on:animateToMarker={handleAnimateToMarker}
		/>
	{/if}

	<!-- Candidate Data Layer -->
	{#if hasCandidateData}
		<DataLayerPanel
			title="Candidates"
			data={candidateData}
			expanded={showCandidates}
			loading={false}
			hasData={candidateData.length > 0}
			dataType="candidates"
			on:toggle={handleToggleCandidates}
			on:loadData={handleLoadData}
			on:toggleMarkerGroup={handleToggleMarkerGroup}
			on:animateToMarker={handleAnimateToMarker}
		/>
	{/if}
</div>

<style>
	.follow-up-controls {
		background-color: white;
		border-radius: 0.5rem;
		border: 1px solid #e5e7eb;
		padding: 1rem;
	}

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
</style>
