<!--
AlertStatusService.svelte - Alert status and classification utilities
Extracted from alerts/+page.svelte to apply service-oriented architecture patterns.
Provides helper functions for alert status detection and classification.
-->
<script lang="ts">
	import type { GWAlertSchema } from '$lib/api';

	/**
	 * Check if an alert has been retracted
	 */
	export function isRetracted(alert: GWAlertSchema): boolean {
		return alert.alert_type?.toLowerCase().includes('retraction') || false;
	}

	/**
	 * Check if a graceid represents a test event
	 * Test events start with 'MS' prefix
	 */
	export function isTestEvent(graceid: string): boolean {
		return graceid.startsWith('MS');
	}

	/**
	 * Generate GraceDB URL for a given graceid
	 */
	export function getGraceDbUrl(graceid: string): string {
		return `https://gracedb.ligo.org/superevents/${graceid}/view/`;
	}

	/**
	 * Get status badge information for an alert
	 * Returns styling and content for status badges
	 */
	export function getStatusBadge(alert: GWAlertSchema, graceid: string) {
		if (isRetracted(alert)) {
			return {
				type: 'retracted',
				title: '⚠️ RETRACTED',
				color: 'bg-red-100 border-red-500 text-red-700',
				borderClass: 'border-l-4'
			};
		} else if (isTestEvent(graceid)) {
			return {
				type: 'test',
				title: 'Test Event',
				message:
					'This is a test event. These events and pointings are automatically deleted every 48 hours',
				color: 'bg-yellow-100 border-yellow-500 text-yellow-700',
				borderClass: 'border-l-4'
			};
		}
		return null;
	}

	/**
	 * Get special download links for specific events
	 * Some events have special downloadable files
	 */
	export function getSpecialDownloads(graceid: string) {
		if (graceid === 'S200219ac') {
			return [
				{
					url: '/static/S200219ac_GBM_Event1_healpix.fit',
					title: 'Download GBM HEALPix FITS file',
					filename: 'S200219ac_GBM_Event1_healpix.fit'
				},
				{
					url: '/static/S200219ac_GBM_Event1_skymap.png',
					title: 'Download GBM Skymap png file',
					filename: 'S200219ac_GBM_Event1_skymap.png'
				}
			];
		}
		return [];
	}
</script>
