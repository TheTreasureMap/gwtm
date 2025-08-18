<script lang="ts">
	/**
	 * @component AlertTypeManager
	 * @description Service component for managing alert type operations in SkyVisualization
	 * Handles loading alert types, switching between alert types, and managing alert state
	 */
	import { createEventDispatcher } from 'svelte';
	import { api, type GWAlertSchema } from '$lib/api';

	const dispatch = createEventDispatcher();

	export let graceid: string;
	export let selectedAlertType: string = '';

	// State tracking
	let availableAlertTypes: any[] = [];
	let isLoadingAlertTypes = false;
	let isSwitchingAlert = false;

	/**
	 * Load available alert types for the graceid (matching Flask behavior)
	 */
	export async function loadAlertTypes(): Promise<any[]> {
		if (isLoadingAlertTypes) return availableAlertTypes;

		isLoadingAlertTypes = true;
		dispatch('loading-started', { operation: 'alert-types' });

		try {
			console.log('Loading alert types for graceid:', graceid);

			// Query alerts for this specific graceid only (matching Flask behavior)
			const response = await api.alerts.queryAlerts({ graceid: graceid });
			if (response.alerts && response.alerts.length > 0) {
				// Try exact matching first (this should be sufficient for most cases)
				let exactGraceidAlerts = response.alerts.filter(
					(alert: any) => alert.graceid === graceid || alert.alternateid === graceid
				);

				// If no exact match, try case-insensitive matching only
				if (exactGraceidAlerts.length === 0) {
					exactGraceidAlerts = response.alerts.filter(
						(alert: any) =>
							alert.graceid?.toLowerCase() === graceid?.toLowerCase() ||
							alert.alternateid?.toLowerCase() === graceid?.toLowerCase()
					);
				}

				// If we still have no alerts, something is wrong - don't fall back to all alerts
				if (exactGraceidAlerts.length === 0) {
					console.error('No alerts found for graceid:', graceid);
					availableAlertTypes = [];
					dispatch('alert-types-loaded', { data: [], count: 0 });
					return [];
				}

				// Filter out retraction alerts from tabs display (matching Flask behavior)
				const validAlerts = exactGraceidAlerts.filter(
					(alert: any) => alert.alert_type !== 'Retraction'
				);

				// Sort by datecreated ASC to match Flask processing order
				validAlerts.sort(
					(a, b) =>
						new Date(a.datecreated || a.timesent).getTime() -
						new Date(b.datecreated || b.timesent).getTime()
				);

				// Process alerts with numbering for duplicates (exactly matching Flask logic)
				const alertTypeTabs: any[] = [];

				validAlerts.forEach((alert: any) => {
					const existingTypes = alertTypeTabs.map((tab) => tab.type);
					const baseType = alert.alert_type;

					// Check if this alert type already exists
					const existingOfSameType = existingTypes.filter((type) => {
						const typeBase = type.split(' ')[0]; // Get base type without number
						return typeBase === baseType;
					});

					if (existingOfSameType.length > 0) {
						// This alert type already exists, add number
						const num = existingOfSameType.length;
						const displayType = `${baseType} ${num}`;

						alertTypeTabs.push({
							type: displayType,
							timesent: alert.timesent,
							urlid: `${alert.id}_${baseType}_${num}`,
							original_alert: alert,
							alert_type: displayType
						});
					} else {
						// First occurrence of this alert type
						alertTypeTabs.push({
							type: baseType,
							timesent: alert.timesent,
							urlid: `${alert.id}_${baseType}`,
							original_alert: alert,
							alert_type: baseType
						});
					}
				});

				// Sort by timesent ASC for display (oldest first, matching Flask chronological order)
				availableAlertTypes = alertTypeTabs.sort(
					(a, b) => new Date(a.timesent).getTime() - new Date(b.timesent).getTime()
				);
			} else {
				availableAlertTypes = [];
			}

			console.log('Loaded alert types:', availableAlertTypes.length);
			dispatch('alert-types-loaded', {
				data: availableAlertTypes,
				count: availableAlertTypes.length
			});

			return availableAlertTypes;
		} catch (err) {
			console.error('Failed to load alert types:', err);
			availableAlertTypes = [];
			dispatch('alert-types-error', { error: err });
			return [];
		} finally {
			isLoadingAlertTypes = false;
			dispatch('loading-finished', { operation: 'alert-types' });
		}
	}

	/**
	 * Get current selected alert from available alert types
	 */
	export function getSelectedAlert(): GWAlertSchema | null {
		if (!selectedAlertType || !availableAlertTypes.length) {
			return null;
		}

		const alert = availableAlertTypes.find((alert) => alert.alert_type === selectedAlertType);

		return alert || null;
	}

	/**
	 * Switch to a different alert type
	 */
	export async function switchAlertType(newAlertType: string): Promise<GWAlertSchema | null> {
		if (isSwitchingAlert || newAlertType === selectedAlertType) {
			return getSelectedAlert();
		}

		isSwitchingAlert = true;
		dispatch('alert-switch-started', {
			from: selectedAlertType,
			to: newAlertType
		});

		try {
			// Validate the alert type exists
			const alert = availableAlertTypes.find((alert) => alert.alert_type === newAlertType);

			if (!alert) {
				throw new Error(`Alert type '${newAlertType}' not found in available alerts`);
			}

			const previousAlertType = selectedAlertType;
			selectedAlertType = newAlertType;

			console.log(`Switching from '${previousAlertType}' to '${newAlertType}'`);

			dispatch('alert-switched', {
				previousAlertType,
				newAlertType,
				selectedAlert: alert
			});

			return alert;
		} catch (err) {
			console.error('Failed to switch alert type:', err);
			dispatch('alert-switch-error', {
				error: err,
				alertType: newAlertType
			});
			return null;
		} finally {
			isSwitchingAlert = false;
			dispatch('alert-switch-finished', { alertType: selectedAlertType });
		}
	}

	/**
	 * Auto-select the most appropriate alert type from available options
	 * Matches Flask logic: select the last (most recent) non-retraction alert
	 */
	export function autoSelectAlertType(): string {
		if (!availableAlertTypes.length) {
			return '';
		}

		// Flask logic: select the last alert in chronological order (most recent)
		// Since availableAlertTypes is now sorted chronologically (oldest first),
		// the last item is the most recent
		const lastAlert = availableAlertTypes[availableAlertTypes.length - 1];
		console.log(`Auto-selected alert type (most recent): ${lastAlert.alert_type}`);
		return lastAlert.alert_type;
	}

	/**
	 * Initialize alert type management for the graceid
	 */
	export async function initialize(): Promise<void> {
		console.log('Initializing AlertTypeManager for graceid:', graceid);

		// Load alert types first
		await loadAlertTypes();

		// Auto-select appropriate alert type if none specified
		if (!selectedAlertType && availableAlertTypes.length > 0) {
			const autoSelected = autoSelectAlertType();
			if (autoSelected) {
				await switchAlertType(autoSelected);
			}
		}

		dispatch('initialized', {
			alertTypes: availableAlertTypes,
			selectedAlertType,
			selectedAlert: getSelectedAlert()
		});
	}

	/**
	 * Get loading state information
	 */
	export function getLoadingState() {
		return {
			isLoadingAlertTypes,
			isSwitchingAlert,
			isLoading: isLoadingAlertTypes || isSwitchingAlert
		};
	}
</script>

<!-- This is a service component with no visual output -->
