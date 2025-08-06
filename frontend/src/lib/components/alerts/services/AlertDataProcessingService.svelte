<!--
AlertDataProcessingService.svelte - Handles alert data loading and processing
Extracted from alerts/+page.svelte to apply service-oriented architecture patterns.
Manages alert loading, filtering, and Flask-compatible data processing.
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { api, type GWAlertSchema } from '$lib/api';
	import { errorHandler } from '$lib/utils/errorHandling';

	// Event dispatcher for service communication
	const dispatch = createEventDispatcher<{
		'alert-loaded': {
			alert: GWAlertSchema & {
				far_human?: string;
				distance_with_error?: string;
				time_coincidence_far_human?: string;
				time_sky_position_coincidence_far_human?: string;
			};
			alertExists: boolean;
		};
		'alert-error': { error: string };
		'alert-cleared': {};
	}>();

	/**
	 * Load and process alert data for a given graceid
	 * Replicates Flask's alert selection and processing logic from forms.py
	 */
	export async function loadAlert(graceid: string): Promise<void> {
		if (!graceid || graceid === 'None') {
			dispatch('alert-cleared');
			return;
		}

		try {
			// Query for ALL alerts with this graceid (matching Flask logic)
			const alertsResponse = await api.alerts.queryAlerts({ graceid });

			if (alertsResponse.alerts && alertsResponse.alerts.length > 0) {
				// Replicate Flask's alert selection logic from forms.py:331-338
				console.log(`Found ${alertsResponse.alerts.length} alerts for ${graceid}`);

				// Filter out retractions and ExtCoinc alerts (like Flask does)
				const cleanedAlerts = alertsResponse.alerts.filter(
					(alert) => alert.alert_type !== 'Retraction' && !alert.alert_type?.includes('ExtCoinc')
				);

				let selectedAlert;
				if (cleanedAlerts.length > 0) {
					// Pick the most recent clean alert (last in chronological order)
					selectedAlert = cleanedAlerts[cleanedAlerts.length - 1];
					console.log(
						`Selected clean alert: ${selectedAlert.alert_type} (${selectedAlert.datecreated})`
					);
				} else {
					// Fallback to first alert if no clean alerts available
					selectedAlert = alertsResponse.alerts[0];
					console.log(`No clean alerts found, using fallback: ${selectedAlert.alert_type}`);
				}

				// Use the FastAPI /ajax_alerttype endpoint to get complete processed data
				// This endpoint provides the same data processing that Flask does
				const urlId = `${selectedAlert.id}_${selectedAlert.alert_type}`;

				let processedAlert;
				try {
					const processedData = await api.ajax.getEventContour(urlId);

					// Map the processed data back to our alert object
					processedAlert = {
						...selectedAlert,
						// Use processed fields where available
						far_human: processedData.alert_human_far,
						distance_with_error: processedData.alert_distance_plus_error,
						area_50: processedData.alert_area_50,
						area_90: processedData.alert_area_90,
						prob_bns: processedData.alert_prob_bns,
						prob_nsbh: processedData.alert_prob_nsbh,
						prob_gap: processedData.alert_prob_gap,
						prob_bbh: processedData.alert_prob_bbh,
						prob_terrestrial: processedData.alert_prob_terrestrial,
						prob_hasns: processedData.alert_prob_hasns,
						prob_hasremenant: processedData.alert_prob_hasremenant,
						time_coincidence_far_human: processedData.alert_time_coincidence_far,
						time_sky_position_coincidence_far_human:
							processedData.alert_time_sky_position_coincidence_far
					};
					console.log('Using processed alert data from FastAPI /ajax_alerttype endpoint');
				} catch (error) {
					console.warn('Error calling /ajax_alerttype endpoint, using basic processing:', error);
					processedAlert = processAlertData(selectedAlert);
				}

				dispatch('alert-loaded', {
					alert: processedAlert,
					alertExists: true
				});
			} else {
				dispatch('alert-cleared');
			}
		} catch (error) {
			console.error('Error loading alert:', error);
			const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
			dispatch('alert-error', { error: errorMessage });
			errorHandler.showToast('Failed to load alert data. Please try again.', { type: 'error' });
		}
	}

	/**
	 * Process alert data to match Flask's processing logic
	 * Replicates the data transformation from forms.py:343-380
	 */
	function processAlertData(rawAlert: GWAlertSchema): GWAlertSchema {
		const processed = { ...rawAlert };

		// Round numerical values to match Flask precision
		if (processed.area_50 !== null && processed.area_50 !== undefined) {
			processed.area_50 = Math.round(processed.area_50 * 1000) / 1000; // 3 decimal places
		}
		if (processed.area_90 !== null && processed.area_90 !== undefined) {
			processed.area_90 = Math.round(processed.area_90 * 1000) / 1000; // 3 decimal places
		}
		if (processed.distance !== null && processed.distance !== undefined) {
			processed.distance = Math.round(processed.distance * 1000) / 1000; // 3 decimal places
		}
		if (processed.distance_error !== null && processed.distance_error !== undefined) {
			processed.distance_error = Math.round(processed.distance_error * 1000) / 1000; // 3 decimal places
		}

		// Round probability values to match Flask (5 decimal places)
		const probFields = [
			'prob_bns',
			'prob_nsbh',
			'prob_gap',
			'prob_bbh',
			'prob_terrestrial',
			'prob_hasns',
			'prob_hasremenant'
		];
		probFields.forEach((field) => {
			if (processed[field] !== null && processed[field] !== undefined) {
				processed[field] = Math.round(processed[field] * 100000) / 100000; // 5 decimal places
			}
		});

		console.log('Processed alert data:', processed);
		return processed;
	}
</script>
