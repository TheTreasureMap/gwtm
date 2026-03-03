<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { GWAlertSchema } from '$lib/api';
	import { LoadingState, AlertBanner } from '$lib/components/ui';
	import SummaryTab from './tabs/SummaryTab.svelte';
	import CoverageCalculatorTab from './tabs/CoverageCalculatorTab.svelte';
	import RenormalizeSkyMapTab from './tabs/RenormalizeSkyMapTab.svelte';

	export let selectedAlert: GWAlertSchema | null = null;
	export let loading: boolean = false;
	export let error: string = '';
	export let plotlyContainer: HTMLDivElement | null = null;
	export let instruments: Array<{ id: number; name: string }> = [];

	const dispatch = createEventDispatcher<{
		calculateCoverage: Record<string, unknown>;
		visualizeRenormalizedSkymap: void;
		downloadRenormalizedSkymap: void;
	}>();

	let activeTab = 'info';

	function handleCalculateCoverage(event: CustomEvent) {
		dispatch('calculateCoverage', event.detail);
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
		<div role="tablist" class="tabs tabs-bordered mb-4">
			<button
				role="tab"
				class="tab"
				class:tab-active={activeTab === 'info'}
				on:click={() => (activeTab = 'info')}>Summary</button
			>
			<button
				role="tab"
				class="tab"
				class:tab-active={activeTab === 'coverage'}
				on:click={() => (activeTab = 'coverage')}>Coverage Calculator</button
			>
			<button
				role="tab"
				class="tab"
				class:tab-active={activeTab === 'renorm'}
				on:click={() => (activeTab = 'renorm')}>Renormalize Skymap</button
			>
		</div>

		{#if activeTab === 'info'}
			<SummaryTab {selectedAlert} />
		{:else if activeTab === 'coverage'}
			<CoverageCalculatorTab
				{plotlyContainer}
				{instruments}
				on:calculate={handleCalculateCoverage}
			/>
		{:else if activeTab === 'renorm'}
			<RenormalizeSkyMapTab
				on:download={handleDownloadRenormalizedSkymap}
				on:visualize={handleVisualizeRenormalizedSkymap}
			/>
		{/if}
	</div>
{/if}
