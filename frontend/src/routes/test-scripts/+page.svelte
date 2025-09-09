<script lang="ts">
	import { onMount } from 'svelte';

	let aladinStatus = 'Checking...';
	let plotlyStatus = 'Checking...';
	let jqueryStatus = 'Checking...';

	onMount(() => {
		console.log('Testing external scripts...');

		// Check jQuery
		if (typeof (window as any).$ !== 'undefined') {
			jqueryStatus = 'Available';
			console.log('jQuery version:', (window as any).$.fn.jquery);
		} else {
			jqueryStatus = 'Missing';
		}

		// Check Aladin
		if (typeof (window as any).A !== 'undefined') {
			aladinStatus = 'Available';
			console.log('Aladin object:', (window as any).A);
		} else {
			aladinStatus = 'Missing';
		}

		// Check Plotly
		if (typeof (window as any).Plotly !== 'undefined') {
			plotlyStatus = 'Available';
			console.log('Plotly version:', (window as any).Plotly.version);
		} else {
			plotlyStatus = 'Missing';
		}

		// Try to create a simple Aladin instance if available
		if (typeof (window as any).A !== 'undefined') {
			try {
				const container = document.getElementById('test-aladin');
				if (container) {
					const A = (window as { A: { aladin: (selector: string, config: unknown) => unknown } }).A;
					const aladin = A.aladin('#test-aladin', {
						fov: 60,
						target: '0 0',
						showReticle: false
					});
					console.log('Test Aladin instance created successfully:', !!aladin);
				}
			} catch (err) {
				console.error('Failed to create test Aladin instance:', err);
			}
		}
	});
</script>

<svelte:head>
	<title>External Scripts Test - GWTM</title>
</svelte:head>

<div class="container mx-auto px-4 py-6">
	<h1 class="text-2xl font-bold mb-6">External Scripts Test</h1>

	<div class="space-y-4">
		<div class="bg-white shadow rounded-lg p-4">
			<h2 class="text-lg font-semibold mb-2">Script Status</h2>
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<div class="text-center">
					<h3 class="font-medium">jQuery</h3>
					<span
						class="inline-block px-3 py-1 rounded-full text-sm"
						class:bg-green-100={jqueryStatus === 'Available'}
						class:text-green-800={jqueryStatus === 'Available'}
						class:bg-red-100={jqueryStatus === 'Missing'}
						class:text-red-800={jqueryStatus === 'Missing'}
						class:bg-yellow-100={jqueryStatus === 'Checking...'}
						class:text-yellow-800={jqueryStatus === 'Checking...'}
					>
						{jqueryStatus}
					</span>
				</div>

				<div class="text-center">
					<h3 class="font-medium">Aladin Lite</h3>
					<span
						class="inline-block px-3 py-1 rounded-full text-sm"
						class:bg-green-100={aladinStatus === 'Available'}
						class:text-green-800={aladinStatus === 'Available'}
						class:bg-red-100={aladinStatus === 'Missing'}
						class:text-red-800={aladinStatus === 'Missing'}
						class:bg-yellow-100={aladinStatus === 'Checking...'}
						class:text-yellow-800={aladinStatus === 'Checking...'}
					>
						{aladinStatus}
					</span>
				</div>

				<div class="text-center">
					<h3 class="font-medium">Plotly</h3>
					<span
						class="inline-block px-3 py-1 rounded-full text-sm"
						class:bg-green-100={plotlyStatus === 'Available'}
						class:text-green-800={plotlyStatus === 'Available'}
						class:bg-red-100={plotlyStatus === 'Missing'}
						class:text-red-800={plotlyStatus === 'Missing'}
						class:bg-yellow-100={plotlyStatus === 'Checking...'}
						class:text-yellow-800={plotlyStatus === 'Checking...'}
					>
						{plotlyStatus}
					</span>
				</div>
			</div>
		</div>

		<div class="bg-white shadow rounded-lg p-4">
			<h2 class="text-lg font-semibold mb-2">Test Aladin Instance</h2>
			<div id="test-aladin" style="width: 100%; height: 400px; border: 1px solid #ccc;"></div>
		</div>

		<div class="bg-white shadow rounded-lg p-4">
			<h2 class="text-lg font-semibold mb-2">Console Output</h2>
			<p class="text-sm text-gray-600">
				Check the browser console (F12) for detailed script loading information.
			</p>
		</div>
	</div>
</div>

<style>
	.container {
		max-width: 1200px;
	}
</style>
