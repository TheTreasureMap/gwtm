<script lang="ts">
	import { createEventDispatcher } from 'svelte';

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
	export let overlayLists: any = {};

	const dispatch = createEventDispatcher();

	function toggleInstrumentOverlay(e: Event) {
		const target = e.target as HTMLInputElement;
		dispatch('toggleInstrument', { target, checked: target.checked });
	}

	function toggleAllInstruments(show: boolean) {
		dispatch('toggleAllInstruments', { show });
	}

	function handleMarkerToggle(groupName: string, checked: boolean, dataType: string) {
		dispatch('toggleMarkerGroup', { groupName, checked, dataType });
	}

	function handleMarkerClick(markerName: string, dataType: string) {
		dispatch('animateToMarker', { markerName, dataType });
	}

	function loadData(dataType: string) {
		dispatch('loadData', { dataType });
	}
</script>

<!-- Right column: Follow-up controls (30% width) matching Flask exactly -->
<div class="column" style="float: right; width: 30%; padding-left: 2%;">
	<div class="row">
		<h3>Follow-Up</h3>
	</div>

	<!-- Instrument block buttons and div (matching Flask exactly) -->
	<div class="btn-group">
		<button 
			class="btn btn-primary btn-sm alert_coll my-1 {showFootprints ? 'down-triangle' : ''}"
			on:click={() => showFootprints = !showFootprints}
			style="margin-right: 5px;"
		></button>
		<button 
			class="btn btn-primary btn-sm my-1"
			on:click={() => toggleAllInstruments(!showFootprints)}
			style="margin-right: 5px;"
		>
			{showFootprints ? 'Hide' : 'Show'}
		</button>
		<h4 style="display: inline-block;" class={(!footprintData || footprintData.length === 0) ? 'loadingtext' : ''}>
			{(!footprintData || footprintData.length === 0) ? '...Loading...' : 'Instruments'}
		</h4>
	</div>
	<div class="row">
		<div class="collapse {showFootprints ? 'in' : ''} scroll-section inst_coll">
			{#if footprintData && Array.isArray(footprintData)}
				{#each footprintData as inst, i}
					<label style="display: block; padding: 2px 0;">
						<input 
							type="checkbox" 
							checked={true}
							style="margin-right: 5px;"
							data-color={inst.color || '#ff0000'}
							on:change={toggleInstrumentOverlay}
						/>
						<span 
							style="display: inline-block; width: 12px; height: 12px; margin-right: 5px; border: 1px solid #ccc; background-color: {inst.color || '#ff0000'};"
						></span>
						{inst.name || `Inst ${i + 1}`}
					</label>
				{/each}
			{/if}
		</div>
	</div>
	
	<!-- GRB coverage block buttons and div -->
	<div class="btn-group">
		<button 
			class="btn btn-primary btn-sm alert_coll my-1 {showGrbCoverage ? 'down-triangle' : ''}"
			on:click={() => showGrbCoverage = !showGrbCoverage}
			style="margin-right: 5px;"
		></button>
		<button 
			class="btn btn-primary btn-sm my-1"
			on:click={() => showGrbCoverage = !showGrbCoverage}
			style="margin-right: 5px;"
		>
			{showGrbCoverage ? 'Hide' : 'Show'}
		</button>
		<h4 style="display: inline-block;">GRB Coverage</h4>
	</div>
	<div class="row">
		<div class="collapse {showGrbCoverage ? 'in' : ''} grb_coll"></div>
	</div>
	
	<div class="row">
		<h3>Sources</h3>
	</div>
	
	<!-- Galaxies block buttons and div -->
	<div class="btn-group">
		<button 
			class="btn btn-primary btn-sm alert_coll my-1 {showGalaxies ? 'down-triangle' : ''}"
			on:click={() => showGalaxies = !showGalaxies}
			style="margin-right: 5px;"
		></button>
		<button 
			class="btn btn-primary btn-sm my-1"
			on:click={() => {
				if (!showGalaxies && galaxyData.length === 0) {
					loadData('galaxies');
				} else if (galaxyData.length > 0) {
					handleMarkerToggle('all', !showGalaxies, 'galaxies');
				}
				showGalaxies = !showGalaxies;
			}}
			style="margin-right: 5px;"
		>
			{galaxyData.length > 0 ? (showGalaxies ? 'Hide' : 'Show') : 'Get'}
		</button>
		<h4 style="display: inline-block;">Galaxies</h4>
	</div>
	<div class="row">
		<div class="collapse {showGalaxies ? 'in' : ''} gal_coll">
			{#if galaxyData.length > 0}
				{#each galaxyData as group}
					<div style="margin-bottom: 5px;">
						<div style="font-weight: bold; font-size: 13px;">{group.name}</div>
						{#if group.markers}
							{#each group.markers as marker}
								<button 
									style="display: block; width: 100%; text-align: left; padding: 2px 5px; border: none; background: none; font-size: 12px; cursor: pointer;"
									on:click={() => handleMarkerClick(marker.name, 'galaxies')}
									on:mouseover={(e) => (e.target).style.backgroundColor = '#f0f0f0'}
									on:mouseout={(e) => (e.target).style.backgroundColor = 'transparent'}
								>
									{marker.name}
								</button>
							{/each}
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</div>
	
	<!-- IceCube Notice block buttons and div -->
	{#if hasIceCubeData}
	<div class="btn-group">
		<button 
			class="btn btn-primary btn-sm alert_coll my-1 {showIceCube ? 'down-triangle' : ''}"
			on:click={() => showIceCube = !showIceCube}
			style="margin-right: 5px;"
		></button>
		<button 
			class="btn btn-primary btn-sm my-1"
			on:click={() => {
				if (!showIceCube && icecubeData.length === 0) {
					loadData('icecube');
				}
				showIceCube = !showIceCube;
			}}
			style="margin-right: 5px;"
		>
			{icecubeData.length > 0 ? (showIceCube ? 'Hide' : 'Show') : 'Get'}
		</button>
		<h4 style="display: inline-block;">ICECUBE Notice</h4>
	</div>
	<div class="row">
		<div class="collapse {showIceCube ? 'in' : ''} icecube_coll">
			{#if icecubeData.length > 0}
				{#each icecubeData as group}
					<div style="margin-bottom: 5px;">
						<div style="font-weight: bold; font-size: 13px;">{group.name}</div>
						{#if group.markers}
							{#each group.markers as marker}
								<button 
									style="display: block; width: 100%; text-align: left; padding: 2px 5px; border: none; background: none; font-size: 12px; cursor: pointer;"
									on:click={() => handleMarkerClick(marker.name, 'icecube')}
									on:mouseover={(e) => (e.target).style.backgroundColor = '#f0f0f0'}
									on:mouseout={(e) => (e.target).style.backgroundColor = 'transparent'}
								>
									{marker.name}
								</button>
							{/each}
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</div>
	{/if}
	
	<!-- Candidates block buttons and div -->
	{#if hasCandidateData}
	<div class="btn-group">
		<button 
			class="btn btn-primary btn-sm alert_coll my-1 {showCandidates ? 'down-triangle' : ''}"
			on:click={() => showCandidates = !showCandidates}
			style="margin-right: 5px;"
		></button>
		<button 
			class="btn btn-primary btn-sm my-1"
			on:click={() => {
				if (!showCandidates && candidateData.length === 0) {
					loadData('candidates');
				}
				showCandidates = !showCandidates;
			}}
			style="margin-right: 5px;"
		>
			{candidateData.length > 0 ? (showCandidates ? 'Hide' : 'Show') : 'Get'}
		</button>
		<h4 style="display: inline-block;">Candidates</h4>
	</div>
	<div class="row">
		<div class="collapse {showCandidates ? 'in' : ''} candidate_coll">
			{#if candidateData.length > 0}
				{#each candidateData as group}
					<div style="margin-bottom: 5px;">
						<div style="font-weight: bold; font-size: 13px;">{group.name}</div>
						{#if group.markers}
							{#each group.markers as marker}
								<button 
									style="display: block; width: 100%; text-align: left; padding: 2px 5px; border: none; background: none; font-size: 12px; cursor: pointer;"
									on:click={() => handleMarkerClick(marker.name, 'candidates')}
									on:mouseover={(e) => (e.target).style.backgroundColor = '#f0f0f0'}
									on:mouseout={(e) => (e.target).style.backgroundColor = 'transparent'}
								>
									{marker.name}
								</button>
							{/each}
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</div>
	{/if}
</div>

<style>
	.loadingtext {
		color: #888;
	}

	.scroll-section {
		max-height: 200px;
		overflow-y: auto;
		border: 1px solid #eee;
		padding: 10px;
		margin-top: 5px;
	}

	/* Custom styles for buttons and triangles */
	.alert_coll::before {
		content: '▶'; /* Right-pointing triangle */
		margin-right: 5px;
		display: inline-block;
		transition: transform 0.2s;
	}

	.alert_coll.down-triangle::before {
		transform: rotate(90deg);
	}

	.btn {
		display: inline-block;
		font-weight: 400;
		text-align: center;
		vertical-align: middle;
		user-select: none;
		border: 1px solid transparent;
		padding: 0.25rem 0.5rem;
		font-size: 0.875rem;
		line-height: 1.5;
		border-radius: 0.2rem;
		transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
		cursor: pointer;
		background: none;
	}

	.btn-primary {
		color: #fff;
		background-color: #007bff;
		border-color: #007bff;
	}

	.btn-primary:hover {
		color: #fff;
		background-color: #0056b3;
		border-color: #004085;
	}

	.btn-sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.875rem;
		line-height: 1.5;
		border-radius: 0.2rem;
	}

	.collapse {
		display: none;
	}

	.collapse.in {
		display: block;
	}

	.my-1 {
		margin-top: 0.25rem;
		margin-bottom: 0.25rem;
	}
</style>