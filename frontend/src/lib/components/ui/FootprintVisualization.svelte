<script lang="ts">
	import { onMount } from 'svelte';
	import Plotly from 'plotly.js-dist-min';
	import { api } from '$lib/api';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';

	export let instrumentId: number;

	let plotContainer: HTMLDivElement;
	let loading = true;
	let error: string | null = null;
	let sanitizedFootprints: number[][][] = [];

	onMount(() => {
		loadFootprint();
	});

	$: if (sanitizedFootprints.length > 0 && plotContainer) {
		renderPlot(sanitizedFootprints);
	}

	async function loadFootprint() {
		try {
			loading = true;
			error = null;

			const footprints = await api.instruments.getFootprints(instrumentId);

			if (footprints.length === 0) {
				error = 'No footprint data available for this instrument.';
				return;
			}

			sanitizedFootprints = sanitizeFootprints(footprints.map((f) => f.footprint));
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load footprint data';
			console.error('Error loading footprint:', err);
		} finally {
			loading = false;
		}
	}

	function sanitizeFootprints(footprints: (string | undefined)[]): number[][][] {
		const sanitized = [];
		for (const f of footprints) {
			if (!f) continue;
			console.log('Original footprint string:', f);
			const footprint = f.replace(/POLYGON\s*\(\(/, '').replace(/\)\)$/, '');
			const points = footprint.split(',').map((p) => p.trim().split(' ').map(Number));
			console.log('Parsed points:', points);

			// Ensure polygon is closed
			if (
				points.length > 0 &&
				(points[0][0] !== points[points.length - 1][0] ||
					points[0][1] !== points[points.length - 1][1])
			) {
				console.log('Closing polygon - adding first point to end');
				points.push([...points[0]]);
			}
			console.log('Final points:', points);
			sanitized.push(points);
		}
		return sanitized;
	}

	function renderPlot(vertices: number[][][]) {
		const traces = vertices.map((vert) => ({
			x: vert.map((v) => v[0]),
			y: vert.map((v) => v[1]),
			type: 'scatter',
			mode: 'lines',
			fill: 'toself',
			fillcolor: 'violet',
			line: { color: 'blue' }
		}));

		const layout = {
			title: 'Footprint Visualization',
			xaxis: { title: 'degrees' },
			yaxis: {
				title: 'degrees',
				scaleanchor: 'x',
				scaleratio: 1,
				constrain: 'domain'
			},
			showlegend: false,
			width: 500,
			height: 500
		};

		Plotly.newPlot(plotContainer, traces, layout);
	}
</script>

<div class="w-full h-96">
	{#if loading}
		<LoadingSpinner message="Loading footprint..." />
	{:else if error}
		<ErrorMessage message={error} title="Error" type="error" />
	{:else}
		<div bind:this={plotContainer}></div>
	{/if}
</div>
