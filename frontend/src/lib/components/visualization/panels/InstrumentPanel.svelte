<!--
@component InstrumentPanel
@description Panel for displaying and controlling instrument footprints
@category Visualization Components
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<InstrumentPanel
  footprintData={instruments}
  expanded={showFootprints}
  on:toggle={handleToggleFootprints}
  on:toggleInstrument={handleToggleInstrument}
  on:toggleAllInstruments={handleToggleAll}
/>
```

@prop {any[]} footprintData - Array of instrument footprint data
@prop {boolean} expanded - Whether panel is expanded

@event toggle - Panel expanded/collapsed
@event toggleInstrument - Individual instrument toggled
@event toggleAllInstruments - All instruments toggled
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { LoadingState } from '$lib/components/ui';

	const dispatch = createEventDispatcher<{
		toggle: { expanded: boolean };
		toggleInstrument: { target: HTMLInputElement; checked: boolean };
		toggleAllInstruments: { show: boolean };
	}>();

	/**
	 * Array of instrument footprint data
	 * @type {any[]}
	 * @default []
	 */
	export let footprintData: any[] = [];

	/**
	 * Whether panel is expanded
	 * @type {boolean}
	 * @default true
	 */
	export let expanded: boolean = true;

	$: loading = !footprintData || footprintData.length === 0;

	function handleToggle() {
		expanded = !expanded;
		dispatch('toggle', { expanded });
	}

	function handleToggleAll() {
		dispatch('toggleAllInstruments', { show: !expanded });
	}

	function handleInstrumentToggle(e: Event) {
		const target = e.target as HTMLInputElement;
		dispatch('toggleInstrument', { target, checked: target.checked });
	}
</script>

<div class="instrument-panel mb-4">
	<!-- Panel Header -->
	<div class="flex items-center gap-2 mb-2">
		<button
			class="toggle-btn w-4 h-4 bg-blue-600 rounded-sm flex items-center justify-center text-white text-xs"
			class:expanded
			on:click={handleToggle}
			aria-label="Toggle instruments panel"
		>
			<span class="transform transition-transform duration-200" class:rotate-90={expanded}>
				▶
			</span>
		</button>

		<button
			class="action-btn px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
			on:click={handleToggleAll}
		>
			{expanded ? 'Hide' : 'Show'}
		</button>

		<h4 class="text-sm font-medium flex-1" class:text-gray-500={loading}>
			{loading ? '...Loading...' : 'Instruments'}
		</h4>
	</div>

	<!-- Panel Content -->
	{#if expanded}
		<div class="panel-content bg-gray-50 rounded border p-3 max-h-64 overflow-y-auto">
			{#if loading}
				<LoadingState message="Loading instruments..." size="small" />
			{:else if footprintData && Array.isArray(footprintData)}
				<div class="instrument-list space-y-2">
					{#each footprintData as inst, i}
						<label
							class="flex items-center gap-2 p-1 hover:bg-white rounded transition-colors cursor-pointer"
						>
							<input
								type="checkbox"
								checked={true}
								data-color={inst.color || '#ff0000'}
								on:change={handleInstrumentToggle}
								class="w-3 h-3"
							/>
							<span
								class="w-3 h-3 border border-gray-300 rounded-sm"
								style="background-color: {inst.color || '#ff0000'};"
								aria-hidden="true"
							></span>
							<span class="text-sm text-gray-900 flex-1">
								{inst.name || `Inst ${i + 1}`}
							</span>
						</label>
					{/each}
				</div>
			{:else}
				<p class="text-sm text-gray-600">No instrument data available</p>
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

	.instrument-list label:hover {
		background-color: white;
	}
</style>
