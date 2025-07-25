<!--
@component EventExplorer
@description Refactored Event Explorer component with tab-based interface for GW alert information
@category Visualization Components
@version 2.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<EventExplorer 
  {selectedAlert} 
  {loading} 
  {error} 
  {plotlyContainer}
  on:calculateCoverage={handleCalculateCoverage}
  on:visualizeRenormalizedSkymap={handleVisualizeRenorm}
  on:downloadRenormalizedSkymap={handleDownloadRenorm}
/>
```

@prop {GWAlertSchema | null} selectedAlert - Selected gravitational wave alert
@prop {boolean} loading - Whether data is loading
@prop {string} error - Error message if any
@prop {HTMLDivElement | null} plotlyContainer - Container for Plotly plots

@event calculateCoverage - Coverage calculation requested
@event visualizeRenormalizedSkymap - Skymap visualization requested  
@event downloadRenormalizedSkymap - Skymap download requested
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { GWAlertSchema } from '$lib/api.js';
	import { TabNavigation, LoadingState, AlertBanner } from '$lib/components/ui';
	import SummaryTab from './tabs/SummaryTab.svelte';
	import CoverageCalculatorTab from './tabs/CoverageCalculatorTab.svelte';
	import RenormalizeSkyMapTab from './tabs/RenormalizeSkyMapTab.svelte';

	/**
	 * Selected gravitational wave alert
	 * @type {GWAlertSchema | null}
	 * @default null
	 */
	export let selectedAlert: GWAlertSchema | null = null;

	/**
	 * Whether data is loading
	 * @type {boolean}
	 * @default false
	 */
	export let loading: boolean = false;

	/**
	 * Error message if any
	 * @type {string}
	 * @default ''
	 */
	export let error: string = '';

	/**
	 * Container for Plotly plots
	 * @type {HTMLDivElement | null}
	 * @default null
	 */
	export let plotlyContainer: HTMLDivElement | null = null;

	const dispatch = createEventDispatcher<{
		calculateCoverage: void;
		visualizeRenormalizedSkymap: void;
		downloadRenormalizedSkymap: void;
	}>();

	let activeTab = 'info';

	// Tab configuration
	const tabs = [
		{ id: 'info', label: 'Summary' },
		{ id: 'coverage', label: 'Coverage Calculator' },
		{ id: 'renorm', label: 'Renormalize Skymap' }
	];

	function handleCalculateCoverage() {
		dispatch('calculateCoverage');
	}

	function handleVisualizeRenormalizedSkymap() {
		dispatch('visualizeRenormalizedSkymap');
	}

	function handleDownloadRenormalizedSkymap() {
		dispatch('downloadRenormalizedSkymap');
	}
</script>

{#if loading}
	<div class="mt-4">
		<LoadingState message="Loading event data..." />
	</div>
{:else if error}
	<div class="mt-4">
		<AlertBanner variant="error" title="Error" dismissible>
			{error}
		</AlertBanner>
	</div>
{:else}
	<div class="mt-4">
		<TabNavigation {tabs} bind:activeTab titleText="Event Explorer:">
			{#if activeTab === 'info'}
				<SummaryTab {selectedAlert} />
			{:else if activeTab === 'coverage'}
				<CoverageCalculatorTab {plotlyContainer} on:calculate={handleCalculateCoverage} />
			{:else if activeTab === 'renorm'}
				<RenormalizeSkyMapTab
					on:download={handleDownloadRenormalizedSkymap}
					on:visualize={handleVisualizeRenormalizedSkymap}
				/>
			{/if}
		</TabNavigation>
	</div>
{/if}
