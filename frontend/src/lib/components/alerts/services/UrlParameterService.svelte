<!--
UrlParameterService.svelte - URL parameter management service
Extracted from alerts/+page.svelte to apply service-oriented architecture patterns.
Manages URL parameter parsing and reactive updates for alert pages.
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Readable } from 'svelte/store';

	// Event dispatcher for parameter change notifications
	const dispatch = createEventDispatcher<{
		'parameters-updated': {
			graceid: string;
			pointingStatus: string;
			alertType: string;
			renormPath: string;
		};
	}>();

	// URL parameter state
	export let graceid = '';
	export let pointingStatus = 'completed';
	export let alertType = '';
	export let renormPath = '';

	/**
	 * Parse URL parameters from page store
	 * Reactive function that updates when page store changes
	 */
	export function parseUrlParameters(pageStore: Readable<{ url: URL }>) {
		pageStore.subscribe(($page) => {
			const newGraceid = $page.url.searchParams.get('graceids') || '';
			const newPointingStatus = $page.url.searchParams.get('pointing_status') || 'completed';
			const newAlertType = $page.url.searchParams.get('alert_type') || '';
			const newRenormPath = $page.url.searchParams.get('normed_path') || '';

			// Check if parameters have changed
			const hasChanged =
				newGraceid !== graceid ||
				newPointingStatus !== pointingStatus ||
				newAlertType !== alertType ||
				newRenormPath !== renormPath;

			if (hasChanged) {
				graceid = newGraceid;
				pointingStatus = newPointingStatus;
				alertType = newAlertType;
				renormPath = newRenormPath;

				dispatch('parameters-updated', {
					graceid,
					pointingStatus,
					alertType,
					renormPath
				});
			}
		});
	}

	/**
	 * Build URL with current parameters
	 * Useful for navigation and link generation
	 */
	export function buildUrl(
		baseUrl: string,
		overrides: Partial<{
			graceid: string;
			pointingStatus: string;
			alertType: string;
			renormPath: string;
		}> = {}
	): string {
		const params = new URLSearchParams();

		const finalParams = {
			graceid: overrides.graceid ?? graceid,
			pointingStatus: overrides.pointingStatus ?? pointingStatus,
			alertType: overrides.alertType ?? alertType,
			renormPath: overrides.renormPath ?? renormPath
		};

		if (finalParams.graceid) {
			params.set('graceids', finalParams.graceid);
		}
		if (finalParams.pointingStatus !== 'completed') {
			params.set('pointing_status', finalParams.pointingStatus);
		}
		if (finalParams.alertType) {
			params.set('alert_type', finalParams.alertType);
		}
		if (finalParams.renormPath) {
			params.set('normed_path', finalParams.renormPath);
		}

		const paramString = params.toString();
		return paramString ? `${baseUrl}?${paramString}` : baseUrl;
	}

	/**
	 * Check if we have the minimum required parameters to load an alert
	 */
	export function hasValidParameters(): boolean {
		return Boolean(graceid && graceid !== 'None');
	}

	/**
	 * Get parameters as an object for easy passing to other components
	 */
	export function getParameters() {
		return {
			graceid,
			pointingStatus,
			alertType,
			renormPath
		};
	}
</script>
