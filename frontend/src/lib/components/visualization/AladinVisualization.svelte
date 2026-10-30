<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher, tick } from 'svelte';
	import type { GWAlertSchema } from '$lib/api';

	// Extended interface for processed alert data
	interface ProcessedGWAlert extends GWAlertSchema {
		original_alert?: {
			avgra?: number;
			avgdec?: number;
		};
	}

	// DSS2 colour HiPS mirrors at two organisations. Each viewer uses whichever answers
	// first, so the sky background survives an outage at either one. Full URLs rather than
	// the 'P/DSS2/color' ID, because resolving an ID needs CDS's MocServer.
	const BASE_SURVEY_MIRRORS = [
		'https://skies.esac.esa.int/DSSColor/',
		'https://alasky.cds.unistra.fr/DSS/DSSColor/',
		'https://alaskybis.cds.unistra.fr/DSS/DSSColor/'
	];
	let baseSurvey = BASE_SURVEY_MIRRORS[0];

	export let graceid: string;
	export let selectedAlert: ProcessedGWAlert | null = null;
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
		// Cleanup Aladin (v3 uses removeOverlays instead of removeLayers)
		if (aladin) {
			try {
				aladin.removeOverlays();
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

	// With every mirror down, the first is kept so overlays still draw on a blank sky.
	async function pickBaseSurvey(timeoutMs = 5000): Promise<string> {
		try {
			return await Promise.any(
				BASE_SURVEY_MIRRORS.map(async (url) => {
					const res = await fetch(`${url}properties`, { signal: AbortSignal.timeout(timeoutMs) });
					if (!res.ok) throw new Error(`${url} returned ${res.status}`);
					return url;
				})
			);
		} catch {
			console.warn('No DSS mirror responded; sky background will be missing');
			return BASE_SURVEY_MIRRORS[0];
		}
	}

	// Aladin is bundled rather than loaded from CDS so the viewer does not depend on CDS
	// being up. Pinned to 3.7.0-beta: 3.6.x drops large GW contours that are partially
	// off-screen. When updating, check outer contours stay visible while rotating the view.
	// Exposed as window.A because OverlayManager and SkyVisualization read it there.
	async function loadAladin() {
		const [{ default: A }, survey] = await Promise.all([import('aladin-lite'), pickBaseSurvey()]);
		(window as any).A = A;
		baseSurvey = survey;
	}

	async function initializeAladin() {
		console.log('initializeAladin called with:', { graceid, alert: !!selectedAlert });

		if (!graceid || !selectedAlert) {
			console.log('Skipping initialization - missing graceid or alert');
			return;
		}

		try {
			await loadAladin();

			// Container should be available by now since awaitContainer() called us
			console.log('Container check:', aladinContainer);
			if (!aladinContainer) {
				throw new Error('Aladin container still not available');
			}

			// Initialize Aladin sky map
			console.log('Initializing Aladin...');
			await initAladin();
			console.log('Aladin initialized successfully:', !!aladin);

			// Ensure Aladin is visible by setting a survey (v3 uses setBaseImageLayer)
			if (aladin) {
				try {
					aladin.setBaseImageLayer(baseSurvey);
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

	async function initAladin(): Promise<void> {
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
				selectedAlert?.original_alert?.avgra && selectedAlert?.original_alert?.avgdec
					? `${selectedAlert.original_alert.avgra} ${selectedAlert.original_alert.avgdec}`
					: '0 0';
			console.log('Target coordinates:', target);

			// Aladin Lite v3 options
			const aladinOptions = {
				fov: 180, // Match Flask initial field of view (180 degrees, later set to 200 after data loads)
				target: target,
				showGotoControl: true,
				showFullscreenControl: true,
				showSimbadPointerControl: true,
				showShareControl: true,
				realFullscreen: false,
				cooFrame: 'ICRSd',
				showReticle: false, // Match Flask setting (false initially)
				survey: baseSurvey
			};
			console.log('Aladin options:', aladinOptions);

			// v3 requires async initialization via A.init promise (WASM loading)
			await A.init;
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
	export async function reinitialize() {
		initializationAttempted = false;
		aladin = null;
		showLoadingSpinner = true;
		aladinError = '';
		await initializeAladin();
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
