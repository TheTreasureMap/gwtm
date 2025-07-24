<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { gwtmApi, type GWAlertSchema } from '$lib/api.js';

	// Import modular components
	import AlertTypeTabs from './AlertTypeTabs.svelte';
	import AladinVisualization from './AladinVisualization.svelte';
	import FollowUpControls from './FollowUpControls.svelte';
	import TimeControls from './TimeControls.svelte';
	import EventExplorer from './EventExplorer.svelte';
	import OverlayManager from './OverlayManager.svelte';

	export let graceid: string;
	export let alert: GWAlertSchema | null = null;
	export let pointingStatus: string = 'completed';
	export let selectedAlertType: string = '';

	// Component state
	let loading = true;
	let error = '';
	let contourData: any = null;
	let footprintData: any = null;
	let coverageData: any = null;
	let sunMoonData: { sun_ra: number; sun_dec: number; moon_ra: number; moon_dec: number } | null =
		null;
	let alertTypes: any[] = [];
	let selectedAlert: GWAlertSchema | null = null;
	let galaxyData: any[] = [];
	let candidateData: any[] = [];
	let icecubeData: any[] = [];

	// Data existence flags
	let hasIceCubeData: boolean = false;
	let hasCandidateData: boolean = false;
	let detectionContours: any = null;
	let grbCoverage: any = null;

	// Control state
	let showContours = true;
	let showFootprints = true;
	let showGalaxies = false;
	let showCandidates = false;
	let showIceCube = false;
	let showGrbCoverage = true;
	let timeRange = [-1, 7]; // Days from trigger
	let minTime = -1;
	let maxTime = 7;

	// Alert type management
	let availableAlertTypes: any[] = [];
	let isLoadingAlertTypes = false;
	let isSwitchingAlert = false;

	// Aladin instance reference
	let aladin: any = null;
	let aladinVisualization: AladinVisualization;
	let overlayManager: OverlayManager;
	let plotlyContainer: HTMLDivElement;

	onMount(async () => {
		// Load alert types first (before visualization)
		if (graceid) {
			await loadAlertTypes();
			// Check for data existence like Flask does
			await checkDataExistence();
		}
		// Set loading to false after initial setup is complete
		// The AladinVisualization component will handle its own loading state
		loading = false;
	});

	// Alert type management functions
	async function loadAlertTypes() {
		if (!graceid || isLoadingAlertTypes) return;

		isLoadingAlertTypes = true;
		try {
			// Query alerts for this specific graceid only (matching Flask behavior)
			const response = await gwtmApi.queryAlerts({ graceid: graceid });
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
					return;
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

				// Sort by timesent DESC for display (newest first, matching Flask)
				availableAlertTypes = alertTypeTabs.sort(
					(a, b) => new Date(b.timesent).getTime() - new Date(a.timesent).getTime()
				);

				// Set selected alert if not already set
				if (!selectedAlert && availableAlertTypes.length > 0) {
					selectedAlert = availableAlertTypes[0].original_alert;
					selectedAlertType = availableAlertTypes[0].alert_type;
				}
			}
		} catch (err) {
			console.error('Failed to load alert types:', err);
		} finally {
			isLoadingAlertTypes = false;
		}
	}

	async function checkDataExistence() {
		// Check if IceCube data exists for this graceid (like Flask does)
		try {
			const icecubeResponse = await gwtmApi.getIceCubeNotice(graceid);
			hasIceCubeData = icecubeResponse && Object.keys(icecubeResponse).length > 0;
		} catch (error) {
			console.warn('Error checking IceCube data existence:', error);
			hasIceCubeData = false;
		}

		// Check if candidate data exists for this graceid (like Flask does)
		try {
			const candidateResponse = await gwtmApi.getCandidateAjax(graceid);
			hasCandidateData = candidateResponse && candidateResponse.length > 0;
		} catch (error) {
			console.warn('Error checking candidate data existence:', error);
			hasCandidateData = false;
		}
	}

	// Alert type switching
	async function handleAlertTypeChange(event: CustomEvent) {
		const { alertType } = event.detail;
		await switchAlertType(alertType);
	}

	async function switchAlertType(alertType: string) {
		if (!alertType || !availableAlertTypes.length || isSwitchingAlert) return;

		const newAlertTab = availableAlertTypes.find((a) => a.alert_type === alertType);
		if (newAlertTab && newAlertTab.original_alert.id !== selectedAlert?.id) {
			isSwitchingAlert = true;

			selectedAlert = newAlertTab.original_alert;
			selectedAlertType = alertType;

			// Clear existing data overlays only (preserve base sky survey to prevent flickering)
			if (aladin) {
				try {
					if (overlayManager) {
						overlayManager.clearDataOverlays();
					}
				} catch (err) {
					console.warn('Error clearing overlays:', err);
				}
			}

			// Reload visualization data for new alert
			await loadVisualizationData();
			updateVisualization();

			// Animate to new alert coordinates (matching Flask behavior)
			if (aladin && selectedAlert!.avgra !== undefined && selectedAlert!.avgdec !== undefined) {
				try {
					aladin.animateToRaDec(selectedAlert!.avgra, selectedAlert!.avgdec, 2); // 2-second animation
				} catch (err) {
					console.warn('Error animating to coordinates:', err);
				}
			}

			// Reset marker data (so they reload for new alert)
			galaxyData = [];
			candidateData = [];
			icecubeData = [];
			showGalaxies = false;
			showCandidates = false;
			showIceCube = false;

			isSwitchingAlert = false;

			// Reload footprint data for the new alert
			await reloadFootprintData();
		}
	}

	// Aladin event handlers
	function handleAladinReady(event: CustomEvent) {
		aladin = event.detail.aladin;
		console.log('Aladin ready:', !!aladin);

		// Now that Aladin is ready, load and update visualization
		loadVisualizationData().then(() => {
			updateVisualization();
			loading = false;
		});
	}

	function handleAladinError(event: CustomEvent) {
		error = event.detail.message;
		loading = false;
	}

	// Visualization data loading and management
	async function loadVisualizationData() {
		if (!graceid) return;

		try {
			// Fetch sun/moon positions from FastAPI backend (using Astropy like Flask)
			console.log('Loading visualization data, attempting to fetch sun/moon positions...');
			sunMoonData = await fetchSunMoonPositions();
			console.log('Sun/moon data result:', sunMoonData);

			// Ensure we always have sun/moon data as failsafe
			if (!sunMoonData) {
				console.log('No sun/moon data received, using default positions');
				sunMoonData = {
					sun_ra: 180.0, // Default sun position
					sun_dec: 0.0,
					moon_ra: 270.0, // Default moon position
					moon_dec: 10.0
				};
			}

			// Load detection overlays from alert data
			if (selectedAlert) {
				try {
					// Try to get detection overlays for this alert type
					const detectionData = await gwtmApi.getAlertDetectionOverlays?.(
						selectedAlert.id,
						selectedAlert.alert_type
					);
					if (detectionData) {
						detectionContours = detectionData;
					}
				} catch (err) {
					console.warn('Detection overlays loading failed:', err);
				}

				// Fallback: try generic contour loading
				if (!detectionContours && showContours) {
					try {
						contourData = await gwtmApi.getGWContour(graceid);
					} catch (err) {
						console.warn('GW contour loading failed (may require auth):', err);
						contourData = null;
					}
				}
			}

			// Load footprint data
			if (showFootprints) {
				// Calculate Time of Signal MJD like Flask does
				const tos_mjd = selectedAlert!.time_of_signal
					? convertToMJD(new Date(selectedAlert!.time_of_signal))
					: undefined;
				console.log('Loading footprint data with params:', { graceid, pointingStatus, tos_mjd });
				footprintData = await gwtmApi.getAlertInstrumentsFootprints(
					graceid,
					pointingStatus,
					tos_mjd
				);
				console.log('Loaded footprint data:', footprintData);

				// Calculate time range from footprint data
				if (footprintData && Array.isArray(footprintData)) {
					calculateTimeRange();
					console.log('Calculated time range:', { minTime, maxTime, timeRange });
				} else {
					console.log('No footprint data or not an array');
				}
			}

			// Load GRB coverage data (MOC)
			if (showGrbCoverage) {
				try {
					// This would be loaded from the same endpoint as Flask
					// For now, we'll simulate empty GRB coverage
					grbCoverage = []; // await gwtmApi.getGRBCoverage(graceid);
				} catch (err) {
					console.warn('GRB coverage loading failed:', err);
					grbCoverage = null;
				}
			}

			// Load coverage data for plotting (optional - skip during initialization)
			// This requires additional parameters like mappathinfo that are not available at init
			// The coverage calculator will be called when the user clicks "Calculate" button
			coverageData = null;
		} catch (err) {
			console.error('Failed to load visualization data:', err);
		}
	}

	async function fetchSunMoonPositions(): Promise<{
		sun_ra: number;
		sun_dec: number;
		moon_ra: number;
		moon_dec: number;
	} | null> {
		console.log('fetchSunMoonPositions called with selectedAlert:', selectedAlert);
		console.log('time_of_signal:', selectedAlert?.time_of_signal);
		// Try selectedAlert first, then fall back to alert prop
		const timeOfSignal = selectedAlert?.time_of_signal || alert?.time_of_signal;
		if (!timeOfSignal) {
			console.log('No time_of_signal available in selectedAlert or alert prop, returning null');
			return null;
		}

		try {
			console.log('Fetching sun/moon positions from FastAPI backend for:', timeOfSignal);

			// Call our temporary FastAPI endpoint (same calculation as Flask version)
			const url = `http://localhost:8000/temp_sun_moon_positions?time_of_signal=${encodeURIComponent(timeOfSignal)}`;
			console.log('Calling URL:', url);
			const response = await fetch(url);

			console.log('Response status:', response.status, response.statusText);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const data = await response.json();

			console.log('Successfully fetched sun/moon positions from FastAPI:', data);
			return {
				sun_ra: data.sun_ra,
				sun_dec: data.sun_dec,
				moon_ra: data.moon_ra,
				moon_dec: data.moon_dec
			};
		} catch (err) {
			console.error('Failed to fetch sun/moon positions from FastAPI backend:', err);

			// Fall back to approximate positions based on time
			const gwTime = new Date(timeOfSignal);
			const dayOfYear = Math.floor(
				(gwTime.getTime() - new Date(gwTime.getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24)
			);

			// Approximate sun position (very rough approximation)
			const sunRA = ((dayOfYear * 360) / 365) % 360;
			const sunDec = 23.5 * Math.sin((2 * Math.PI * (dayOfYear - 80)) / 365);

			// Approximate moon position (offset from sun by ~90 degrees as rough approximation)
			const moonRA = (sunRA + 90) % 360;
			const moonDec = sunDec * 0.5; // Rough approximation

			console.log('Using fallback sun/moon positions:', {
				sun_ra: sunRA,
				sun_dec: sunDec,
				moon_ra: moonRA,
				moon_dec: moonDec
			});

			return {
				sun_ra: sunRA,
				sun_dec: sunDec,
				moon_ra: moonRA,
				moon_dec: moonDec
			};
		}
	}

	function updateVisualization() {
		if (!aladin) return;

		try {
			// Clear existing data overlays only (preserve base sky survey)
			if (overlayManager) {
				overlayManager.clearDataOverlays();
			}

			// Add sun and moon overlays (always shown like in Flask)
			if (sunMoonData) {
				if (overlayManager) {
					overlayManager.addSunMoonOverlays();
				}
			} else {
				console.log('No sunMoonData available in updateVisualization, attempting to fetch...');
				// Try to get sun/moon data if we don't have it yet
				fetchSunMoonPositions()
					.then((data) => {
						if (data) {
							sunMoonData = data;
							if (overlayManager) {
								overlayManager.addSunMoonOverlays();
							}
						}
					})
					.catch((err) => {
						console.error('Failed to fetch sun/moon data in updateVisualization:', err);
					});
			}

			// Add a test marker to ensure something is visible
			if (aladin && alert) {
				try {
					const A = (window as any).A;
					const testCat = A.catalog({ name: 'GW Event', color: 'red', sourceSize: 15 });
					testCat.addSources([
						A.source(alert.avgra || 0, alert.avgdec || 0, { name: `GW ${graceid}` })
					]);
					aladin.addCatalog(testCat);
					console.log('Added GW event marker at:', alert.avgra, alert.avgdec);
				} catch (err) {
					console.warn('Failed to add test marker:', err);
				}
			}

			// Add gravitational wave contours (detection overlays)
			if (showContours && (contourData || detectionContours)) {
				if (overlayManager) {
					overlayManager.addContourLayer();
				}
			}

			// Add telescope footprints
			console.log('Checking footprints:', {
				showFootprints,
				footprintData: !!footprintData,
				footprintDataLength: footprintData?.length
			});
			if (showFootprints && footprintData) {
				console.log('Adding footprint layer...');
				if (overlayManager) {
					overlayManager.addFootprintLayer();
				}
			} else {
				console.log('Not adding footprints - conditions not met');
			}

			// Add galaxy markers
			if (showGalaxies) {
				if (overlayManager) {
					overlayManager.addGalaxyLayer();
				}
			}

			// Add candidate markers
			if (showCandidates) {
				if (overlayManager) {
					overlayManager.addCandidateLayer();
				}
			}

			// Add IceCube markers
			if (showIceCube) {
				if (overlayManager) {
					overlayManager.addIceCubeLayer();
				}
			}

			// Add GRB coverage (MOC)
			if (showGrbCoverage && grbCoverage) {
				if (overlayManager) {
					overlayManager.addMOCLayer(grbCoverage);
				}
			}

			// Update coverage plot
			updateCoveragePlot();
		} catch (err) {
			console.error('Failed to update visualization:', err);
		}
	}

	// Overlay management is now handled by OverlayManager component

	function updateCoveragePlot() {
		if (!plotlyContainer || !coverageData || typeof window === 'undefined') return;

		try {
			const Plotly = (window as any).Plotly;

			const data = [
				{
					x: (coverageData as any).time || [],
					y: (coverageData as any).probability || [],
					type: 'scatter',
					mode: 'lines+markers',
					name: 'Probability Coverage',
					line: { color: 'blue' }
				}
			];

			const layout = {
				title: 'Coverage vs Time',
				xaxis: { title: 'Time since trigger (hours)' },
				yaxis: { title: 'Cumulative Probability' },
				height: 300
			};

			Plotly.newPlot(plotlyContainer, data, layout, { responsive: true });
		} catch (err) {
			console.error('Failed to update coverage plot:', err);
		}
	}

	// Marker functions delegated to OverlayManager

	// Time controls event handlers
	function handleTimeRangeChange(event: CustomEvent) {
		timeRange = event.detail.timeRange;
		filterFootprintsByTime();
	}

	function handlePointingStatusChange(event: CustomEvent) {
		pointingStatus = event.detail.pointingStatus;
		reloadFootprintData();
	}

	function filterFootprintsByTime() {
		if (overlayManager) {
			overlayManager.filterFootprintsByTime();
		}
	}

	// Time-filtered footprint functions delegated to OverlayManager

	function calculateTimeRange() {
		if (!footprintData || !Array.isArray(footprintData)) return;

		try {
			let allTimes: number[] = [];

			// Extract all times from contours
			footprintData.forEach((instData: any) => {
				if (instData.contours && Array.isArray(instData.contours)) {
					instData.contours.forEach((contour: any) => {
						if (typeof contour.time === 'number') {
							allTimes.push(contour.time);
						}
					});
				}
			});

			if (allTimes.length > 0) {
				minTime = Math.min(...allTimes);
				maxTime = Math.max(...allTimes);

				// Set initial range to cover all data
				timeRange = [minTime, maxTime];

				console.log('Calculated time range:', { minTime, maxTime, timeRange });
			} else {
				// Default values if no time data found
				minTime = -1;
				maxTime = 7;
				timeRange = [-1, 7];
			}
		} catch (err) {
			console.error('Failed to calculate time range:', err);
		}
	}

	async function reloadFootprintData() {
		if (!graceid || !selectedAlert) return;

		try {
			loading = true;
			footprintData = await gwtmApi.getAlertInstrumentsFootprints(graceid, pointingStatus);

			if (footprintData && Array.isArray(footprintData)) {
				calculateTimeRange();
				updateVisualization();
			}
		} catch (err) {
			console.error('Failed to reload footprint data:', err);
		} finally {
			loading = false;
		}
	}

	// FollowUp Controls event handlers
	function handleToggleInstrument(event: CustomEvent) {
		const { target, checked } = event.detail;
		const overlayLists = overlayManager?.getOverlayLists();
		if (overlayLists) {
			toggleInstrumentOverlay(target, overlayLists.instOverlays as any[]);
		}
	}

	function handleToggleAllInstruments(event: CustomEvent) {
		const { show } = event.detail;
		toggleAllInstruments(show);
	}

	function handleToggleMarkerGroup(event: CustomEvent) {
		const { groupName, checked, dataType } = event.detail;
		// Implementation for toggling marker groups
	}

	function handleAnimateToMarker(event: CustomEvent) {
		const { markerName, dataType } = event.detail;
		if (overlayManager) {
			overlayManager.animateToMarker(markerName, getMarkerData(dataType));
		}
	}

	function handleLoadData(event: CustomEvent) {
		const { dataType } = event.detail;
		if (dataType === 'galaxies') {
			loadGalaxies();
		} else if (dataType === 'candidates') {
			loadCandidates();
		} else if (dataType === 'icecube') {
			loadIceCubeData();
		}
	}

	function getMarkerData(dataType: string) {
		switch (dataType) {
			case 'galaxies':
				return galaxyData;
			case 'candidates':
				return candidateData;
			case 'icecube':
				return icecubeData;
			default:
				return [];
		}
	}

	// Helper functions
	function toggleInstrumentOverlay(target: any, overlayList: any[]) {
		if (!target || !overlayList) return;

		try {
			const targetColor = target.dataset?.color;
			if (!targetColor) return;

			// Find overlay by color (matching Flask pattern)
			for (const overlay of overlayList) {
				if ((overlay as any).tocolor === targetColor) {
					if (target.checked) {
						(overlay as any).contour?.show();
						(overlay as any).toshow = true;
					} else {
						(overlay as any).contour?.hide();
						(overlay as any).toshow = false;
					}
					break;
				}
			}

			if (aladin) {
				aladin.view.requestRedraw();
			}
		} catch (err) {
			console.error('Failed to toggle instrument overlay:', err);
		}
	}

	function toggleAllInstruments(show: boolean) {
		const overlayLists = overlayManager?.getOverlayLists();
		if (!overlayLists || !(overlayLists.instOverlays as any[])) return;

		try {
			(overlayLists.instOverlays as any[]).forEach((overlay: any) => {
				if (overlay.contour) {
					show ? overlay.contour.show() : overlay.contour.hide();
					overlay.toshow = show;
				}
			});

			// Update all checkboxes
			const checkboxes = document.querySelectorAll('.instruments-list input[type="checkbox"]');
			checkboxes.forEach((checkbox: any) => {
				checkbox.checked = show;
			});

			if (aladin) {
				aladin.view.requestRedraw();
			}
		} catch (err) {
			console.error('Failed to toggle all instruments:', err);
		}
	}

	// Animation functions delegated to OverlayManager

	// Data loading functions
	async function loadGalaxies() {
		if (!selectedAlert?.id) return;

		try {
			galaxyData = await gwtmApi.getEventGalaxiesAjax(selectedAlert.id.toString());
			if (showGalaxies) {
				if (overlayManager) {
					overlayManager.addGalaxyLayer();
				}
			}
		} catch (err) {
			console.warn('Failed to load galaxies:', err);
			galaxyData = [];
		}
	}

	async function loadCandidates() {
		if (!graceid) return;

		try {
			candidateData = await gwtmApi.getCandidateAjax(graceid);
			if (showCandidates) {
				if (overlayManager) {
					overlayManager.addCandidateLayer();
				}
			}
		} catch (err) {
			console.warn('Failed to load candidates:', err);
			candidateData = [];
		}
	}

	async function loadIceCubeData() {
		if (!graceid) return;

		try {
			icecubeData = await gwtmApi.getIceCubeNotice(graceid);
			if (showIceCube) {
				if (overlayManager) {
					overlayManager.addIceCubeLayer();
				}
			}
		} catch (err) {
			console.warn('Failed to load IceCube data:', err);
			icecubeData = [];
		}
	}

	// Event Explorer event handlers
	async function handleCalculateCoverage() {
		if (!graceid) return;

		try {
			loading = true;

			// Call coverage calculator API
			coverageData = await gwtmApi.coverageCalculator({
				graceid: graceid,
				approx_cov: 1
			});

			// Update the plot
			updateCoveragePlot();
		} catch (err) {
			console.error('Failed to calculate coverage:', err);
			error = 'Failed to calculate coverage. Please try again.';
		} finally {
			loading = false;
		}
	}

	async function handleVisualizeRenormalizedSkymap() {
		if (!graceid || !selectedAlert) return;

		try {
			loading = true;

			const result = await (gwtmApi as any).renormalizeSkymap({
				graceid: graceid,
				alert_id: selectedAlert.id,
				approx_cov: 1
			});

			if (result && result.detection_overlays) {
				// Update visualization with renormalized contours
				detectionContours = result.detection_overlays;
				updateVisualization();

				// Update result display
				const resultDiv = document.getElementById('renorm-result');
				if (resultDiv) {
					resultDiv.innerHTML =
						'<span class="text-green-600 font-medium">The Skymap has been Renormalized (~ look up! ~)</span>';
				}
			} else {
				const resultDiv = document.getElementById('renorm-result');
				if (resultDiv) {
					resultDiv.innerHTML = '<span class="text-red-600">Done! No pointings selected.</span>';
				}
			}
		} catch (err) {
			console.error('Failed to visualize renormalized skymap:', err);
			const resultDiv = document.getElementById('renorm-result');
			if (resultDiv) {
				resultDiv.innerHTML = '<span class="text-red-600">Error in Renormalize Skymap</span>';
			}
		} finally {
			loading = false;
		}
	}

	async function handleDownloadRenormalizedSkymap() {
		if (!graceid || !selectedAlert) return;

		try {
			loading = true;

			// Update progress
			const resultDiv = document.getElementById('renorm-result');
			if (resultDiv) {
				resultDiv.innerHTML =
					'<span class="text-blue-600">Generating fits file...</span><div class="w-full bg-gray-200 rounded-full h-2 mt-2"><div class="bg-blue-600 h-2 rounded-full" style="width: 45%"></div></div>';
			}

			// Call API with download flag
			const response = await fetch(
				`/ajax_renormalize_skymap?graceid=${graceid}&alert_id=${selectedAlert.id}&approx_cov=1&download=true&_ts=${Date.now()}`
			);

			if (response.ok) {
				const blob = await response.blob();

				if (blob.size > 0) {
					// Extract filename from headers
					const contentDisposition = response.headers.get('Content-Disposition');
					let filename = 'normed_skymap.fits';

					if (contentDisposition && contentDisposition.includes('filename=')) {
						filename = contentDisposition.split('filename=')[1].split(';')[0].replace(/"/g, '');
					}

					// Create download link
					const downloadUrl = URL.createObjectURL(blob);
					const tempLink = document.createElement('a');
					tempLink.href = downloadUrl;
					tempLink.download = filename;
					tempLink.click();

					// Cleanup
					URL.revokeObjectURL(downloadUrl);

					if (resultDiv) {
						resultDiv.innerHTML =
							'<span class="text-green-600 font-medium">Download complete!</span>';
					}
				} else {
					if (resultDiv) {
						resultDiv.innerHTML =
							'<span class="text-red-600">No completed pointings selected.</span>';
					}
				}
			} else {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
		} catch (err) {
			console.error('Failed to download renormalized skymap:', err);
			const resultDiv = document.getElementById('renorm-result');
			if (resultDiv) {
				resultDiv.innerHTML =
					'<span class="text-red-600">Error Downloading Renormalized Skymap</span>';
			}
		} finally {
			loading = false;
		}
	}

	// Utility functions
	function convertToMJD(date: Date): number {
		// MJD = JD - 2400000.5
		// JD = (Unix timestamp / 86400) + 2440587.5
		const unixTimestamp = date.getTime() / 1000; // Convert to seconds
		const julianDate = unixTimestamp / 86400 + 2440587.5;
		const mjd = julianDate - 2400000.5;
		return Math.round(mjd * 1000) / 1000; // Round to 3 decimal places like Flask
	}
</script>

<div class="space-y-6">
	<!-- Alert Type Tabs -->
	<AlertTypeTabs
		{availableAlertTypes}
		{selectedAlertType}
		{loading}
		on:alertTypeChange={handleAlertTypeChange}
	/>

	{#if !error}
		<!-- Two column layout matching Flask implementation -->
		<div class="flex w-full gap-4">
			<!-- Left column: Aladin visualization (70% width) -->
			<AladinVisualization
				{graceid}
				{selectedAlert}
				{loading}
				{error}
				bind:this={aladinVisualization}
				on:aladinReady={handleAladinReady}
				on:error={handleAladinError}
			/>

			<!-- Overlay Manager (hidden component for overlay management) -->
			<OverlayManager
				{aladin}
				{footprintData}
				{contourData}
				{detectionContours}
				{galaxyData}
				{candidateData}
				{icecubeData}
				{sunMoonData}
				{grbCoverage}
				{timeRange}
				bind:this={overlayManager}
			/>

			<!-- Right column: Follow-up controls (30% width) -->
			<FollowUpControls
				{footprintData}
				{galaxyData}
				{candidateData}
				{icecubeData}
				{hasIceCubeData}
				{hasCandidateData}
				{showFootprints}
				{showGrbCoverage}
				{showGalaxies}
				{showCandidates}
				{showIceCube}
				overlayLists={overlayManager?.getOverlayLists() || {}}
				on:toggleInstrument={handleToggleInstrument}
				on:toggleAllInstruments={handleToggleAllInstruments}
				on:toggleMarkerGroup={handleToggleMarkerGroup}
				on:animateToMarker={handleAnimateToMarker}
				on:loadData={handleLoadData}
			/>
		</div>

		<!-- Time Controls Section -->
		<TimeControls
			{pointingStatus}
			{timeRange}
			{minTime}
			{maxTime}
			{loading}
			on:timeRangeChange={handleTimeRangeChange}
			on:pointingStatusChange={handlePointingStatusChange}
		/>

		<!-- Event Explorer -->
		<EventExplorer
			{selectedAlert}
			{loading}
			{error}
			{plotlyContainer}
			on:calculateCoverage={handleCalculateCoverage}
			on:visualizeRenormalizedSkymap={handleVisualizeRenormalizedSkymap}
			on:downloadRenormalizedSkymap={handleDownloadRenormalizedSkymap}
		/>
	{:else}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4">
			<div class="flex items-center">
				<div class="text-red-600 mr-3">⚠️</div>
				<div>
					<h3 class="text-lg font-medium text-red-800">Error</h3>
					<p class="text-red-700">{error}</p>
				</div>
			</div>
		</div>
	{/if}
</div>
