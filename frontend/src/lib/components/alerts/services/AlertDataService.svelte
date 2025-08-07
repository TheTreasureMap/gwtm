<script lang="ts">
	/**
	 * @component AlertDataService
	 * @description Service component for processing alert data, grouping, and classifications
	 * Handles alert loading, grouping by graceid, classification logic, and pointing counts
	 */
	import { createEventDispatcher } from 'svelte';
	import { api, type GWAlertSchema } from '$lib/api';

	const dispatch = createEventDispatcher();

	// Data state
	export let alerts: GWAlertSchema[] = [];
	export let groupedAlerts: any[] = [];
	export let loading: boolean = false;
	export let error: string | null = null;

	/**
	 * Load alerts with given parameters
	 */
	export async function loadAlerts(queryParams: any) {
		try {
			loading = true;
			error = null;

			// Call FastAPI to fetch alerts
			const response = await api.alerts.queryAlerts(queryParams);
			if (response) {
				alerts = response.alerts || [];

				// Group alerts by graceid for display
				groupedAlerts = groupAlertsByGraceid(alerts);

				// Get pointing counts for the grouped alerts
				if (groupedAlerts.length > 0) {
					const graceids = groupedAlerts.map((g) => g.alertname);
					await loadPointingCounts(graceids);
				}

				dispatch('alerts-loaded', {
					alerts,
					groupedAlerts,
					pagination: {
						total: response.total,
						totalPages: response.total_pages,
						hasNext: response.has_next,
						hasPrev: response.has_prev,
						currentPage: response.page
					}
				});

				return {
					alerts,
					groupedAlerts,
					total: response.total,
					totalPages: response.total_pages,
					hasNext: response.has_next,
					hasPrev: response.has_prev,
					currentPage: response.page
				};
			} else {
				alerts = [];
				groupedAlerts = [];
				dispatch('alerts-loaded', {
					alerts: [],
					groupedAlerts: [],
					pagination: {
						total: 0,
						totalPages: 0,
						hasNext: false,
						hasPrev: false,
						currentPage: 1
					}
				});

				return {
					alerts: [],
					groupedAlerts: [],
					total: 0,
					totalPages: 0,
					hasNext: false,
					hasPrev: false,
					currentPage: 1
				};
			}
		} catch (err) {
			error = err.message || 'Failed to load alerts';
			console.error('Error loading alerts:', err);
			dispatch('alerts-error', { error });
			throw err;
		} finally {
			loading = false;
		}
	}

	/**
	 * Group alerts by graceid for display
	 */
	function groupAlertsByGraceid(alertsList: any[]) {
		const grouped: Record<string, GWAlertSchema[]> = {};

		// Group alerts by graceid (or alternateid if available)
		alertsList.forEach((alert) => {
			const key = alert.alternateid || alert.graceid;
			if (!grouped[key]) {
				grouped[key] = [];
			}
			grouped[key].push(alert);
		});

		// Process each group to create the grouped alert format
		const result: any[] = [];
		for (const [graceid, alertGroup] of Object.entries(grouped)) {
			const alerts = alertGroup as GWAlertSchema[];
			// Sort alerts by date created, most recent first
			alerts.sort((a: GWAlertSchema, b: GWAlertSchema) => new Date(b.datecreated || '').getTime() - new Date(a.datecreated || '').getTime());

			const mostRecentAlert = alerts[0];
			const alertTypes = alerts.map((a: GWAlertSchema) => a.alert_type).filter(Boolean);
			const hasRetraction = alertTypes.includes('Retraction');

			// Calculate classification (like Flask version)
			let classification = 'Unknown';
			if (hasRetraction) {
				classification = 'Retracted';
			} else {
				// Use most recent alert's classification logic
				classification = getAlertClassification(mostRecentAlert);
			}

			// Format distance
			let distanceStr = 'N/A';
			if (mostRecentAlert.distance && mostRecentAlert.distance > 0) {
				const dist = Math.round(mostRecentAlert.distance * 100) / 100;
				const distErr = mostRecentAlert.distance_error
					? Math.round(mostRecentAlert.distance_error * 100) / 100
					: null;
				distanceStr = distErr ? `${dist} +/- ${distErr}` : `${dist}`;
			}

			result.push({
				alertname: graceid,
				classification: classification,
				distance: distanceStr,
				pcounts: 0, // Will be loaded separately
				alert_types: alertTypes,
				has_icecube: false, // TODO: Get icecube data
				mostRecentAlert: mostRecentAlert
			});
		}

		return result.sort((a, b) => a.alertname.localeCompare(b.alertname));
	}

	/**
	 * Get alert classification based on probabilities
	 */
	function getAlertClassification(alert: any) {
		// Classification logic matching Flask version
		if (!alert) return 'Unknown';

		// Handle Burst events
		if (alert.group === 'Burst') {
			return 'None (detected as burst)';
		}

		// Build probability list with classifications
		const probabilities = [];

		if (alert.prob_bns && alert.prob_bns > 0.01) {
			probabilities.push({ prob: alert.prob_bns, name: 'BNS' });
		}
		if (alert.prob_nsbh && alert.prob_nsbh > 0.01) {
			probabilities.push({ prob: alert.prob_nsbh, name: 'NSBH' });
		}
		if (alert.prob_bbh && alert.prob_bbh > 0.01) {
			probabilities.push({ prob: alert.prob_bbh, name: 'BBH' });
		}
		if (alert.prob_terrestrial && alert.prob_terrestrial > 0.01) {
			probabilities.push({ prob: alert.prob_terrestrial, name: 'Terrestrial' });
		}
		if (alert.prob_gap && alert.prob_gap > 0.01) {
			probabilities.push({ prob: alert.prob_gap, name: 'Mass Gap' });
		}

		// Sort by probability descending
		probabilities.sort((a, b) => b.prob - a.prob);

		// Format as "BBH: (85.2%) BNS: (12.3%) "
		if (probabilities.length === 0) {
			return 'Unknown';
		}

		return probabilities.map((p) => `${p.name}: (${(p.prob * 100).toFixed(1)}%)`).join(' ') + ' ';
	}

	/**
	 * Get alert type badges with styling configuration
	 */
	export function getAlertTypeBadges(alertTypes: string[]) {
		const badgeConfig = {
			Preliminary: { color: 'bg-yellow-100 text-yellow-800', icon: 'P' },
			Initial: { color: 'bg-blue-100 text-blue-800', icon: 'I' },
			Update: { color: 'bg-green-100 text-green-800', icon: 'U' },
			Retraction: { color: 'bg-red-100 text-red-800', icon: 'R' },
			EarlyWarning: { color: 'bg-purple-100 text-purple-800', icon: 'EW' },
			Early_Warning: { color: 'bg-purple-100 text-purple-800', icon: 'EW' },
			Publication: { color: 'bg-gray-100 text-gray-800', icon: 'PU' }
		};

		return alertTypes.map((type) => {
			const config = badgeConfig[type] || {
				color: 'bg-gray-100 text-gray-800',
				icon: type?.substring(0, 2) || '?'
			};
			return { type, ...config };
		});
	}

	/**
	 * Load pointing counts for the given graceids
	 */
	async function loadPointingCounts(graceids: string[]) {
		try {
			// Get pointing counts for each graceid using the existing pointings API
			const pointingPromises = graceids.map(async (graceid) => {
				try {
					const pointings = await api.pointings.getPointings({ graceid, status: 'completed' });
					return { graceid, count: pointings?.length || 0 };
				} catch (err) {
					console.warn(`Failed to get pointings for ${graceid}:`, err);
					return { graceid, count: 0 };
				}
			});

			const pointingCounts = await Promise.all(pointingPromises);

			// Update the grouped alerts with pointing counts
			groupedAlerts = groupedAlerts.map((alert) => {
				const countData = pointingCounts.find((pc) => pc.graceid === alert.alertname);
				return {
					...alert,
					pcounts: countData ? countData.count : 0
				};
			});

			dispatch('pointing-counts-loaded', { pointingCounts });
		} catch (err) {
			console.error('Error loading pointing counts:', err);
			// Set all counts to 0 on error
			groupedAlerts = groupedAlerts.map((alert) => ({
				...alert,
				pcounts: 0
			}));
			dispatch('pointing-counts-error', { error: err });
		}
	}

	/**
	 * Format date for display
	 */
	export function formatDate(dateString: string) {
		if (!dateString) return 'N/A';
		try {
			return new Date(dateString).toLocaleString();
		} catch {
			return dateString;
		}
	}

	/**
	 * Format number for display
	 */
	export function formatNumber(num: any) {
		if (num === null || num === undefined) return 'N/A';
		if (typeof num === 'number') {
			return num.toFixed(3);
		}
		return num;
	}
</script>

<!-- This is a service component with no visual output -->
