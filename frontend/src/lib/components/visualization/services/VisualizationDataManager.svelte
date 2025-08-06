<script lang="ts">
	/**
	 * @component VisualizationDataManager
	 * @description Service component for managing visualization data state and operations
	 * Handles contours, footprints, coverage calculation, and data coordination
	 */
	import { createEventDispatcher } from 'svelte';
	import { api, type GWAlertSchema } from '$lib/api';
	import { convertToMJD, type SunMoonData } from '$lib/utils/astronomicalCalculations.js';

	const dispatch = createEventDispatcher();

	export let graceid: string;
	export let selectedAlert: GWAlertSchema | null = null;
	export let pointingStatus: string = 'completed';
	export let showFootprints: boolean = true;
	export let showContours: boolean = true;
	export let showGrbCoverage: boolean = false;

	// Visualization data state
	let contourData: any = null;
	let footprintData: any = null;
	let coverageData: any = null;
	let grbCoverage: any = null;
	let detectionContours: any = null;

	// Time range data (numbers representing days from trigger)
	export let minTime: number = -1;
	export let maxTime: number = 7;
	export let timeRange: number[] = [-1, 7];

	/**
	 * Load all visualization data for the current alert
	 */
	export async function loadVisualizationData(
		sunMoonData: SunMoonData | null = null
	): Promise<void> {
		if (!graceid || !selectedAlert) return;

		dispatch('loading-started', { operation: 'visualization-data' });

		try {
			console.log('Loading visualization data for alert:', selectedAlert.alert_type);

			// Load detection overlays from alert data
			if (selectedAlert) {
				await loadDetectionOverlays();
			}

			// Load footprint data
			if (showFootprints) {
				await loadFootprintData();
			}

			// Load GRB coverage data (MOC)
			if (showGrbCoverage) {
				await loadGrbCoverageData();
			}

			// Coverage data is not loaded here - it's calculated on demand
			// This requires additional parameters like mappathinfo that are not available at init
			coverageData = null;

			dispatch('visualization-data-loaded', {
				contourData,
				footprintData,
				coverageData,
				grbCoverage,
				detectionContours,
				sunMoonData
			});
		} catch (err) {
			console.error('Failed to load visualization data:', err);
			dispatch('visualization-data-error', { error: err });
		} finally {
			dispatch('loading-finished', { operation: 'visualization-data' });
		}
	}

	/**
	 * Load detection overlays for the selected alert
	 */
	async function loadDetectionOverlays(): Promise<void> {
		if (!selectedAlert) {
			console.log('No selected alert for detection overlays');
			return;
		}

		console.log('Loading detection overlays for alert:', {
			selectedAlert,
			id: selectedAlert.id,
			alert_type: selectedAlert.alert_type
		});

		// Only try detection overlays if we have valid alert data
		if (selectedAlert.id && selectedAlert.alert_type) {
			try {
				console.log(
					'Calling getAlertDetectionOverlays with:',
					selectedAlert.id,
					selectedAlert.alert_type
				);
				const detectionData = await api.ajax.getAlertDetectionOverlays?.(
					selectedAlert.id,
					selectedAlert.alert_type
				);
				if (detectionData) {
					detectionContours = detectionData;
					dispatch('detection-overlays-loaded', { data: detectionData });
					console.log('Detection overlays loaded successfully');
					return; // Skip fallback if we got detection data
				}
			} catch (err) {
				console.warn('Detection overlays loading failed:', err);
			}
		} else {
			console.log('Skipping detection overlays - missing id or alert_type');
		}

		// Fallback: try generic contour loading
		if (!detectionContours && showContours && graceid) {
			try {
				console.log('Falling back to GW contour loading for:', graceid);
				contourData = await api.alerts.getGWContour(graceid);
				dispatch('contour-data-loaded', { data: contourData });
			} catch (err) {
				console.warn('GW contour loading failed (may require auth):', err);
				contourData = null;
			}
		}
	}

	/**
	 * Load footprint data with time calculations
	 */
	async function loadFootprintData(): Promise<void> {
		if (!selectedAlert) {
			console.log('Cannot load footprint data: no selected alert');
			return;
		}

		try {
			// Calculate Time of Signal MJD like Flask does
			const tos_mjd = selectedAlert.time_of_signal
				? convertToMJD(new Date(selectedAlert.time_of_signal))
				: undefined;

			console.log('Loading footprint data with params:', {
				graceid,
				pointingStatus,
				tos_mjd,
				selectedAlert: {
					id: selectedAlert.id,
					time_of_signal: selectedAlert.time_of_signal
				}
			});

			footprintData = await api.ajax.getAlertInstrumentsFootprints(graceid, pointingStatus, tos_mjd);

			console.log('Loaded footprint data:', {
				isArray: Array.isArray(footprintData),
				length: footprintData?.length,
				data: footprintData
			});

			// Calculate time range from footprint data
			if (footprintData && Array.isArray(footprintData)) {
				calculateTimeRange();
				console.log('Calculated time range:', { minTime, maxTime, timeRange });
			} else {
				console.log('No footprint data or not an array - setting default time range');
				minTime = -1;
				maxTime = 7;
				timeRange = [-1, 7];
			}

			dispatch('footprint-data-loaded', {
				data: footprintData,
				timeRange: { minTime, maxTime, timeRange }
			});
		} catch (err) {
			console.error('Failed to load footprint data:', err);
			footprintData = null;
			dispatch('footprint-data-error', { error: err });
		}
	}

	/**
	 * Load GRB coverage data
	 */
	async function loadGrbCoverageData(): Promise<void> {
		try {
			// This would be loaded from the same endpoint as Flask
			// For now, we'll simulate empty GRB coverage
			grbCoverage = []; // await gwtmApi.getGRBCoverage(graceid);
			dispatch('grb-coverage-loaded', { data: grbCoverage });
		} catch (err) {
			console.warn('GRB coverage loading failed:', err);
			grbCoverage = null;
		}
	}

	/**
	 * Calculate coverage for instruments (on-demand)
	 */
	export async function calculateCoverage(): Promise<any> {
		if (!graceid) return null;

		dispatch('coverage-calculation-started');

		try {
			console.log('Calculating coverage for graceid:', graceid);

			// This calls the coverage calculation endpoint
			coverageData = await api.ajax.coverageCalculator({ graceid });

			console.log('Coverage calculation result:', coverageData);

			dispatch('coverage-calculated', { data: coverageData });
			return coverageData;
		} catch (err) {
			console.error('Coverage calculation failed:', err);
			dispatch('coverage-calculation-error', { error: err });
			return null;
		}
	}

	/**
	 * Calculate time range from footprint data
	 */
	function calculateTimeRange(): void {
		if (!footprintData || !Array.isArray(footprintData)) {
			console.log('No footprint data for time range calculation');
			return;
		}

		console.log('Calculating time range from footprint data...');

		// Extract all contour times from all instruments
		const allTimes: number[] = [];
		const allObservationTimes: Date[] = [];

		footprintData.forEach((instrument: any, idx: number) => {
			if (instrument.contours && Array.isArray(instrument.contours)) {
				// Debug: Look at the first contour to see its structure
				if (idx === 0 && instrument.contours.length > 0) {
					console.log('Sample contour structure:', Object.keys(instrument.contours[0]));
					console.log('Sample contour data:', instrument.contours[0]);
				}

				instrument.contours.forEach((contour: any) => {
					if (typeof contour.time === 'number') {
						allTimes.push(contour.time);
					}
					// Also collect raw observation times for fallback calculation
					if (contour.observation_time) {
						allObservationTimes.push(new Date(contour.observation_time));
					}
				});
			}

			console.log(
				`Instrument ${idx} (${instrument.name}): found ${
					instrument.contours?.filter((c: any) => typeof c.time === 'number').length || 0
				} contours with time data`
			);
		});

		console.log('All extracted times:', allTimes.length, 'total times');
		console.log('Sample time values:', allTimes.slice(0, 10));

		if (allTimes.length === 0) {
			console.log('No time data found, trying to calculate from observation times...');

			if (allObservationTimes.length > 0 && selectedAlert?.time_of_signal) {
				// Calculate time differences manually if we have observation times and time of signal
				const tosDate = new Date(selectedAlert.time_of_signal);
				const calculatedTimes = allObservationTimes.map((obsTime) => {
					const diffMs = obsTime.getTime() - tosDate.getTime();
					const diffDays = diffMs / (1000 * 60 * 60 * 24);
					return diffDays;
				});

				if (calculatedTimes.length > 0) {
					const minCalcTime = Math.min(...calculatedTimes);
					const maxCalcTime = Math.max(...calculatedTimes);

					console.log('Calculated times from observation data:', {
						minCalcTime,
						maxCalcTime,
						tosDate,
						sampleObsTimes: allObservationTimes.slice(0, 3)
					});

					// If we got reasonable values, use them
					if (minCalcTime !== maxCalcTime) {
						minTime = minCalcTime;
						maxTime = maxCalcTime;
						timeRange = [minCalcTime, maxCalcTime];
						return;
					}
				}
			}

			// Final fallback: default range
			console.log('Using default range');
			minTime = -1;
			maxTime = 7;
			timeRange = [-1, 7];
			return;
		}

		const minTimeValue = Math.min(...allTimes);
		const maxTimeValue = Math.max(...allTimes);

		// Handle case where all times are the same (especially 0)
		if (minTimeValue === maxTimeValue) {
			console.warn('All time values are identical:', minTimeValue);
			if (minTimeValue === 0) {
				console.warn('All times are 0 - trying to calculate from raw observation times...');

				if (allObservationTimes.length > 0 && selectedAlert?.time_of_signal) {
					// Calculate time differences manually if we have observation times and time of signal
					const tosDate = new Date(selectedAlert.time_of_signal);
					const calculatedTimes = allObservationTimes.map((obsTime) => {
						const diffMs = obsTime.getTime() - tosDate.getTime();
						const diffDays = diffMs / (1000 * 60 * 60 * 24);
						return diffDays;
					});

					if (calculatedTimes.length > 0) {
						const minCalcTime = Math.min(...calculatedTimes);
						const maxCalcTime = Math.max(...calculatedTimes);

						console.log('Fallback calculated times:', {
							minCalcTime,
							maxCalcTime,
							tosDate,
							sampleCalculated: calculatedTimes.slice(0, 3)
						});

						// If we got reasonable values, use them
						if (Math.abs(maxCalcTime - minCalcTime) > 0.001) {
							// At least 1.44 minutes difference
							minTime = minCalcTime;
							maxTime = maxCalcTime;
							timeRange = [minCalcTime, maxCalcTime];
							return;
						}
					}
				}

				// If still no luck, use default range
				console.warn('Could not calculate meaningful time range, using default');
				minTime = -1;
				maxTime = 7;
				timeRange = [-1, 7];
				return;
			} else {
				// Expand around the single time value
				minTime = minTimeValue - 1;
				maxTime = maxTimeValue + 1;
				timeRange = [minTime, maxTime];
				return;
			}
		}

		// Set min/max as numbers (days from trigger) for TimeControls
		minTime = minTimeValue;
		maxTime = maxTimeValue;

		// timeRange should be an array [min, max] for the overlay filtering
		timeRange = [minTimeValue, maxTimeValue];

		console.log('Calculated time range:', {
			minTimeValue,
			maxTimeValue,
			timeRange,
			totalContours: allTimes.length
		});
	}

	/**
	 * Update display flags and reload data if needed
	 */
	export async function updateDisplaySettings(settings: {
		showContours?: boolean;
		showFootprints?: boolean;
		showGrbCoverage?: boolean;
	}): Promise<void> {
		const {
			showContours: newShowContours,
			showFootprints: newShowFootprints,
			showGrbCoverage: newShowGrbCoverage
		} = settings;

		let needsReload = false;

		if (newShowContours !== undefined && newShowContours !== showContours) {
			showContours = newShowContours;
			needsReload = true;
		}

		if (newShowFootprints !== undefined && newShowFootprints !== showFootprints) {
			showFootprints = newShowFootprints;
			needsReload = true;
		}

		if (newShowGrbCoverage !== undefined && newShowGrbCoverage !== showGrbCoverage) {
			showGrbCoverage = newShowGrbCoverage;
			needsReload = true;
		}

		if (needsReload) {
			await loadVisualizationData();
		}

		dispatch('display-settings-updated', {
			showContours,
			showFootprints,
			showGrbCoverage
		});
	}

	/**
	 * Clear all visualization data
	 */
	export function clearVisualizationData(): void {
		contourData = null;
		footprintData = null;
		coverageData = null;
		grbCoverage = null;
		detectionContours = null;
		minTime = -1;
		maxTime = 7;
		timeRange = [-1, 7];

		dispatch('visualization-data-cleared');
	}

	/**
	 * Get current visualization state
	 */
	export function getVisualizationState() {
		return {
			contourData,
			footprintData,
			coverageData,
			grbCoverage,
			detectionContours,
			showContours,
			showFootprints,
			showGrbCoverage,
			timeRange: { minTime, maxTime, timeRange },
			hasData: !!(contourData || footprintData || detectionContours)
		};
	}
</script>

<!-- This is a service component with no visual output -->
