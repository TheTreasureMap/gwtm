<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { api, type GWAlertSchema } from '$lib/api';

	// Extended interface for processed alerts with original_alert data
	interface ProcessedGWAlert extends GWAlertSchema {
		original_alert?: {
			avgra?: number;
			avgdec?: number;
		};
	}

	// Import modular components
	import AlertTypeTabs from './AlertTypeTabs.svelte';
	import AladinVisualization from './AladinVisualization.svelte';
	import FollowUpControls from './FollowUpControls.svelte';
	import TimeControls from './TimeControls.svelte';
	import EventExplorer from './EventExplorer.svelte';
	import OverlayManager from './OverlayManager.svelte';

	// Import service components
	import DataLoaderService from './services/DataLoaderService.svelte';
	import AlertTypeManager from './services/AlertTypeManager.svelte';
	import VisualizationDataManager from './services/VisualizationDataManager.svelte';
	import AlertDataProcessingService from '../alerts/services/AlertDataProcessingService.svelte';

	// Import utilities
	import {
		fetchSunMoonPositions,
		getDefaultSunMoonPositions,
		convertToMJD,
		type SunMoonData
	} from '$lib/utils/astronomicalCalculations.js';

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
	let sunMoonData: SunMoonData | null = null;
	let alertTypes: any[] = [];
	let selectedAlert: ProcessedGWAlert | null = null;
	let processedSelectedAlert: GWAlertSchema | null = null; // For SummaryTab with Flask-compatible processing
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
	let dataLoaderService: DataLoaderService;
	let alertTypeManager: AlertTypeManager;
	let visualizationDataManager: VisualizationDataManager;
	let alertDataProcessingService: AlertDataProcessingService;
	let plotlyContainer: HTMLDivElement | null = null;

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
		if (!graceid || !alertTypeManager) return;

		try {
			await alertTypeManager.initialize();
		} catch (err) {
			console.error('Failed to initialize alert type manager:', err);
		}
	}

	async function checkDataExistence() {
		// Check if IceCube data exists for this graceid (like Flask does)
		try {
			const icecubeResponse = await api.ajax.getIceCubeNotice(graceid);
			hasIceCubeData = icecubeResponse && Object.keys(icecubeResponse).length > 0;
		} catch (error) {
			console.warn('Error checking IceCube data existence:', error);
			hasIceCubeData = false;
		}

		// Check if candidate data exists for this graceid (like Flask does)
		try {
			const candidateResponse = await api.ajax.getCandidateAjax(graceid);
			hasCandidateData = candidateResponse && candidateResponse.length > 0;
		} catch (error) {
			console.warn('Error checking candidate data existence:', error);
			hasCandidateData = false;
		}
	}

	// Alert type switching
	async function handleAlertTypeChange(event: CustomEvent) {
		const { alertType } = event.detail;
		if (alertTypeManager) {
			await alertTypeManager.switchAlertType(alertType);
		}
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
			if (
				aladin &&
				selectedAlert!.original_alert?.avgra !== undefined &&
				selectedAlert!.original_alert?.avgdec !== undefined
			) {
				try {
					aladin.animateToRaDec(
						selectedAlert!.original_alert.avgra,
						selectedAlert!.original_alert.avgdec,
						2
					); // 2-second animation
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
			// Fetch sun/moon positions first
			console.log('Loading visualization data, attempting to fetch sun/moon positions...');
			sunMoonData = await loadSunMoonData();
			console.log('Sun/moon data result:', sunMoonData);

			// Ensure we always have sun/moon data as failsafe
			if (!sunMoonData) {
				console.log('No sun/moon data received, using default positions');
				sunMoonData = getDefaultSunMoonPositions();
			}

			// Load visualization data using the service
			if (visualizationDataManager) {
				await visualizationDataManager.loadVisualizationData(sunMoonData);
			}
		} catch (err) {
			console.error('Failed to load visualization data:', err);
		}
	}

	async function loadSunMoonData(): Promise<SunMoonData | null> {
		// Try selectedAlert first, then fall back to alert prop
		const timeOfSignal = selectedAlert?.time_of_signal || alert?.time_of_signal;
		if (!timeOfSignal) {
			console.log('No time_of_signal available, using defaults');
			return getDefaultSunMoonPositions();
		}

		const result = await fetchSunMoonPositions(timeOfSignal);
		return result || getDefaultSunMoonPositions();
	}

	// Data loader service event handlers
	function handleGalaxyDataLoaded(event: CustomEvent<{ data: any[] }>) {
		galaxyData = event.detail.data;
		console.log('Galaxy data loaded:', galaxyData.length, 'galaxies');
	}

	function handleCandidateDataLoaded(event: CustomEvent<{ data: any[] }>) {
		candidateData = event.detail.data;
		console.log('Candidate data loaded:', candidateData.length, 'candidates');
	}

	function handleIceCubeDataLoaded(event: CustomEvent<{ data: any[] }>) {
		icecubeData = event.detail.data;
		hasIceCubeData = icecubeData.length > 0;
		console.log('IceCube data loaded:', icecubeData.length, 'events');
	}

	// AlertTypeManager event handlers
	function handleAlertTypesLoaded(event: CustomEvent<{ data: any[]; count: number }>) {
		availableAlertTypes = event.detail.data;
		console.log('Alert types loaded:', event.detail.count, 'types');
	}

	function handleAlertSwitched(
		event: CustomEvent<{ previousAlertType: string; newAlertType: string; selectedAlert: any }>
	) {
		const { previousAlertType, newAlertType, selectedAlert: newSelectedAlert } = event.detail;

		// Update component state
		selectedAlert = newSelectedAlert;
		selectedAlertType = newAlertType;

		console.log(`Alert switched from '${previousAlertType}' to '${newAlertType}'`);

		// Load processed alert data for SummaryTab
		if (newSelectedAlert && graceid) {
			loadProcessedAlertData();
		}

		// Clear existing data and reload visualization
		clearDataForAlertSwitch();
		loadVisualizationData();
	}

	function handleAlertTypeManagerInitialized(
		event: CustomEvent<{ alertTypes: any[]; selectedAlertType: string; selectedAlert: any }>
	) {
		const {
			alertTypes,
			selectedAlertType: initSelectedType,
			selectedAlert: initSelectedAlert
		} = event.detail;

		availableAlertTypes = alertTypes;
		selectedAlertType = initSelectedType;
		selectedAlert = initSelectedAlert;

		console.log('AlertTypeManager initialized with', alertTypes.length, 'alert types');

		// Load processed alert data for SummaryTab
		if (initSelectedAlert && graceid) {
			loadProcessedAlertData();
		}

		// Load visualization data after initialization
		if (selectedAlert) {
			loadVisualizationData();
		}
	}

	function clearDataForAlertSwitch() {
		// Reset marker data (so they reload for new alert)
		galaxyData = [];
		candidateData = [];
		icecubeData = [];
		showGalaxies = false;
		showCandidates = false;
		showIceCube = false;

		// Clear visualization data
		if (visualizationDataManager) {
			visualizationDataManager.clearVisualizationData();
		}

		// Clear existing data overlays only (preserve base sky survey to prevent flickering)
		if (aladin) {
			try {
				if (overlayManager) {
					overlayManager.clearDataOverlays();
				}
			} catch (err) {
				console.warn('Error clearing overlays during alert switch:', err);
			}
		}
	}

	async function loadProcessedAlertData() {
		if (!selectedAlert || !graceid || !alertDataProcessingService) return;

		try {
			console.log('Loading processed alert data for SummaryTab...');
			await alertDataProcessingService.loadAlert(graceid);
		} catch (err) {
			console.error('Failed to load processed alert data:', err);
		}
	}

	// VisualizationDataManager event handlers
	function handleVisualizationDataLoaded(
		event: CustomEvent<{
			contourData: any;
			footprintData: any;
			coverageData: any;
			grbCoverage: any;
			detectionContours: any;
			sunMoonData: any;
		}>
	) {
		const {
			contourData: newContourData,
			footprintData: newFootprintData,
			detectionContours: newDetectionContours
		} = event.detail;

		// Update local state for components that need direct access
		contourData = newContourData;
		footprintData = newFootprintData;
		detectionContours = newDetectionContours;

		console.log('Visualization data loaded via service');

		// Ensure time range is calculated if we have footprint data
		// (This is a safeguard in case the footprint-data-loaded event doesn't fire)
		if (newFootprintData && Array.isArray(newFootprintData) && minTime === -1 && maxTime === 7) {
			console.log('Time range still at default values, checking if service calculated it...');
			// Fallback: calculate min/max time from footprintData contours
			const times: number[] = [];
			newFootprintData.forEach((instrument: any) => {
				if (instrument.contours && Array.isArray(instrument.contours)) {
					instrument.contours.forEach((contour: any) => {
						if (typeof contour.time === 'number' && !isNaN(contour.time)) {
							times.push(contour.time);
						}
					});
				}
			});
			if (times.length > 0) {
				minTime = Math.min(...times);
				maxTime = Math.max(...times);
				timeRange = [minTime, maxTime];
				console.log('Calculated time range from footprintData contours:', {
					minTime,
					maxTime,
					timeRange
				});
			} else {
				console.warn('Could not calculate time range from footprintData contours');
			}
		}

		// Update visualization after data loads
		updateVisualization();
	}

	function handleFootprintDataLoaded(event: CustomEvent<{ data: any; timeRange: any }>) {
		const { data, timeRange: timeRangeData } = event.detail;
		footprintData = data;

		// Explicitly update time range from the event data
		if (timeRangeData) {
			minTime = timeRangeData.minTime;
			maxTime = timeRangeData.maxTime;
			timeRange = timeRangeData.timeRange;
			console.log('Updated time range from event:', { minTime, maxTime, timeRange });
		} else {
			console.log('No time range data in event, using binding values:', {
				minTime,
				maxTime,
				timeRange
			});
		}
	}

	function handleCoverageCalculated(event: CustomEvent<{ data: any }>) {
		coverageData = event.detail.data;
		console.log('Coverage calculated:', coverageData);

		// Update the coverage plot
		updateCoveragePlot();
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
				loadSunMoonData()
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
			if (aladin && selectedAlert?.original_alert) {
				try {
					const A = (window as any).A;
					const testCat = A.catalog({ name: 'GW Event', color: 'red', sourceSize: 15 });
					testCat.addSources([
						A.source(
							selectedAlert.original_alert.avgra || 0,
							selectedAlert.original_alert.avgdec || 0,
							{ name: `GW ${graceid}` }
						)
					]);
					aladin.addCatalog(testCat);
					console.log(
						'Added GW event marker at:',
						selectedAlert.original_alert.avgra,
						selectedAlert.original_alert.avgdec
					);
				} catch (err) {
					console.warn('Failed to add test marker:', err);
				}
			}

			// Add telescope footprints first (so contours appear on top)
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

			// Add gravitational wave contours (detection overlays) on top
			if (showContours && (contourData || detectionContours)) {
				if (overlayManager) {
					overlayManager.addContourLayer();
				}
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

			// Center on alert coordinates after all overlays are loaded (matching Flask behavior)
			if (
				selectedAlert?.original_alert?.avgra !== undefined &&
				selectedAlert?.original_alert?.avgdec !== undefined
			) {
				try {
					aladin.animateToRaDec(
						selectedAlert.original_alert.avgra,
						selectedAlert.original_alert.avgdec,
						2
					); // 2-second animation
					aladin.setFov(200.0); // Set FOV to 200 degrees like Flask does after loading data
				} catch (err) {
					console.warn('Failed to center on alert coordinates after data load:', err);
				}
			}
		} catch (err) {
			console.error('Failed to update visualization:', err);
		}
	}

	// Overlay management is now handled by OverlayManager component

	function updateCoveragePlot() {
		if (!coverageData || typeof window === 'undefined') return;

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

			if (plotlyContainer) {
				Plotly.newPlot(plotlyContainer, data, layout, { responsive: true });
			}
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
	// Time range calculation is now handled by VisualizationDataManager service

	async function reloadFootprintData() {
		if (!graceid || !selectedAlert) return;

		try {
			loading = true;

			// Calculate Time of Signal MJD like Flask does
			const tos_mjd = selectedAlert.time_of_signal
				? convertToMJD(new Date(selectedAlert.time_of_signal))
				: undefined;

			footprintData = await api.ajax.getAlertInstrumentsFootprints(
				graceid,
				pointingStatus,
				tos_mjd
			);

			if (footprintData && Array.isArray(footprintData)) {
				// Time range calculation is handled by VisualizationDataManager service
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

		if (dataLoaderService) {
			await dataLoaderService.loadGalaxyData();
			if (showGalaxies) {
				if (overlayManager) {
					overlayManager.addGalaxyLayer();
				}
			}
		}
	}

	async function loadCandidates() {
		if (!graceid) return;

		if (dataLoaderService) {
			await dataLoaderService.loadCandidateData();
			if (showCandidates) {
				if (overlayManager) {
					overlayManager.addCandidateLayer();
				}
			}
		}
	}

	async function loadIceCubeData() {
		if (!graceid) return;

		if (dataLoaderService) {
			await dataLoaderService.loadIceCubeData();
			if (showIceCube) {
				if (overlayManager) {
					overlayManager.addIceCubeLayer();
				}
			}
		}
	}

	// AlertDataProcessingService event handlers
	function handleProcessedAlertLoaded(event: CustomEvent) {
		const { alert: loadedAlert } = event.detail;
		processedSelectedAlert = loadedAlert;
		console.log('Processed alert data loaded for SummaryTab:', processedSelectedAlert);
	}

	function handleProcessedAlertCleared() {
		processedSelectedAlert = null;
		console.log('Processed alert data cleared');
	}

	function handleProcessedAlertError(event: CustomEvent) {
		console.error('Processed alert loading error:', event.detail.error);
		processedSelectedAlert = null;
	}

	// Event Explorer event handlers
	async function handleCalculateCoverage() {
		if (!graceid || !visualizationDataManager) return;

		try {
			loading = true;
			await visualizationDataManager.calculateCoverage();
			// updateCoveragePlot will be called by the event handler
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

			const result = await (api as any).renormalizeSkymap({
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

	// Utility functions now imported from astronomicalCalculations.js
</script>

<div class="space-y-6">
	<!-- Service Components (no visual output) -->
	<DataLoaderService
		{graceid}
		{selectedAlert}
		bind:this={dataLoaderService}
		on:galaxy-data-loaded={handleGalaxyDataLoaded}
		on:candidate-data-loaded={handleCandidateDataLoaded}
		on:icecube-data-loaded={handleIceCubeDataLoaded}
	/>

	<AlertTypeManager
		{graceid}
		{selectedAlertType}
		bind:this={alertTypeManager}
		on:alert-types-loaded={handleAlertTypesLoaded}
		on:alert-switched={handleAlertSwitched}
		on:initialized={handleAlertTypeManagerInitialized}
	/>

	<VisualizationDataManager
		{graceid}
		{selectedAlert}
		{pointingStatus}
		{showFootprints}
		{showContours}
		{showGrbCoverage}
		bind:minTime
		bind:maxTime
		bind:timeRange
		bind:this={visualizationDataManager}
		on:visualization-data-loaded={handleVisualizationDataLoaded}
		on:footprint-data-loaded={handleFootprintDataLoaded}
		on:coverage-calculated={handleCoverageCalculated}
	/>

	<AlertDataProcessingService
		bind:this={alertDataProcessingService}
		on:alert-loaded={handleProcessedAlertLoaded}
		on:alert-cleared={handleProcessedAlertCleared}
		on:alert-error={handleProcessedAlertError}
	/>

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
			selectedAlert={processedSelectedAlert || selectedAlert}
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
