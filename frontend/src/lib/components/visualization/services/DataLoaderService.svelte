<script lang="ts">
	/**
	 * @component DataLoaderService
	 * @description Service component for managing data loading operations in SkyVisualization
	 * Handles fetching of alert data, galaxy data, candidate data, and detection overlays
	 */
	import { createEventDispatcher } from 'svelte';
	import { api } from '$lib/api';
	import type { GWAlertSchema } from '$lib/api';

	const dispatch = createEventDispatcher();

	export let graceid: string;
	export const selectedAlert: GWAlertSchema | null = null;

	/**
	 * Load galaxy data for visualization
	 */
	export async function loadGalaxyData() {
		console.log('[Galaxy debug] loadGalaxyData called with graceid:', graceid);
		try {
			const galaxyData = await api.ajax.getEventGalaxiesAjax?.(graceid);
			console.log('[Galaxy debug] API response:', {
				type: typeof galaxyData,
				isArray: Array.isArray(galaxyData),
				length: Array.isArray(galaxyData) ? galaxyData.length : 'n/a',
				firstItem: Array.isArray(galaxyData) && galaxyData.length > 0 ? {
					name: galaxyData[0].name,
					markersLength: galaxyData[0].markers?.length,
					firstMarker: galaxyData[0].markers?.[0]
				} : null,
				raw: galaxyData
			});
			dispatch('galaxy-data-loaded', { data: galaxyData });
			return galaxyData || [];
		} catch (err) {
			console.error('[Galaxy debug] Failed to load galaxy data:', err);
			dispatch('galaxy-data-error', { error: err });
			return [];
		}
	}

	/**
	 * Load candidate data for visualization
	 */
	export async function loadCandidateData() {
		try {
			const candidateData = await api.ajax.getCandidateAjax?.(graceid);
			dispatch('candidate-data-loaded', { data: candidateData });
			return candidateData || [];
		} catch (err) {
			console.error('Failed to load candidate data:', err);
			dispatch('candidate-data-error', { error: err });
			return [];
		}
	}

	/**
	 * Load IceCube neutrino data
	 */
	export async function loadIceCubeData() {
		try {
			const icecubeData = await api.ajax.getIceCubeNotice?.(graceid);
			dispatch('icecube-data-loaded', { data: icecubeData });
			return icecubeData || [];
		} catch (err) {
			console.error('Failed to load IceCube data:', err);
			dispatch('icecube-data-error', { error: err });
			return [];
		}
	}

	/**
	 * Check if IceCube data exists for this alert
	 */
	export async function checkIceCubeDataExists(): Promise<boolean> {
		try {
			const icecubeData = await loadIceCubeData();
			return icecubeData && icecubeData.length > 0;
		} catch (err) {
			console.error('Failed to check IceCube data existence:', err);
			return false;
		}
	}

	/**
	 * Load all data for the visualization
	 */
	export async function loadAllData() {
		const results = await Promise.allSettled([
			loadGalaxyData(),
			loadCandidateData(),
			loadIceCubeData()
		]);

		dispatch('all-data-loaded', { results });
		return results;
	}
</script>

<!-- This is a service component with no visual output -->
