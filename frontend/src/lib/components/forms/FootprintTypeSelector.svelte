<script lang="ts">
	/**
	 * @component FootprintTypeSelector
	 * @description Dynamic footprint type selector that shows appropriate fields based on selection
	 */

	import { slide } from 'svelte/transition';
	import FormField from './FormField.svelte';
	import type { EnumOption } from '$lib/services/instrumentService';

	export let footprintType: string = '';
	export let footprintTypes: EnumOption[] = [];

	// Rectangular fields
	export let height: number | null = null;
	export let width: number | null = null;

	// Circular fields
	export let radius: number | null = null;

	// Polygon fields
	export let polygon: string = '';

	// Reactive statements for showing/hiding sections
	$: showRectangular = footprintType === 'Rectangular';
	$: showCircular = footprintType === 'Circular';
	$: showPolygon = footprintType === 'Polygon';

	// Convert enum options to form options
	$: footprintOptions = [
		{ value: '', label: 'Choose Footprint Type' },
		...footprintTypes.map((type) => ({
			value: type.value,
			label: type.name
		}))
	];
</script>

<div class="footprint-selector">
	<!-- Footprint Type Selection -->
	<FormField
		name="footprint_type"
		label="Footprint Shape"
		type="select"
		bind:value={footprintType}
		options={footprintOptions}
		required
		helpText="Select the shape of your instrument's field of view"
	/>

	<!-- Rectangular Fields -->
	{#if showRectangular}
		<div class="footprint-section rectangular-section" transition:slide>
			<h4>Rectangular Footprint</h4>
			<div class="form-row">
				<FormField
					name="height"
					label="Height"
					type="number"
					bind:value={height}
					step="any"
					min="0"
					required
					helpText="Height of the rectangular footprint"
				/>
				<FormField
					name="width"
					label="Width"
					type="number"
					bind:value={width}
					step="any"
					min="0"
					required
					helpText="Width of the rectangular footprint"
				/>
			</div>
		</div>
	{/if}

	<!-- Circular Fields -->
	{#if showCircular}
		<div class="footprint-section circular-section" transition:slide>
			<h4>Circular Footprint</h4>
			<FormField
				name="radius"
				label="Radius"
				type="number"
				bind:value={radius}
				step="any"
				min="0"
				required
				helpText="Radius of the circular footprint"
			/>
		</div>
	{/if}

	<!-- Polygon Fields -->
	{#if showPolygon}
		<div class="footprint-section polygon-section" transition:slide>
			<h4>Polygon Footprint</h4>

			<!-- Instructions -->
			<div class="polygon-instructions">
				<h5>Instructions:</h5>
				<ul>
					<li><strong>First and last vertices must be the same to complete polygon</strong></li>
					<li>
						<strong>Vertices must be in order going clockwise, separated by linebreak</strong>
					</li>
					<li><strong>Multiple polygons can be submitted in [] delimited by #</strong></li>
					<li><strong>The entire configuration MUST be centered around 0,0</strong></li>
				</ul>
			</div>

			<!-- Examples -->
			<div class="polygon-examples">
				<div class="example-column">
					<h6>Single Polygon Example:</h6>
					<pre class="example-text">(-1, 1)
(1, 1)
(1, -1)
(-1, -1)
(-1, 1)</pre>
				</div>

				<div class="example-column">
					<h6>Multi-Polygon Example:</h6>
					<pre class="example-text">[(-1, 1)
(-0.3, 1)
(-0.3, -1)
(-1, -1)
(-1, 1)]
#
[(0.3, 1)
(1, 1)
(1, -1)
(0.3, -1)
(0.3, 1)]</pre>
				</div>
			</div>

			<!-- Polygon Input -->
			<FormField
				name="polygon"
				label="Polygon Coordinates"
				type="textarea"
				bind:value={polygon}
				rows={12}
				required
				helpText="Enter polygon vertices as shown in examples above"
			/>
		</div>
	{/if}
</div>

<style>
	.footprint-selector {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.footprint-section {
		background-color: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		padding: 1.5rem;
		margin-top: 1rem;
	}

	.footprint-section h4 {
		margin: 0 0 1rem 0;
		color: #374151;
		font-size: 1.125rem;
		font-weight: 600;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.polygon-instructions {
		background-color: #fef3c7;
		border: 1px solid #f59e0b;
		border-radius: 0.375rem;
		padding: 1rem;
		margin-bottom: 1rem;
	}

	.polygon-instructions h5 {
		margin: 0 0 0.5rem 0;
		color: #92400e;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.polygon-instructions ul {
		margin: 0;
		padding-left: 1.25rem;
		list-style-type: disc;
	}

	.polygon-instructions li {
		color: #78350f;
		font-size: 0.875rem;
		margin-bottom: 0.25rem;
	}

	.polygon-examples {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.example-column h6 {
		margin: 0 0 0.5rem 0;
		color: #374151;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.example-text {
		background-color: #f3f4f6;
		border: 1px solid #d1d5db;
		border-radius: 0.25rem;
		padding: 0.75rem;
		font-family: 'Courier New', monospace;
		font-size: 0.75rem;
		line-height: 1.4;
		color: #374151;
		margin: 0;
		white-space: pre-wrap;
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.form-row {
			grid-template-columns: 1fr;
		}

		.polygon-examples {
			grid-template-columns: 1fr;
		}
	}
</style>
