<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher, tick } from 'svelte';
	import type { GWAlertSchema } from '$lib/api.js';

	export let graceid: string;
	export let selectedAlert: GWAlertSchema | null = null;
	export const loading: boolean = false;
	export const error: string = '';

	// Internal loading state for Aladin initialization
	let aladinLoading = false; // Start false so container is rendered
	let aladinError = '';
	let showLoadingSpinner = false; // Separate state for spinner

	const dispatch = createEventDispatcher();

	let aladinContainer: HTMLDivElement;
	let aladin: any = null;
	let initializationAttempted = false;

	onMount(async () => {
		// Don't initialize immediately - wait for graceid and selectedAlert to be ready
		console.log('AladinVisualization onMount:', { graceid, selectedAlert: !!selectedAlert });
	});

	// Reactive initialization when conditions are met
	$: if (graceid && selectedAlert && !initializationAttempted) {
		console.log('Conditions met for Aladin initialization');
		showLoadingSpinner = true;
		aladinError = '';
		initializeWhenReady();
	}

	async function initializeWhenReady() {
		if (initializationAttempted) {
			console.log('Aladin initialization already attempted, skipping');
			return;
		}

		initializationAttempted = true;

		// Wait for Svelte to complete DOM updates
		await tick();

		// Additional small delay to ensure rendering is complete
		await new Promise((resolve) => setTimeout(resolve, 200));

		await awaitContainer();
	}

	onDestroy(() => {
		// Cleanup Aladin
		if (aladin) {
			try {
				aladin.removeLayers();
			} catch (e) {
				console.warn('Error cleaning up Aladin:', e);
			}
		}
	});

	async function awaitContainer(maxRetries = 30, retryDelay = 200) {
		console.log('awaitContainer started, looking for container...');

		for (let i = 0; i < maxRetries; i++) {
			console.log(`Container check attempt ${i + 1}:`);
			console.log('  - aladinContainer (binding):', !!aladinContainer);
			console.log(
				'  - aladinContainer visible:',
				aladinContainer && aladinContainer.offsetParent !== null
			);
			console.log('  - document.getElementById:', !!document.getElementById('aladin-lite-div'));
			console.log('  - aladinLoading:', aladinLoading);
			console.log('  - aladinError:', aladinError);

			// Check if container is bound and visible
			if (aladinContainer && aladinContainer.offsetParent !== null) {
				console.log('Container found via binding and is visible');
				await initializeAladin();
				return;
			}

			// Fallback: try to find by ID
			const containerById = document.getElementById('aladin-lite-div');
			if (containerById && containerById.offsetParent !== null) {
				console.log('Container found by ID and is visible');
				aladinContainer = containerById as HTMLDivElement;
				await initializeAladin();
				return;
			}

			// Wait before next attempt
			await new Promise((resolve) => setTimeout(resolve, retryDelay));
		}

		console.error('Container never became available after', maxRetries, 'attempts');
		console.log('Final state:', {
			aladinContainer: !!aladinContainer,
			containerVisible: aladinContainer && aladinContainer.offsetParent !== null,
			containerById: !!document.getElementById('aladin-lite-div'),
			aladinLoading,
			aladinError
		});

		aladinError = 'Sky map container failed to initialize. Please refresh the page.';
		showLoadingSpinner = false;
		dispatch('error', {
			message: 'Sky map container failed to initialize. Please refresh the page.'
		});
	}

	async function initializeAladin() {
		console.log('initializeAladin called with:', { graceid, alert: !!selectedAlert });

		if (!graceid || !selectedAlert) {
			console.log('Skipping initialization - missing graceid or alert');
			return;
		}

		try {
			// Check if scripts are available
			console.log('Checking for Aladin availability...');
			if (typeof window !== 'undefined' && !(window as any).A) {
				throw new Error('Aladin script not available. Please check your internet connection.');
			}
			console.log('Aladin is available:', typeof (window as any).A);

			// Container should be available by now since awaitContainer() called us
			console.log('Container check:', aladinContainer);
			if (!aladinContainer) {
				throw new Error('Aladin container still not available');
			}

			// Initialize Aladin sky map
			console.log('Initializing Aladin...');
			initAladin();
			console.log('Aladin initialized successfully:', !!aladin);

			// Ensure Aladin is visible by setting a survey
			if (aladin) {
				try {
					aladin.setImageSurvey('P/DSS2/color');
					console.log('Set default survey for visibility');
				} catch (err: any) {
					console.warn('Failed to set survey:', err);
				}
			}

			// Notify parent that Aladin is ready
			showLoadingSpinner = false;
			dispatch('aladinReady', { aladin });
		} catch (err: any) {
			console.error('Failed to initialize Aladin:', err);
			aladinError = `Failed to load visualization: ${err.message}`;
			showLoadingSpinner = false;
			dispatch('error', { message: `Failed to load visualization: ${err.message}` });
		}
	}

	function initAladin() {
		console.log('initAladin called', { aladinContainer: !!aladinContainer, window: typeof window });

		if (!aladinContainer || typeof window === 'undefined') {
			console.log('Cannot initialize Aladin - missing container or window');
			return;
		}

		try {
			const A = (window as any).A;
			console.log('Aladin object:', A);

			// Set a unique ID for the container
			aladinContainer.id = 'aladin-lite-div';
			console.log('Container ID set to:', aladinContainer.id);

			// Calculate target coordinates
			const target =
				selectedAlert?.avgra && selectedAlert?.avgdec
					? `${selectedAlert.avgra} ${selectedAlert.avgdec}`
					: '0 0';
			console.log('Target coordinates:', target);

			// Use the correct Aladin v2 API syntax matching Flask settings
			const aladinOptions = {
				fov: 180, // Match Flask default field of view
				target: target,
				showGotoControl: true,
				showFullscreenControl: true,
				showSimbadPointerControl: true,
				showShareControl: true,
				realFullscreen: false,
				cooFrame: 'ICRSd',
				showReticle: true, // Show reticle to confirm position
				survey: 'P/DSS2/color' // Set default survey
			};
			console.log('Aladin options:', aladinOptions);

			aladin = A.aladin('#aladin-lite-div', aladinOptions);
			console.log('Aladin instance created:', !!aladin);
		} catch (err) {
			console.error('Failed to initialize Aladin:', err);
			aladinError = 'Failed to initialize sky map';
			showLoadingSpinner = false;
			dispatch('error', { message: 'Failed to initialize sky map' });
		}
	}

	// Expose aladin instance to parent
	export function getAladinInstance() {
		return aladin;
	}

	// Allow parent to trigger re-initialization
	export function reinitialize() {
		initializationAttempted = false;
		aladin = null;
		showLoadingSpinner = true;
		aladinError = '';
		initializeAladin();
	}

	// Reset when graceid changes
	$: if (graceid) {
		initializationAttempted = false;
		aladin = null;
		showLoadingSpinner = false;
		aladinError = '';
	}
</script>

<!-- Left column: Aladin visualization (70% width) -->
<div style="width: 70%;">
	<div class="bg-white border rounded-lg overflow-hidden">
		<!-- Always render the container -->
		<div class="relative aladin-container-wrapper" style="height: 640px;">
			<div
				bind:this={aladinContainer}
				class="w-full aladin-container"
				style="height: 640px; position: relative; border: 2px solid #ccc; background: #000;"
				id="aladin-lite-div"
			></div>

			<!-- Loading overlay -->
			{#if showLoadingSpinner}
				<div class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 z-10">
					<div class="text-center">
						<div
							class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"
						></div>
						<p class="text-gray-600">Loading sky visualization...</p>
					</div>
				</div>
			{/if}

			<!-- Error overlay -->
			{#if aladinError}
				<div class="absolute inset-0 flex items-center justify-center bg-white z-10">
					<div class="text-center text-red-600">
						<div class="text-4xl mb-4">⚠️</div>
						<p class="font-medium">{aladinError}</p>
						<button
							class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
							on:click={reinitialize}
						>
							Retry
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.aladin-container {
		width: 100%;
		height: 640px;
		position: relative;
		border: 2px solid #ccc;
		background: #000;
	}
</style>
