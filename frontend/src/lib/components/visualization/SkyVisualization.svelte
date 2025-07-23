<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { gwtmApi, type GWAlertSchema } from '$lib/api.js';

	export let graceid: string;
	export let alert: GWAlertSchema | null = null;
	export let pointingStatus: string = 'completed';
	export let selectedAlertType: string = '';

	let aladinContainer: HTMLDivElement;
	let aladin: any;
	let plotlyContainer: HTMLDivElement;
	
	// Component state
	let loading = true;
	let error = '';
	let contourData: any = null;
	let footprintData: any = null;
	let coverageData: any = null;
	let sunMoonData: { sun_ra: number, sun_dec: number, moon_ra: number, moon_dec: number } | null = null;
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
	let currentTab = 'info'; // 'info', 'coverage', 'renorm'
	
	// Alert type management  
	let availableAlertTypes: any[] = [];
	
	let isLoadingAlertTypes = false;
	let isSwitchingAlert = false;
	
	// Overlay management
	let overlayLists = {
		instOverlays: [],
		detectionOverlays: [],
		grbOverlays: [],
		galaxyMarkers: [],
		candidateMarkers: [],
		icecubeMarkers: []
	};

	onMount(async () => {
		// Load alert types first (before visualization)
		if (graceid) {
			await loadAlertTypes();
			// Check for data existence like Flask does
			await checkDataExistence();
		}
		
		// Use tick to ensure DOM is fully rendered
		await tick();
		
		// Wait for container to be available with retries
		awaitContainer();
	});
	
	async function awaitContainer(maxRetries = 20, retryDelay = 200) {
		// Also try to find container by ID as backup
		const findContainerById = () => document.getElementById('aladin-lite-div');
		
		for (let i = 0; i < maxRetries; i++) {
			const containerByBinding = aladinContainer;
			const containerById = findContainerById();
			
			if (containerByBinding || containerById) {
				// Use whichever container we found
				if (!aladinContainer && containerById) {
					aladinContainer = containerById as HTMLDivElement;
					console.log('Using container found by ID');
				}
				
				console.log(`Container found on attempt ${i + 1}`);
				await initializeVisualization();
				return;
			}
			
			await new Promise(resolve => setTimeout(resolve, retryDelay));
		}
		
		console.error('Container never became available');
		console.log('Final state check:', {
			aladinContainer,
			documentBody: document.body,
			alladinDivs: document.querySelectorAll('[id*="aladin"]'),
			allDivs: document.querySelectorAll('div').length
		});
		error = 'Aladin container failed to initialize. Please refresh the page.';
		loading = false;
	}

	onDestroy(() => {
		// Cleanup Aladin
		if (aladin) {
			try {
				aladin.removeLayers();
			} catch (e) {
				console.warn('Error cleaning up Aladin:', e);
			}
		}
		
		// Cleanup drag event listeners
		if (typeof window !== 'undefined') {
			document.removeEventListener('mousemove', handleDrag);
			document.removeEventListener('mouseup', stopDrag);
			document.removeEventListener('touchmove', handleDrag);
			document.removeEventListener('touchend', stopDrag);
		}
	});

	async function initializeVisualization() {
		console.log('initializeVisualization called with:', { graceid, alert: !!alert });
		
		if (!graceid || !alert) {
			console.log('Skipping initialization - missing graceid or alert');
			return;
		}
		
		loading = true;
		error = '';

		try {
			// Check if scripts are available
			console.log('Checking for Aladin availability...');
			if (typeof window !== 'undefined' && !(window as any).A) {
				throw new Error('Aladin script not available. Please check your internet connection.');
			}
			console.log('Aladin is available:', typeof (window as any).A);
			
			console.log('Checking for Plotly availability...');
			if (typeof window !== 'undefined' && !(window as any).Plotly) {
				throw new Error('Plotly script not available. Please check your internet connection.');
			}
			console.log('Plotly is available:', typeof (window as any).Plotly);
			
			// Container should be available by now since awaitContainer() called us
			console.log('Container check:', aladinContainer);
			if (!aladinContainer) {
				throw new Error('Aladin container still not available');
			}
			
			// Initialize Aladin sky map
			console.log('Initializing Aladin...');
			initAladin();
			console.log('Aladin initialized successfully:', !!aladin);
			
			// Ensure Aladin is visible by setting a survey
			if (aladin) {
				try {
					aladin.setImageSurvey('P/DSS2/color');
					console.log('Set default survey for visibility');
				} catch (err: any) {
					console.warn('Failed to set survey:', err);
				}
			}
			
			// Load data
			console.log('Loading visualization data...');
			await loadVisualizationData();
			
			// Update visualization
			console.log('Updating visualization...');
			updateVisualization();
			console.log('Visualization ready');
			
		} catch (err: any) {
			console.error('Failed to initialize visualization:', err);
			error = `Failed to load visualization: ${err.message}`;
		} finally {
			loading = false;
		}
	}

	// Scripts are now loaded statically in app.html, so no dynamic loading needed

	async function fetchSunMoonPositions(): Promise<{ sun_ra: number, sun_dec: number, moon_ra: number, moon_dec: number } | null> {
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
			const dayOfYear = Math.floor((gwTime.getTime() - new Date(gwTime.getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24));
			
			// Approximate sun position (very rough approximation)
			const sunRA = (dayOfYear * 360 / 365) % 360;
			const sunDec = 23.5 * Math.sin(2 * Math.PI * (dayOfYear - 80) / 365);
			
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

	async function fetchHorizonsPosition(command: string, startDate: string, stopDate: string, name: string): Promise<{ ra: number, dec: number } | null> {
		try {
			// JPL Horizons API parameters - build URL manually to avoid quote issues
			const baseUrl = 'https://ssd.jpl.nasa.gov/api/horizons.api';
			const params = [
				'format=json',
				`COMMAND='${command}'`,
				'EPHEM_TYPE=OBSERVER',
				'CENTER=500@399',
				`START_TIME='${startDate}'`,
				`STOP_TIME='${stopDate}'`,
				'STEP_SIZE=1d',
				'QUANTITIES=1',
				'CSV_FORMAT=YES'
			].join('&');

			const url = `${baseUrl}?${params}`;
			console.log(`Fetching ${name} position from:`, url);

			const response = await fetch(url, {
				mode: 'cors',
				cache: 'default'
			});
			
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const data = await response.json();
			
			// Parse the CSV-like result from Horizons
			if (data.result) {
				const position = parseHorizonsResult(data.result);
				console.log(`${name} position:`, position);
				return position;
			}

			throw new Error(`No result data for ${name}`);
		} catch (err) {
			console.error(`Failed to fetch ${name} position:`, err);
			return null;
		}
	}

	function parseHorizonsResult(result: string): { ra: number, dec: number } | null {
		try {
			console.log('Parsing Horizons result...');
			
			// Split result into lines
			const lines = result.split('\n');
			
			// Find the data line (after "$SOE" and before "$EOE")
			let dataStarted = false;
			let dataLines: any[] = [];
			
			for (const line of lines) {
				if (line.includes('$SOE')) {
					dataStarted = true;
					continue;
				}
				if (line.includes('$EOE')) {
					break;
				}
				if (dataStarted && line.trim()) {
					dataLines.push(line);
					console.log('Data line found:', line);
				}
			}
			
			console.log('All data lines:', dataLines);
			
			// Process the first data line
			if (dataLines.length > 0) {
				const line = dataLines[0];
				
				// Parse CSV format: Date, , , RA_(ICRF), DEC__(ICRF)
				// Example: " 2025-Mar-19 00:00, , , 15 03 41.14, -21 40 28.5,"
				const parts = line.split(',');
				console.log('CSV parts:', parts);
				
				if (parts.length >= 5) {
					// RA is in HMS format: "15 03 41.14" (hours minutes seconds)
					const raStr = parts[3].trim(); // " 15 03 41.14"
					const decStr = parts[4].trim(); // " -21 40 28.5"
					
					console.log('RA string:', raStr);
					console.log('DEC string:', decStr);
					
					// Convert HMS to decimal degrees
					const ra = parseHMSToDegrees(raStr);
					// Convert DMS to decimal degrees  
					const dec = parseDMSToDegrees(decStr);
					
					if (ra !== null && dec !== null) {
						console.log('Parsed coordinates:', { ra, dec });
						return { ra, dec };
					}
				}
			}
			
			throw new Error('Could not parse coordinates from result');
		} catch (err) {
			console.error('Failed to parse Horizons result:', err);
			console.error('Raw result:', result);
			return null;
		}
	}

	function parseHMSToDegrees(hmsStr: string): number | null {
		try {
			// Parse "HH MM SS.SS" format to decimal degrees
			const parts = hmsStr.trim().split(/\s+/);
			if (parts.length >= 3) {
				const hours = parseFloat(parts[0]);
				const minutes = parseFloat(parts[1]);
				const seconds = parseFloat(parts[2]);
				
				if (!isNaN(hours) && !isNaN(minutes) && !isNaN(seconds)) {
					// Convert to degrees: hours * 15 + minutes/4 + seconds/240
					const degrees = hours * 15 + minutes / 4 + seconds / 240;
					return degrees;
				}
			}
			return null;
		} catch (err) {
			console.error('Failed to parse HMS:', hmsStr, err);
			return null;
		}
	}

	function parseDMSToDegrees(dmsStr: string): number | null {
		try {
			// Parse "±DD MM SS.S" format to decimal degrees
			const parts = dmsStr.trim().split(/\s+/);
			if (parts.length >= 3) {
				const degrees = parseFloat(parts[0]);
				const minutes = parseFloat(parts[1]);
				const seconds = parseFloat(parts[2]);
				
				if (!isNaN(degrees) && !isNaN(minutes) && !isNaN(seconds)) {
					// Convert to decimal degrees
					const sign = degrees < 0 ? -1 : 1;
					const absDegrees = Math.abs(degrees);
					const decimalDegrees = sign * (absDegrees + minutes / 60 + seconds / 3600);
					return decimalDegrees;
				}
			}
			return null;
		} catch (err) {
			console.error('Failed to parse DMS:', dmsStr, err);
			return null;
		}
	}

	function initAladin() {
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
			const target = selectedAlert?.avgra && selectedAlert?.avgdec 
				? `${selectedAlert.avgra} ${selectedAlert.avgdec}` 
				: alert?.avgra && alert?.avgdec 
					? `${alert.avgra} ${alert.avgdec}`
					: '0 0';
			console.log('Target coordinates:', target);
			
			// Use the correct Aladin v2 API syntax matching Flask settings
			const aladinOptions = {
				fov: 180, // Match Flask default field of view
				target: target,
				showGotoControl: true,
				showFullscreenControl: true,
				showSimbadPointerControl: true,
				showShareControl: true,
				realFullscreen: false,
				cooFrame: 'ICRSd',
				showReticle: true, // Show reticle to confirm position
				survey: 'P/DSS2/color' // Set default survey
			};
			console.log('Aladin options:', aladinOptions);
			
			aladin = A.aladin('#aladin-lite-div', aladinOptions);
			console.log('Aladin instance created:', !!aladin);

		} catch (err) {
			console.error('Failed to initialize Aladin:', err);
			error = 'Failed to initialize sky map';
		}
	}

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
					sun_ra: 180.0,   // Default sun position
					sun_dec: 0.0,
					moon_ra: 270.0,  // Default moon position 
					moon_dec: 10.0
				};
			}

			// Load detection overlays from alert data
			if (selectedAlert) {
				try {
					// Try to get detection overlays for this alert type
					const detectionData = await gwtmApi.getAlertDetectionOverlays?.(selectedAlert.id, selectedAlert.alert_type);
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
				const tos_mjd = selectedAlert!.time_of_signal ? convertToMJD(new Date(selectedAlert!.time_of_signal)) : undefined;
				footprintData = await gwtmApi.getAlertInstrumentsFootprints(graceid, pointingStatus, tos_mjd);
				
				// Calculate time range from footprint data
				if (footprintData && Array.isArray(footprintData)) {
					calculateTimeRange();
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

	function updateVisualization() {
		if (!aladin) return;

		try {
			// Clear existing data overlays only (preserve base sky survey)
			clearDataOverlays();

			// Add sun and moon overlays (always shown like in Flask)
			if (sunMoonData) {
				addSunMoonOverlays();
			} else {
				console.log('No sunMoonData available in updateVisualization, attempting to fetch...');
				// Try to get sun/moon data if we don't have it yet
				fetchSunMoonPositions().then(data => {
					if (data) {
						sunMoonData = data;
						addSunMoonOverlays();
					}
				}).catch(err => {
					console.error('Failed to fetch sun/moon data in updateVisualization:', err);
				});
			}
			
			// Add a test marker to ensure something is visible
			if (aladin && alert) {
				try {
					const A = (window as any).A;
					const testCat = A.catalog({name: 'GW Event', color: 'red', sourceSize: 15});
					testCat.addSources([A.source(alert.avgra || 0, alert.avgdec || 0, {name: `GW ${graceid}`})]);
					aladin.addCatalog(testCat);
					console.log('Added GW event marker at:', alert.avgra, alert.avgdec);
				} catch (err) {
					console.warn('Failed to add test marker:', err);
				}
			}

			// Add gravitational wave contours (detection overlays)
			if (showContours && (contourData || detectionContours)) {
				addContourLayer();
			}

			// Add telescope footprints
			if (showFootprints && footprintData) {
				addFootprintLayer();
			}

			// Add galaxy markers
			if (showGalaxies) {
				addGalaxyLayer();
			}

			// Add candidate markers
			if (showCandidates) {
				addCandidateLayer();
			}

			// Add IceCube markers
			if (showIceCube) {
				addIceCubeLayer();
			}

			// Add GRB coverage (MOC)
			if (showGrbCoverage && grbCoverage) {
				overlayLists.grbOverlays = addMOCLayer(grbCoverage) as any[];
			}

			// Update coverage plot
			updateCoveragePlot();

		} catch (err) {
			console.error('Failed to update visualization:', err);
		}
	}

	function addSunMoonOverlays() {
		console.log('addSunMoonOverlays called with:', { aladin: !!aladin, sunMoonData });
		if (!aladin || !sunMoonData) {
			console.log('Cannot add sun/moon overlays - missing aladin or sunMoonData');
			return;
		}

		try {
			const A = (window as any).A;
			
			// Implement the exact same approach as Flask's aladin_setImage function
			function aladinSetImage(aladin: any, imgsource: any, imgname: any, pos_ra: any, pos_dec: any) {
				const IMG = new Image();
				IMG.src = imgsource;
				const cat = A.catalog({shape: IMG, name: imgname});
				aladin.addCatalog(cat);
				cat.addSources(A.source(pos_ra, pos_dec));
			}
			
			// Add sun and moon images using the exact Flask approach
			aladinSetImage(aladin, '/sun-logo-100.png', 'Sun at GW T0', sunMoonData.sun_ra, sunMoonData.sun_dec);
			aladinSetImage(aladin, '/moon-supersmall.png', 'Moon at GW T0', sunMoonData.moon_ra, sunMoonData.moon_dec);
			
			console.log('Added sun/moon image overlays using Flask approach:', {
				sun: { ra: sunMoonData.sun_ra, dec: sunMoonData.sun_dec, image: '/sun-logo-100.png' },
				moon: { ra: sunMoonData.moon_ra, dec: sunMoonData.moon_dec, image: '/moon-supersmall.png' }
			});
			
		} catch (err) {
			console.error('Failed to add sun/moon overlays:', err);
		}
	}

	function addContourLayer() {
		if (!aladin) return;
		
		// Use detection contours if available, otherwise fall back to contour data
		const contoursToRender = detectionContours || contourData;
		if (!contoursToRender) return;

		try {
			const A = (window as any).A;
			const contourList = Array.isArray(contoursToRender) ? contoursToRender : [contoursToRender];
			
			contourList.forEach((contourData: any, i: number) => {
				const overlay = A.graphicOverlay({
					id: `contour_${i}`,
					color: contourData.color || '#00ff00',
					lineWidth: 2,
					name: contourData.name || 'GW Localization'
				});
				
				aladin.addOverlay(overlay);
				
				// Add contour polygons
				if (contourData.contours && Array.isArray(contourData.contours)) {
					contourData.contours.forEach((contour: any) => {
						if (contour.polygon) {
							overlay.addFootprints([A.polygon(contour.polygon)]);
						}
					});
				}
				
				(overlayLists.detectionOverlays as any[]).push({
					contour: overlay,
					toshow: true,
					tocolor: contourData.color || '#00ff00'
				});
			});
			
		} catch (err) {
			console.error('Failed to add contour layer:', err);
		}
	}

	function addFootprintLayer() {
		if (!footprintData) return;
		
		// Use time-filtered version by default
		addFootprintLayerWithTimeFilter();
	}

	function addGalaxyLayer() {
		if (!galaxyData || galaxyData.length === 0) return;
		
		try {
			const markers = addMarkersToAladin(galaxyData, 'Galaxies', '#FF6B35');
			overlayLists.galaxyMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add galaxy layer:', err);
		}
	}

	function addCandidateLayer() {
		if (!candidateData || candidateData.length === 0) return;
		
		try {
			const markers = addMarkersToAladin(candidateData, 'Candidates', '#8E44AD');
			overlayLists.candidateMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add candidate layer:', err);
		}
	}

	function addIceCubeLayer() {
		if (!icecubeData || icecubeData.length === 0) return;
		
		try {
			const markers = addMarkersToAladin(icecubeData, 'IceCube Events', '#0080FF');
			overlayLists.icecubeMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add IceCube layer:', err);
		}
	}

	// Generic function to add markers to Aladin (matching Flask pattern)
	function addMarkersToAladin(markerData: any[], catalogName: string, color: string) {
		if (!aladin || !markerData.length) return [];
		
		try {
			const A = (window as any).A;
			const markerLayers: any[] = [];
			
			markerData.forEach((group: any, i: number) => {
				const groupName = group.name || `${catalogName} ${i + 1}`;
				const markers = group.markers || [];
				
				const markerlayer = A.catalog({
					name: groupName,
					color: color,
					sourceSize: 8
				});
				
				const overlay = A.graphicOverlay();
				let hasOverlay = false;
				
				// Check if markers have radius (circles)
				if (markers.length > 0 && markers[0].radius) {
					aladin.addOverlay(overlay);
					hasOverlay = true;
				}
				
				markers.forEach((marker: any) => {
					const aladinMarker = A.marker(marker.ra, marker.dec, {
						popupTitle: marker.name,
						popupDesc: marker.info || ''
					});
					markerlayer.addSources([aladinMarker]);
					
					if (hasOverlay && marker.radius) {
						overlay.add(A.circle(marker.ra, marker.dec, marker.radius, { color: color }));
					}
				});
				
				aladin.addCatalog(markerlayer);
				
				markerLayers.push({
					name: groupName,
					toshow: true,
					tocolor: color,
					markerlayer: markerlayer,
					overlaylayer: overlay,
					has_overlay: hasOverlay
				});
			});
			
			return markerLayers;
		} catch (err) {
			console.error('Failed to add markers to Aladin:', err);
			return [];
		}
	}

	// Interactive marker animation (matching Flask)
	function animateToMarker(targetName: string, markerData: any[]) {
		if (!aladin || !markerData.length) return;
		
		try {
			for (const group of markerData) {
				const markers = group.markers || [];
				for (const marker of markers) {
					if (marker.name === targetName) {
						// Zoom and animate to marker position (matching Flask behavior)
						aladin.zoomToFoV(3, 3); // 3 degree field of view
						aladin.animateToRaDec(marker.ra, marker.dec, 3);
						return;
					}
				}
			}
		} catch (err) {
			console.error('Failed to animate to marker:', err);
		}
	}

	// Toggle marker visibility
	function toggleMarkerGroup(markerList: any[], groupName: string, show: boolean) {
		if (!markerList.length) return;
		
		try {
			const groupIdStr = groupName.replace(/\s+/g, '');
			for (const markerGroup of markerList) {
				const nameIdStr = (markerGroup as any).name.replace(/\s+/g, '');
				if (groupIdStr === nameIdStr) {
					if (show) {
						(markerGroup as any).markerlayer?.show();
						if ((markerGroup as any).has_overlay) {
							(markerGroup as any).overlaylayer?.show();
						}
					} else {
						(markerGroup as any).markerlayer?.hide();
						if ((markerGroup as any).has_overlay) {
							(markerGroup as any).overlaylayer?.hide();
						}
					}
					(markerGroup as any).toshow = show;
					break;
				}
			}
		} catch (err) {
			console.error('Failed to toggle marker group:', err);
		}
	}

	// Generate HTML for marker lists with collapsible groups (matching Flask)
	function generateMarkerHtml(markerData: any[], containerId: string) {
		if (!markerData.length) return;
		
		let html = '<ul style="list-style-type:none;">';
		
		for (const group of markerData) {
			const groupName = (group as any).name;
			const idStr = groupName.replace(/\s+/g, '');
			const color = (group as any).color || '#FF6B35';
			
			html += `
				<li>
					<fieldset>
						<button 
							id="collbtn${idStr}" 
							type="button" 
							class="text-blue-600 hover:text-blue-800 text-sm mr-2"
							onclick="toggleCollapse('${idStr}')"
						>
							▶
						</button>
						<label>
							<input 
								id="marker_group_${idStr}" 
								type="checkbox" 
								checked="checked"
								class="mr-2"
								onchange="handleMarkerToggle('${groupName}', this.checked)"
							/>
							<div 
								class="inline-block w-3 h-3 rounded-full mr-2"
								style="background-color: ${color};"
							></div>
							<span class="text-sm">${groupName}</span>
						</label>
					</fieldset>
					<div class="ml-4 hidden" id="collapse${idStr}">
						<ul style="list-style-type:none;">`;
			
			const markers = (group as any).markers || [];
			for (const marker of markers) {
				html += `
					<li>
						<fieldset>
							<label>
								<div 
									id="${(marker as any).name}" 
									class="text-xs text-blue-600 hover:text-blue-800 cursor-pointer py-1"
									onclick="handleMarkerClick('${(marker as any).name}')"
								>
									${(marker as any).name}
								</div>
							</label>
						</fieldset>
					</li>`;
			}
			
			html += `
						</ul>
					</div>
				</li>`;
		}
		
		html += '</ul>';
		
		// Update the container (this would need to be handled differently in Svelte)
		// For now, just log the HTML that would be generated
		console.log(`Generated marker HTML for ${containerId}:`, html);
	}

	// Dynamic data loading functions (matching Flask AJAX pattern)
	async function loadGalaxies() {
		if (!selectedAlert?.id) return;
		
		try {
			galaxyData = await gwtmApi.getEventGalaxiesAjax(selectedAlert.id.toString());
			if (showGalaxies) {
				addGalaxyLayer();
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
				addCandidateLayer();
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
				addIceCubeLayer();
			}
		} catch (err) {
			console.warn('Failed to load IceCube data:', err);
			icecubeData = [];
		}
	}

	function updateCoveragePlot() {
		if (!plotlyContainer || !coverageData || typeof window === 'undefined') return;

		try {
			const Plotly = (window as any).Plotly;
			
			const data = [{
				x: (coverageData as any).time || [],
				y: (coverageData as any).probability || [],
				type: 'scatter',
				mode: 'lines+markers',
				name: 'Probability Coverage',
				line: { color: 'blue' }
			}];

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

	// Alert type loading and switching
	async function loadAlertTypes() {
		if (!graceid || isLoadingAlertTypes) return;
		
		isLoadingAlertTypes = true;
		try {
			// Query alerts for this specific graceid only (matching Flask behavior)
			const response = await gwtmApi.queryAlerts({ graceid: graceid });
			if (response.alerts && response.alerts.length > 0) {
				// Try exact matching first (this should be sufficient for most cases)
				let exactGraceidAlerts = response.alerts.filter((alert: any) => 
					alert.graceid === graceid || alert.alternateid === graceid
				);
				
				// If no exact match, try case-insensitive matching only
				if (exactGraceidAlerts.length === 0) {
					exactGraceidAlerts = response.alerts.filter((alert: any) => 
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
				const validAlerts = exactGraceidAlerts.filter((alert: any) => alert.alert_type !== 'Retraction');
				
				// Sort by datecreated ASC to match Flask processing order
				validAlerts.sort((a, b) => new Date(a.datecreated || a.timesent).getTime() - new Date(b.datecreated || b.timesent).getTime());
				
				// Process alerts with numbering for duplicates (exactly matching Flask logic)
				const alertTypeTabs: any[] = [];
				
				validAlerts.forEach((alert: any) => {
					const existingTypes = alertTypeTabs.map(tab => tab.type);
					const baseType = alert.alert_type;
					
					// Check if this alert type already exists
					const existingOfSameType = existingTypes.filter(type => {
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
				availableAlertTypes = alertTypeTabs.sort((a, b) => new Date(b.timesent).getTime() - new Date(a.timesent).getTime());
				
				
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
	
	// Convert JavaScript Date to Modified Julian Date (matching Flask's astropy calculation)
	function convertToMJD(date: Date): number {
		// MJD = JD - 2400000.5
		// JD = (Unix timestamp / 86400) + 2440587.5
		const unixTimestamp = date.getTime() / 1000; // Convert to seconds
		const julianDate = (unixTimestamp / 86400) + 2440587.5;
		const mjd = julianDate - 2400000.5;
		return Math.round(mjd * 1000) / 1000; // Round to 3 decimal places like Flask
	}
	
	async function switchAlertType(alertType: string) {
		if (!alertType || !availableAlertTypes.length || isSwitchingAlert) return;
		
		const newAlertTab = availableAlertTypes.find(a => a.alert_type === alertType);
		if (newAlertTab && newAlertTab.original_alert.id !== selectedAlert?.id) {
			isSwitchingAlert = true;
			
			selectedAlert = newAlertTab.original_alert;
			selectedAlertType = alertType;
			
			// Clear existing data overlays only (preserve base sky survey to prevent flickering)
			if (aladin) {
				try {
					clearDataOverlays();
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

	// Reactive updates
	$: if (showContours || showFootprints || showGalaxies || showCandidates || showIceCube || showGrbCoverage) {
		updateVisualization();
	}

	// Load alert types only once when component mounts (not reactively)
	// Reactive loading was causing tabs to flicker during alert switching

	// Initialization is now handled by onMount to avoid container timing issues
	// $: if (graceid && selectedAlert) {
	//	initializeVisualization();
	// }

	// Alert switching is handled directly by click handlers to avoid flickering
	// Removed reactive statement to prevent redundant switchAlertType() calls

	// Dynamic data loading triggers
	$: if (showGalaxies && galaxyData.length === 0) {
		loadGalaxies();
	}

	$: if (showCandidates && candidateData.length === 0) {
		loadCandidates();
	}

	$: if (showIceCube && icecubeData.length === 0) {
		loadIceCubeData();
	}

	// Time range filtering is now handled by the slider drag events directly

	// Reload data when pointing status changes
	$: if (pointingStatus && graceid && selectedAlert && !isSwitchingAlert) {
		reloadFootprintData();
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

	// Removed duplicate - using the comprehensive animateToMarker function above

	// Clear only data overlays (preserve base sky survey to prevent flickering)
	function clearDataOverlays() {
		if (!aladin) return;
		
		try {
			// Clear tracked overlay lists
			Object.keys(overlayLists).forEach(key => {
				const overlays = (overlayLists as any)[key as keyof typeof overlayLists];
				if (Array.isArray(overlays)) {
					overlays.forEach((overlay: any) => {
						try {
							if (overlay.markerlayer) overlay.markerlayer.removeAll();
							if (overlay.overlaylayer && overlay.overlaylayer.removeAll) overlay.overlaylayer.removeAll();
							if (overlay.contour && overlay.contour.removeAll) overlay.contour.removeAll();
							if (overlay.remove) overlay.remove();
						} catch (e) {
							console.warn('Error removing overlay:', e);
						}
					});
					// Clear the array
					((overlayLists as any)[key as keyof typeof overlayLists] as any[]).length = 0;
				}
			});
		} catch (err) {
			console.warn('Error in clearDataOverlays:', err);
		}
	}

	// Toggle marker visibility (matching Flask pattern)
	function toggleMarkerVisibility(markerList: any[], show: boolean) {
		if (!markerList) return;
		
		try {
			markerList.forEach((markerLayer: any) => {
				if (markerLayer.markerlayer) {
					show ? markerLayer.markerlayer.show() : markerLayer.markerlayer.hide();
				}
				if (markerLayer.overlaylayer && markerLayer.has_overlay) {
					show ? markerLayer.overlaylayer.show() : markerLayer.overlaylayer.hide();
				}
			});
			
			if (aladin) {
				aladin.view.requestRedraw();
			}
		} catch (err) {
			console.error('Failed to toggle marker visibility:', err);
		}
	}

	// MOC support for GRB coverage (matching Flask implementation)
	function addMOCLayer(mocData: any[]) {
		if (!aladin || !mocData || mocData.length === 0) return [];
		
		try {
			const A = (window as any).A;
			const mocOverlays: any[] = [];
			
			mocData.forEach((mocItem: any, i: number) => {
				if (mocItem.json) {
					const moc = A.MOCFromJSON(mocItem.json, {
						opacity: 0.25,
						color: mocItem.color || '#FF6B35',
						lineWidth: 1,
						name: mocItem.name || `MOC ${i + 1}`
					});
					
					aladin.addMOC(moc);
					moc.hide(); // Start hidden like in Flask
					
					mocOverlays.push(moc);
				}
			});
			
			return mocOverlays;
		} catch (err) {
			console.error('Failed to add MOC layer:', err);
			return [];
		}
	}

	// Toggle MOC visibility (matching Flask implementation)
	function toggleMOC(mocOverlays: any[], show: boolean) {
		if (!mocOverlays) return;
		
		try {
			mocOverlays.forEach((moc: any) => {
				show ? moc.show() : moc.hide();
			});
			
			if (aladin) {
				aladin.view.requestRedraw();
			}
		} catch (err) {
			console.error('Failed to toggle MOC visibility:', err);
		}
	}

	// Coverage calculator function (matching Flask implementation)
	async function calculateCoverage() {
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

	// Skymap renormalization functions (matching Flask implementation)
	async function visualizeRenormalizedSkymap() {
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
					resultDiv.innerHTML = '<span class="text-green-600 font-medium">The Skymap has been Renormalized (~ look up! ~)</span>';
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

	async function downloadRenormalizedSkymap() {
		if (!graceid || !selectedAlert) return;
		
		try {
			loading = true;
			
			// Update progress
			const resultDiv = document.getElementById('renorm-result');
			if (resultDiv) {
				resultDiv.innerHTML = '<span class="text-blue-600">Generating fits file...</span><div class="w-full bg-gray-200 rounded-full h-2 mt-2"><div class="bg-blue-600 h-2 rounded-full" style="width: 45%"></div></div>';
			}
			
			// Call API with download flag
			const response = await fetch(`/ajax_renormalize_skymap?graceid=${graceid}&alert_id=${selectedAlert.id}&approx_cov=1&download=true&_ts=${Date.now()}`);
			
			if (response.ok) {
				const blob = await response.blob();
				
				if (blob.size > 0) {
					// Extract filename from headers
					const contentDisposition = response.headers.get('Content-Disposition');
					let filename = 'normed_skymap.fits';
					
					if (contentDisposition && contentDisposition.includes('filename=')) {
						filename = contentDisposition
							.split('filename=')[1]
							.split(';')[0]
							.replace(/"/g, '');
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
						resultDiv.innerHTML = '<span class="text-green-600 font-medium">Download complete!</span>';
					}
				} else {
					if (resultDiv) {
						resultDiv.innerHTML = '<span class="text-red-600">No completed pointings selected.</span>';
					}
				}
			} else {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			
		} catch (err) {
			console.error('Failed to download renormalized skymap:', err);
			const resultDiv = document.getElementById('renorm-result');
			if (resultDiv) {
				resultDiv.innerHTML = '<span class="text-red-600">Error Downloading Renormalized Skymap</span>';
			}
		} finally {
			loading = false;
		}
	}

	// Filter footprints by time range (matching Flask time slider)
	function filterFootprintsByTime() {
		if (!aladin || !footprintData) return;
		
		try {
			// Clear existing instrument overlays first
			(overlayLists.instOverlays as any[]).forEach((overlay: any) => {
				if (overlay.contour) {
					try {
						aladin.removeOverlay(overlay.contour);
					} catch (e) {
						// Ignore removal errors
					}
				}
			});
			overlayLists.instOverlays = [];
			
			// Re-add sun/moon markers (they should always be visible)
			if (sunMoonData) {
				addSunMoonOverlays();
			}
			
			// Recreate footprints with time filtering
			addFootprintLayerWithTimeFilter();
			
			// Re-add contours if they should be shown
			if (showContours && (contourData || detectionContours)) {
				addContourLayer();
			}
			
			aladin.view.requestRedraw();
		} catch (err) {
			console.error('Failed to filter footprints by time:', err);
		}
	}

	function addFootprintLayerWithTimeFilter() {
		if (!footprintData || !Array.isArray(footprintData)) return;
		
		try {
			const A = (window as any).A;
			const newOverlays: any[] = [];
			
			footprintData.forEach((instData: any, i: number) => {
				const overlay = A.graphicOverlay({
					id: i,
					color: instData.color || '#ff0000',
					lineWidth: 2,
					name: instData.name || `Instrument ${i + 1}`
				});
				
				aladin.addOverlay(overlay);
				
				let hasVisibleContours = false;
				
				// Filter contours by time
				if (instData.contours && Array.isArray(instData.contours)) {
					instData.contours.forEach((contour: any) => {
						// Check if contour time is within range
						if (typeof contour.time === 'number' && 
							contour.time >= timeRange[0] && 
							contour.time <= timeRange[1]) {
							if (contour.polygon && Array.isArray(contour.polygon)) {
								overlay.addFootprints([A.polygon(contour.polygon)]);
								hasVisibleContours = true;
							}
						}
					});
				}
				
				// Only add to overlay list if there are visible contours
				if (hasVisibleContours || !instData.contours) {
					newOverlays.push({
						contour: overlay,
						toshow: true,
						tocolor: instData.color || '#ff0000',
						name: instData.name || `Instrument ${i + 1}`
					});
				} else {
					// Remove overlay if no visible contours
					try {
						aladin.removeOverlay(overlay);
					} catch (e) {
						// Ignore removal errors
					}
				}
			});
			
			overlayLists.instOverlays = newOverlays as any[];
			console.log(`Filtered footprints: ${newOverlays.length} instruments visible in time range [${timeRange[0].toFixed(1)}, ${timeRange[1].toFixed(1)}]`);
			
		} catch (err) {
			console.error('Failed to add time-filtered footprints:', err);
		}
	}

	// Calculate time range from footprint data (matching Flask implementation)
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
	
	// Interactive control functions (matching Flask implementation)
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
		if (!(overlayLists.instOverlays as any[])) return;
		
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
	
	function updateHideShowButton() {
		try {
			const checkboxes = document.querySelectorAll('.instruments-list input[type="checkbox"]');
			const checkedBoxes = document.querySelectorAll('.instruments-list input[type="checkbox"]:checked');
			
			// Update global show state based on checkbox states
			if (checkboxes.length === checkedBoxes.length) {
				showFootprints = true;
			} else if (checkedBoxes.length === 0) {
				showFootprints = false;
			}
		} catch (err) {
			console.error('Failed to update hide/show button:', err);
		}
	}

	// Time slider drag handling
	let isDragging = false;
	let dragHandle: 'min' | 'max' | null = null;

	function startDrag(e: MouseEvent | TouchEvent, handle: 'min' | 'max') {
		e.preventDefault();
		isDragging = true;
		dragHandle = handle;
		
		// Add global event listeners
		if (typeof window !== 'undefined') {
			document.addEventListener('mousemove', handleDrag);
			document.addEventListener('mouseup', stopDrag);
			document.addEventListener('touchmove', handleDrag, { passive: false });
			document.addEventListener('touchend', stopDrag);
		}
	}

	function handleDrag(e: MouseEvent | TouchEvent) {
		if (!isDragging || !dragHandle) return;
		
		e.preventDefault();
		
		// Get the slider wrapper element
		const sliderWrapper = document.querySelector('.time-slider-wrapper');
		if (!sliderWrapper) return;
		
		const rect = sliderWrapper.getBoundingClientRect();
		const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
		const percent = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
		const newValue = minTime + (percent / 100) * (maxTime - minTime);
		
		if (dragHandle === 'min') {
			timeRange[0] = Math.min(newValue, timeRange[1]);
		} else {
			timeRange[1] = Math.max(newValue, timeRange[0]);
		}
		
		// Trigger reactivity
		timeRange = [...timeRange];
		
		// Filter footprints in real-time (like Flask)
		filterFootprintsByTime();
	}

	function stopDrag() {
		isDragging = false;
		dragHandle = null;
		
		// Remove global event listeners
		if (typeof window !== 'undefined') {
			document.removeEventListener('mousemove', handleDrag);
			document.removeEventListener('mouseup', stopDrag);
			document.removeEventListener('touchmove', handleDrag);
			document.removeEventListener('touchend', stopDrag);
		}
	}
</script>

<!-- Alert Type Tabs (matching Flask) - positioned at top above visualization -->
{#if !error && availableAlertTypes.length > 0}
	<div class="mb-4">
		<ul class="nav nav-tabs flex flex-wrap border-b border-gray-200">
			{#each availableAlertTypes as alertTypeOption}
				<li class="nav-item mr-2">
					<button
						class="px-3 py-2 text-sm font-medium border-b-2 transition-all cursor-pointer
							{selectedAlertType === alertTypeOption.alert_type 
								? 'text-blue-600 border-blue-600 bg-blue-50' 
								: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
						on:click={() => switchAlertType(alertTypeOption.alert_type)}
					>
						<div class="text-center leading-tight">
							<div class="font-medium">{alertTypeOption.alert_type}</div>
							{#if alertTypeOption.timesent}
								<div class="text-xs opacity-75">
									{new Date(alertTypeOption.timesent).toLocaleString()}
								</div>
							{/if}
						</div>
					</button>
				</li>
			{/each}
		</ul>
	</div>
{/if}

<!-- Two column layout matching Flask implementation -->
<div class="flex w-full gap-4">
	<!-- Left column: Aladin visualization (70% width) -->
	<div style="width: 70%;">
		<div class="bg-white border rounded-lg overflow-hidden">
			<div 
				bind:this={aladinContainer}
				class="w-full aladin-container"
				style="height: 640px; position: relative; border: 2px solid #ccc; background: #000;"
				id="aladin-lite-div"
			></div>
		</div>
	</div>

	<!-- Right column: Follow-up controls (30% width) matching Flask exactly -->
	<div class="column" style="float: right; width: 30%; padding-left: 2%;">
		<div class="row">
			<h3>Follow-Up</h3>
		</div>

		
		<!-- Instrument block buttons and div (matching Flask exactly) -->
		<div class="btn-group">
			<button 
				class="btn btn-primary btn-sm alert_coll my-1 {showFootprints ? 'down-triangle' : ''}"
				on:click={() => showFootprints = !showFootprints}
				style="margin-right: 5px;"
			></button>
			<button 
				class="btn btn-primary btn-sm my-1"
				on:click={() => {
					(overlayLists.instOverlays as any[]).forEach(overlay => {
						if (overlay.contour) {
							showFootprints ? overlay.contour.hide() : overlay.contour.show();
						}
					});
					showFootprints = !showFootprints;
				}}
				style="margin-right: 5px;"
			>
				{showFootprints ? 'Hide' : 'Show'}
			</button>
			<h4 style="display: inline-block;" class={(!footprintData || footprintData.length === 0) ? 'loadingtext' : ''}>
				{(!footprintData || footprintData.length === 0) ? '...Loading...' : 'Instruments'}
			</h4>
		</div>
		<div class="row">
			<div class="collapse {showFootprints ? 'in' : ''} scroll-section inst_coll">
				{#if footprintData && Array.isArray(footprintData)}
					{#each footprintData as inst, i}
						<label style="display: block; padding: 2px 0;">
							<input 
								type="checkbox" 
								checked={true}
								style="margin-right: 5px;"
								data-color={inst.color || '#ff0000'}
								on:change={(e) => {
									toggleInstrumentOverlay(e.target, overlayLists.instOverlays as any[]);
									updateHideShowButton();
								}}
							/>
							<span 
								style="display: inline-block; width: 12px; height: 12px; margin-right: 5px; border: 1px solid #ccc; background-color: {inst.color || '#ff0000'};"
							></span>
							{inst.name || `Inst ${i + 1}`}
						</label>
					{/each}
				{/if}
			</div>
		</div>
		
		<!-- GRB coverage block buttons and div -->
		<div class="btn-group">
			<button 
				class="btn btn-primary btn-sm alert_coll my-1 {showGrbCoverage ? 'down-triangle' : ''}"
				on:click={() => showGrbCoverage = !showGrbCoverage}
				style="margin-right: 5px;"
			></button>
			<button 
				class="btn btn-primary btn-sm my-1"
				on:click={() => showGrbCoverage = !showGrbCoverage}
				style="margin-right: 5px;"
			>
				{showGrbCoverage ? 'Hide' : 'Show'}
			</button>
			<h4 style="display: inline-block;">GRB Coverage</h4>
		</div>
		<div class="row">
			<div class="collapse {showGrbCoverage ? 'in' : ''} grb_coll"></div>
		</div>
		
		<div class="row">
			<h3>Sources</h3>
		</div>
		
		<!-- Galaxies block buttons and div -->
		<div class="btn-group">
			<button 
				class="btn btn-primary btn-sm alert_coll my-1 {showGalaxies ? 'down-triangle' : ''}"
				on:click={() => showGalaxies = !showGalaxies}
				style="margin-right: 5px;"
			></button>
			<button 
				class="btn btn-primary btn-sm my-1"
				on:click={() => {
					if (!showGalaxies && galaxyData.length === 0) {
						loadGalaxies();
					} else if (galaxyData.length > 0) {
						(overlayLists.galaxyMarkers as any[]).forEach(markerGroup => {
							toggleMarkerGroup([markerGroup], markerGroup.name, !showGalaxies);
						});
					}
					showGalaxies = !showGalaxies;
				}}
				style="margin-right: 5px;"
			>
				{galaxyData.length > 0 ? (showGalaxies ? 'Hide' : 'Show') : 'Get'}
			</button>
			<h4 style="display: inline-block;">Galaxies</h4>
		</div>
		<div class="row">
			<div class="collapse {showGalaxies ? 'in' : ''} gal_coll">
				{#if galaxyData.length > 0}
					{#each galaxyData as group}
						<div style="margin-bottom: 5px;">
							<div style="font-weight: bold; font-size: 13px;">{(group as any).name}</div>
							{#if (group as any).markers}
								{#each (group as any).markers as marker}
									<button 
										style="display: block; width: 100%; text-align: left; padding: 2px 5px; border: none; background: none; font-size: 12px; cursor: pointer;"
										on:click={() => animateToMarker((marker as any).name, galaxyData)}
										on:mouseover={(e) => (e.target as any).style.backgroundColor = '#f0f0f0'}
										on:mouseout={(e) => (e.target as any).style.backgroundColor = 'transparent'}
									>
										{(marker as any).name}
									</button>
								{/each}
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</div>
		
		<!-- IceCube Notice block buttons and div -->
		{#if hasIceCubeData}
		<div class="btn-group">
			<button 
				class="btn btn-primary btn-sm alert_coll my-1 {showIceCube ? 'down-triangle' : ''}"
				on:click={() => showIceCube = !showIceCube}
				style="margin-right: 5px;"
			></button>
			<button 
				class="btn btn-primary btn-sm my-1"
				on:click={() => {
					if (!showIceCube && icecubeData.length === 0) {
						loadIceCubeData();
					}
					showIceCube = !showIceCube;
				}}
				style="margin-right: 5px;"
			>
				{icecubeData.length > 0 ? (showIceCube ? 'Hide' : 'Show') : 'Get'}
			</button>
			<h4 style="display: inline-block;">ICECUBE Notice</h4>
		</div>
		<div class="row">
			<div class="collapse {showIceCube ? 'in' : ''} icecube_coll">
				{#if icecubeData.length > 0}
					{#each icecubeData as group}
						<div style="margin-bottom: 5px;">
							<div style="font-weight: bold; font-size: 13px;">{(group as any).name}</div>
							{#if (group as any).markers}
								{#each (group as any).markers as marker}
									<button 
										style="display: block; width: 100%; text-align: left; padding: 2px 5px; border: none; background: none; font-size: 12px; cursor: pointer;"
										on:click={() => animateToMarker((marker as any).name, icecubeData)}
										on:mouseover={(e) => (e.target as any).style.backgroundColor = '#f0f0f0'}
										on:mouseout={(e) => (e.target as any).style.backgroundColor = 'transparent'}
									>
										{(marker as any).name}
									</button>
								{/each}
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</div>
		{/if}
		
		<!-- Candidates block buttons and div -->
		{#if hasCandidateData}
		<div class="btn-group">
			<button 
				class="btn btn-primary btn-sm alert_coll my-1 {showCandidates ? 'down-triangle' : ''}"
				on:click={() => showCandidates = !showCandidates}
				style="margin-right: 5px;"
			></button>
			<button 
				class="btn btn-primary btn-sm my-1"
				on:click={() => {
					if (!showCandidates && candidateData.length === 0) {
						loadCandidates();
					}
					showCandidates = !showCandidates;
				}}
				style="margin-right: 5px;"
			>
				{candidateData.length > 0 ? (showCandidates ? 'Hide' : 'Show') : 'Get'}
			</button>
			<h4 style="display: inline-block;">Candidates</h4>
		</div>
		<div class="row">
			<div class="collapse {showCandidates ? 'in' : ''} candidate_coll">
				{#if candidateData.length > 0}
					{#each candidateData as group}
						<div style="margin-bottom: 5px;">
							<div style="font-weight: bold; font-size: 13px;">{(group as any).name}</div>
							{#if (group as any).markers}
								{#each (group as any).markers as marker}
									<button 
										style="display: block; width: 100%; text-align: left; padding: 2px 5px; border: none; background: none; font-size: 12px; cursor: pointer;"
										on:click={() => animateToMarker((marker as any).name, candidateData)}
										on:mouseover={(e) => (e.target as any).style.backgroundColor = '#f0f0f0'}
										on:mouseout={(e) => (e.target as any).style.backgroundColor = 'transparent'}
									>
										{(marker as any).name}
									</button>
								{/each}
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</div>
		{/if}
	</div>
</div>


<div class="space-y-6">
	{#if !loading && !error}

		<!-- Time Controls Section -->
		<div class="bg-white border rounded-lg p-4">
			<h3 class="text-lg font-semibold mb-3">Time Controls</h3>
			<div class="mb-4">
				<label class="block text-sm font-medium text-gray-700 mb-2">
					Pointing Status:
				</label>
				<select 
					bind:value={pointingStatus}
					class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="completed">Completed</option>
					<option value="planned">Planned</option>
					<option value="all">All</option>
				</select>
			</div>

			<div class="mb-4">
				<label class="block text-sm font-medium text-gray-700 mb-2">
					Date range (days since Time of Signal): {timeRange[0].toFixed(1)} - {timeRange[1].toFixed(1)}
				</label>

				<!-- Time Range Slider -->
				<div class="time-slider-container mt-4">
					<div class="time-slider-wrapper">
						<div class="time-slider-track"></div>
						<div 
							class="time-slider-range" 
							style="left: {((timeRange[0] - minTime) / (maxTime - minTime)) * 100}%; 
								   width: {((timeRange[1] - timeRange[0]) / (maxTime - minTime)) * 100}%"
						></div>
						
						<!-- Min handle -->
						<div 
							class="time-slider-handle min-handle"
							class:dragging={isDragging && dragHandle === 'min'}
							style="left: {((timeRange[0] - minTime) / (maxTime - minTime)) * 100}%"
							on:mousedown={(e) => startDrag(e, 'min')}
							on:touchstart={(e) => startDrag(e, 'min')}
							title="Minimum time: {timeRange[0].toFixed(1)} days"
						></div>
						
						<!-- Max handle -->
						<div 
							class="time-slider-handle max-handle"
							class:dragging={isDragging && dragHandle === 'max'}
							style="left: {((timeRange[1] - minTime) / (maxTime - minTime)) * 100}%"
							on:mousedown={(e) => startDrag(e, 'max')}
							on:touchstart={(e) => startDrag(e, 'max')}
							title="Maximum time: {timeRange[1].toFixed(1)} days"
						></div>
					</div>
					
					<!-- Time labels -->
					<div class="time-labels mt-2">
						<span class="text-xs text-gray-500">{minTime.toFixed(1)} days</span>
						<span class="text-xs text-gray-500 float-right">{maxTime.toFixed(1)} days</span>
					</div>
				</div>
			</div>
		</div>


		<!-- Event Explorer Tabs (exactly matching Flask) -->
		<div class="bg-white border rounded-lg overflow-hidden mt-4">
			<!-- Tab Navigation (matching Flask Bootstrap nav-tabs) -->
			<ul class="nav nav-tabs flex border-b border-gray-200 bg-gray-50">
				<li class="nav-item px-4 py-3">
					<span class="nav-link disabled text-sm font-medium text-gray-500" style="font-weight: bold;">Event Explorer:</span>
				</li>
				<li class="nav-item cursor-pointer">
					<button
						class="nav-link px-4 py-3 text-sm font-medium border-b-2 transition-colors
							{currentTab === 'info' 
								? 'text-blue-600 border-blue-600 bg-white' 
								: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
						on:click={() => currentTab = 'info'}
					>
						Summary
					</button>
				</li>
				<li class="nav-item cursor-pointer">
					<button
						class="nav-link px-4 py-3 text-sm font-medium border-b-2 transition-colors
							{currentTab === 'coverage' 
								? 'text-blue-600 border-blue-600 bg-white' 
								: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
						on:click={() => currentTab = 'coverage'}
					>
						Coverage Calculator
					</button>
				</li>
				<li class="nav-item cursor-pointer">
					<button
						class="nav-link px-4 py-3 text-sm font-medium border-b-2 transition-colors
							{currentTab === 'renorm' 
								? 'text-blue-600 border-blue-600 bg-white' 
								: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
						on:click={() => currentTab = 'renorm'}
					>
						Renormalize Skymap
					</button>
				</li>
			</ul>

			<!-- Tab Content -->
			<div class="tab-content p-6">
				{#if currentTab === 'info'}
					<!-- Summary Tab (matching Flask exactly) -->
					<div class="tab-pane active" id="calc-info-content">
						<div class="container-fluid">
							<div class="row flex flex-wrap">
								<!-- Left Column: Alert Information -->
								<div class="col-sm-6 w-1/2 pr-4">
									<table class="table w-full border-collapse">
										<thead>
											<tr class="border-b">
												<th class="text-left py-2 font-semibold">Information</th>
												<th class="text-left py-2"></th>
											</tr>
										</thead>
										<tbody>
											{#if selectedAlert?.group && selectedAlert.group !== 'None' && selectedAlert.group !== ''}
												<tr class="alert-info border-b">
													<td class="py-2">Group</td>
													<td class="py-2" id="alert_group">{selectedAlert.group}</td>
												</tr>
											{/if}
											<tr class="alert-info border-b">
												<td class="py-2">Detectors</td>
												<td class="py-2" id="alert_detectors">{selectedAlert?.detectors || 'N/A'}</td>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">Time of Signal</td>
												<td class="py-2" id="alert_time_of_signal">
													{selectedAlert?.time_of_signal ? new Date(selectedAlert.time_of_signal).toISOString().replace('T', ' ').replace('Z', ' UTC') : 'N/A'}
												</td>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">Time Sent</td>
												<td class="py-2" id="alert_timesent">
													{selectedAlert?.timesent ? new Date(selectedAlert.timesent).toISOString().replace('T', ' ').replace('Z', ' UTC') : 'N/A'}
												</td>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">False Alarm Rate</td>
												<td class="py-2" id="alert_human_far">
													{#if selectedAlert?.human_far}
														once per {selectedAlert.human_far} {selectedAlert.human_far_unit || 'years'}
													{:else}
														N/A
													{/if}
												</td>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">50% Area</td>
												<td class="py-2" id="alert_area_50">{selectedAlert?.area_50 || 'N/A'} deg<sup>2</sup></td>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">90% Area</td>
												<td class="py-2" id="alert_area_90">{selectedAlert?.area_90 || 'N/A'} deg<sup>2</sup></td>
											</tr>
											{#if selectedAlert?.group !== 'Burst'}
												<tr class="alert-info border-b">
													<td class="py-2">Distance</td>
													<td class="py-2" id="alert_distance_plus_error">
														{#if selectedAlert?.distance && selectedAlert?.distance_error}
															{selectedAlert.distance} +/- {selectedAlert.distance_error} Mpc
														{:else}
															N/A
														{/if}
													</td>
												</tr>
											{:else}
												<tr class="alert-info border-b">
													<td class="py-2">Central Frequency</td>
													<td class="py-2" id="alert_centralfreq">{selectedAlert?.centralfreq || 'N/A'} Hz</td>
												</tr>
												<tr class="alert-info border-b">
													<td class="py-2">Duration</td>
													<td class="py-2" id="alert_duration">{selectedAlert?.duration || 'N/A'} seconds</td>
												</tr>
											{/if}
										</tbody>
									</table>
								</div>

								<!-- Right Column: Classification (CBC Only) -->
								{#if selectedAlert?.group !== 'Burst'}
									<div class="col-sm-6 w-1/2 pl-4">
										<table class="table w-full border-collapse">
											<thead>
												<tr class="border-b">
													<th class="text-left py-2 font-semibold">Classification (CBC Only)</th>
													<th class="text-left py-2"></th>
												</tr>
											</thead>
											<tbody>
												<tr class="alert-info border-b">
													<td class="py-2">BNS</td>
													<td class="py-2" id="alert_prob_bns">{selectedAlert?.prob_bns || 'N/A'}</td>
												</tr>
												<tr class="alert-info border-b">
													<td class="py-2">NSBH</td>
													<td class="py-2" id="alert_prob_nsbh">{selectedAlert?.prob_nsbh || 'N/A'}</td>
												</tr>
												<tr class="alert-info border-b">
													<td class="py-2">Mass Gap</td>
													<td class="py-2" id="alert_prob_gap">{selectedAlert?.prob_gap || 'N/A'}</td>
												</tr>
												<tr class="alert-info border-b">
													<td class="py-2">BBH</td>
													<td class="py-2" id="alert_prob_bbh">{selectedAlert?.prob_bbh || 'N/A'}</td>
												</tr>
												<tr class="alert-info border-b">
													<td class="py-2">Terrestrial</td>
													<td class="py-2" id="alert_prob_terrestrial">{selectedAlert?.prob_terrestrial || 'N/A'}</td>
												</tr>
												<tr class="alert-info border-b">
													<td class="py-2">Has NS</td>
													<td class="py-2" id="alert_prob_hasns">{selectedAlert?.prob_hasns || 'N/A'}</td>
												</tr>
												<tr class="alert-info border-b">
													<td class="py-2">Has Remnant</td>
													<td class="py-2" id="alert_prob_hasremenant">{selectedAlert?.prob_hasremenant || 'N/A'}</td>
												</tr>
											</tbody>
										</table>
									</div>
								{/if}
							</div>
						</div>
					</div>
				{:else if currentTab === 'coverage'}
					<!-- Coverage Calculator Tab (matching Flask exactly) -->
					<div class="tab-pane" id="calc-coverage-content">
						<div class="container-fluid">
							<center><h3 class="text-xl font-semibold" style="margin-top: 2rem;">Coverage Calculator</h3></center>
							
							<br>
							
							<i class="text-sm text-gray-700 block mb-4"> 
								Calculate the coverage of the GW localization over time, 
								with choices to limit the coverage calculation to particular sets of instruments, 
								wavelengths, or depth. All fields are optional, but cuts on depths must have an associated unit. 
								If an empty form is submitted, the total reported coverage regardless of depth or band is computed. 
								Once a HEALPIX pixel has been first covered, it is marked as done, to avoid double counting probability 
								when the same field is covered multiple times. After clicking Calculate, be patient, it may take up to 2 minutes 
								to fully compute the coverage profile.
							</i>
							<p class="text-red-600 text-sm mb-4">
								Disclaimer: The DECam Footprint currently breaks in the calculator. We are temporarily approximating its coverage as a circle with 1 deg radius.
							</p>
							
							<br>
							
							<!-- Coverage plot placeholder -->
							<div id="coveragediv" bind:this={plotlyContainer}></div>
							
							<!-- Coverage plot input parameters -->
							<div class="flex flex-wrap gap-4 mb-4">
								<div class="inline-block whitespace-nowrap">
									<b>Instrument</b>
									<select class="ml-2 px-2 py-1 border rounded" multiple id="inst_cov">
										<!-- Instrument options would be populated from API -->
										<option value="all">All Instruments</option>
									</select>
								</div>

								<div class="inline-block whitespace-nowrap">
									<b class="tooltip-container">
										Approximate
										<span class="tooltip-text">
											For footprints with multiple ccd's this will approximate the calculator's input by using a simplified instrument footprint without chip-gaps. It is substantially faster, but does introduce a level of uncertainty in the resulting area and probability.
										</span>
									</b>
									<select class="ml-2 px-2 py-1 border rounded" id="approx_cov">
										<option value="1" selected>Yes</option>
										<option value="0">No</option>
									</select>
								</div>

								<div class="inline-block whitespace-nowrap">
									<b>Depth</b>
									<input type="text" size="7" class="ml-2 px-2 py-1 border rounded" id="depth_cov" placeholder="Optional">
									<b class="ml-2">Depth Unit</b>
									<select class="ml-2 px-2 py-1 border rounded" id="depth_unit">
										<option value="">Select Unit</option>
										<option value="mag">Magnitude</option>
										<option value="flux">FLUX erg cm^-2 s^-1</option>
									</select>
								</div>

								<div class="inline-block whitespace-nowrap">
									<b>Band</b>
									<select class="ml-2 px-2 py-1 border rounded" multiple id="band_cov">
										<option value="">All Bands</option>
										<option value="g">g</option>
										<option value="r">r</option>
										<option value="i">i</option>
									</select>
								</div>

								<div class="inline-block whitespace-nowrap">
									<b class="tooltip-container">
										Spectral Range
										<span class="tooltip-text">
											Filter pointings based on their wavelength, energy, or frequency range
										</span>
									</b>
									<b class="ml-2">Type:</b>
									<select class="ml-1 px-2 py-1 border rounded" id="spectral_range_type">
										<option value="wavelength" selected>Wavelength</option>
										<option value="energy">Energy</option>
										<option value="frequency">Frequency</option>
									</select>
									<b class="ml-2">Range:</b>
									<input size="10" type="text" class="ml-1 px-1 py-1 border rounded" id="spectral_range_low" placeholder="Min"> -
									<input size="10" type="text" class="ml-1 px-1 py-1 border rounded" id="spectral_range_high" placeholder="Max">
									<b class="ml-2">Unit</b>
									<select class="ml-1 px-2 py-1 border rounded" id="spectral_range_unit">
										<option value="nm">nm</option>
										<option value="angstrom">Angstrom</option>
									</select>
								</div>
							</div>
							
							<br><br>
							<div class="flex justify-center">
								<button 
									class="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
									on:click={calculateCoverage}
								>
									Calculate
								</button>
							</div>
						</div>
					</div>
				{:else if currentTab === 'renorm'}
					<!-- Renormalize Skymap Tab (matching Flask exactly) -->
					<div class="tab-pane" id="calc-renorm-skymap-content">
						<div class="container-fluid">
							<center><h3 class="text-xl font-semibold" style="margin-top: 2rem;">Renormalize Skymap</h3></center>
							
							<br>
							
							<i class="text-sm text-gray-700 block mb-4"> 
								Removes pointings from the GW skymap and renormalizes the remaining probability mass, 
								with choices to select particular sets of instruments, 
								and/or pointings that cover certain wavelengths or depth. All fields are optional, but cuts on depths must have an associated unit. 
								If an empty form is submitted, all completed pointings regardless of depth or band are removed from the skymap. 
								Once a HEALPIX pixel has been first covered, it is marked as done, to avoid double counting probability 
								when the same field is covered multiple times. After clicking Download, be patient, it may take up to 3 minutes 
								to fully compute the renormalized skymap and download the HEALPIX fits file. 
								Click Visualize to replace the 50% and 90% localization contours in the figure above with ones calculated from the renormalized skymap.
							</i>
							<p class="text-red-600 text-sm mb-4">
								Disclaimer: The DECam Footprint currently breaks in the calculator. We are temporarily approximating its coverage as a circle with 1 deg radius.
							</p>
							
							<br>
							
							<!-- Renorm skymap input parameters -->
							<div class="flex flex-wrap gap-4 mb-4">
								<div class="inline-block whitespace-nowrap">
									<b class="tooltip-container">
										Instrument:
										<span class="tooltip-text">
											Completed and planned pointings to include from each instrument
										</span>
									</b>
									<b class="ml-2">Completed</b>
									<select class="ml-2 px-2 py-1 border rounded" multiple id="r_inst_cov">
										<option value="all">All Instruments</option>
									</select>
									<b class="ml-2">Planned</b>
									<select class="ml-2 px-2 py-1 border rounded" multiple id="r_inst_plan">
										<option value="all">All Instruments</option>
									</select>
								</div>

								<div class="inline-block whitespace-nowrap">
									<b class="tooltip-container">
										Approximate
										<span class="tooltip-text">
											For footprints with multiple ccd's this will approximate the calculator's input by using a simplified instrument footprint without chip-gaps. It is substantially faster, but does introduce a level of uncertainty in the resulting area and probability.
										</span>
									</b>
									<select class="ml-2 px-2 py-1 border rounded" id="r_approx_cov">
										<option value="1" selected>Yes</option>
										<option value="0">No</option>
									</select>
								</div>

								<div class="inline-block whitespace-nowrap">
									<b>Depth</b>
									<input type="text" size="7" class="ml-2 px-2 py-1 border rounded" id="r_depth_cov" placeholder="Optional">
									<b class="ml-2">Depth Unit</b>
									<select class="ml-2 px-2 py-1 border rounded" id="r_depth_unit">
										<option value="">Select Unit</option>
										<option value="mag">Magnitude</option>
										<option value="flux">FLUX erg cm^-2 s^-1</option>
									</select>
								</div>

								<div class="inline-block whitespace-nowrap">
									<b>Band</b>
									<select class="ml-2 px-2 py-1 border rounded" multiple id="r_band_cov">
										<option value="">All Bands</option>
										<option value="g">g</option>
										<option value="r">r</option>
										<option value="i">i</option>
									</select>
								</div>

								<div class="inline-block whitespace-nowrap">
									<b class="tooltip-container">
										Spectral Range
										<span class="tooltip-text">
											Filter pointings based on their wavelength, energy, or frequency range
										</span>
									</b>
									<b class="ml-2">Type:</b>
									<select class="ml-1 px-2 py-1 border rounded" id="r_spectral_range_type">
										<option value="wavelength" selected>Wavelength</option>
										<option value="energy">Energy</option>
										<option value="frequency">Frequency</option>
									</select>
									<b class="ml-2">Range:</b>
									<input size="10" type="text" class="ml-1 px-1 py-1 border rounded" id="r_spectral_range_low" placeholder="Min"> -
									<input size="10" type="text" class="ml-1 px-1 py-1 border rounded" id="r_spectral_range_high" placeholder="Max">
									<b class="ml-2">Unit</b>
									<select class="ml-1 px-2 py-1 border rounded" id="r_spectral_range_unit">
										<option value="nm">nm</option>
										<option value="angstrom">Angstrom</option>
									</select>
								</div>
							</div>
							
							<br>
							
							<!-- renorm-skymap result placeholder -->
							<div id="renormdiv"></div>
							<div id="renorm-result" class="mt-4 text-sm"></div>
							
							<br>
							
							<div class="flex justify-center gap-4">
								<button 
									class="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
									on:click={downloadRenormalizedSkymap}
								>
									Download
								</button>
								<button 
									class="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
									on:click={visualizeRenormalizedSkymap}
								>
									Visualize
								</button>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
<style>
	/* General component styles */
	.aladin-container {
		width: 100%;
		height: 640px;
		position: relative;
		border: 2px solid #ccc;
		background: #000;
	}

	.loadingtext {
		color: #888;
	}

	.scroll-section {
		max-height: 200px;
		overflow-y: auto;
		border: 1px solid #eee;
		padding: 10px;
		margin-top: 5px;
	}

	/* Custom styles for buttons and triangles */
	.alert_coll::before {
		content: '▶'; /* Right-pointing triangle */
		margin-right: 5px;
		display: inline-block;
		transition: transform 0.2s;
	}

	.alert_coll.down-triangle::before {
		transform: rotate(90deg);
	}
	
	/* Time slider styles */
	.time-slider-container {
		width: 100%;
		margin-top: 1rem;
	}

	.time-slider-wrapper {
		position: relative;
		height: 20px;
		width: 100%;
		cursor: pointer;
	}

	.time-slider-track {
		position: absolute;
		top: 50%;
		left: 0;
		right: 0;
		height: 4px;
		background-color: #e5e7eb; /* gray-200 */
		border-radius: 2px;
		transform: translateY(-50%);
	}

	.time-slider-range {
		position: absolute;
		top: 50%;
		height: 4px;
		background-color: #3b82f6; /* blue-500 */
		border-radius: 2px;
		transform: translateY(-50%);
	}

	.time-slider-handle {
		position: absolute;
		top: 50%;
		width: 16px;
		height: 16px;
		background-color: #3b82f6; /* blue-500 */
		border: 2px solid white;
		border-radius: 50%;
		cursor: grab;
		transform: translate(-50%, -50%);
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
		z-index: 10;
		transition: transform 0.1s ease;
	}

	.time-slider-handle:hover {
		transform: translate(-50%, -50%) scale(1.1);
	}

	.time-slider-handle:active,
	.time-slider-handle.dragging {
		cursor: grabbing;
		transform: translate(-50%, -50%) scale(1.15);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
	}

	.time-labels {
		display: flex;
		justify-content: space-between;
		margin-top: 0.5rem;
	}

	/* Tooltip styles (matching Flask implementation) */
	.tooltip-container {
		position: relative;
		cursor: help;
		border-bottom: 1px dotted #999;
	}

	.tooltip-container .tooltip-text {
		visibility: hidden;
		width: 300px;
		background-color: #555;
		color: white;
		text-align: left;
		border-radius: 6px;
		padding: 8px;
		font-size: 12px;
		font-weight: normal;
		position: absolute;
		z-index: 1000;
		bottom: 125%;
		left: 50%;
		margin-left: -150px;
		opacity: 0;
		transition: opacity 0.3s;
		box-shadow: 0 2px 8px rgba(0,0,0,0.3);
	}

	.tooltip-container .tooltip-text::after {
		content: "";
		position: absolute;
		top: 100%;
		left: 50%;
		margin-left: -5px;
		border-width: 5px;
		border-style: solid;
		border-color: #555 transparent transparent transparent;
	}

	.tooltip-container:hover .tooltip-text {
		visibility: visible;
		opacity: 1;
	}

	/* Bootstrap-style form controls */
	.table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 1rem;
	}

	.table th,
	.table td {
		padding: 0.5rem;
		vertical-align: top;
		border-bottom: 1px solid #dee2e6;
	}

	.table th {
		font-weight: 600;
		border-bottom: 2px solid #dee2e6;
	}

	/* Nav tabs styling (matching Bootstrap) */
	.nav-tabs {
		display: flex;
		flex-wrap: wrap;
		border-bottom: 1px solid #dee2e6;
		background-color: #f8f9fa;
	}

	.nav-tabs .nav-item {
		margin-bottom: -1px;
	}

	.nav-tabs .nav-link {
		border: 1px solid transparent;
		border-top-left-radius: 0.25rem;
		border-top-right-radius: 0.25rem;
		transition: all 0.15s ease-in-out;
	}

	.nav-tabs .nav-link:hover {
		border-color: #e9ecef #e9ecef #dee2e6;
	}

	.nav-tabs .nav-link.active,
	.nav-tabs .nav-item.show .nav-link {
		color: #495057;
		background-color: #fff;
		border-color: #dee2e6 #dee2e6 #fff;
	}

	/* Container and row styles */
	.container-fluid {
		width: 100%;
		padding-right: 15px;
		padding-left: 15px;
		margin-right: auto;
		margin-left: auto;
	}

	.row {
		display: flex;
		flex-wrap: wrap;
		margin-right: -15px;
		margin-left: -15px;
	}

	.col-sm-6 {
		flex: 0 0 50%;
		max-width: 50%;
		padding-right: 15px;
		padding-left: 15px;
	}

	/* Form styling */
	select, input[type="text"] {
		font-size: 14px;
		line-height: 1.5;
	}

	.btn {
		display: inline-block;
		font-weight: 400;
		text-align: center;
		vertical-align: middle;
		user-select: none;
		border: 1px solid transparent;
		padding: 0.375rem 0.75rem;
		font-size: 1rem;
		line-height: 1.5;
		border-radius: 0.25rem;
		transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
		cursor: pointer;
	}

	.btn-primary {
		color: #fff;
		background-color: #007bff;
		border-color: #007bff;
	}

	.btn-primary:hover {
		color: #fff;
		background-color: #0056b3;
		border-color: #004085;
	}
</style>