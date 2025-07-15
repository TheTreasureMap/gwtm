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
					aladinContainer = containerById;
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
		// Cleanup
		if (aladin) {
			try {
				aladin.removeLayers();
			} catch (e) {
				console.warn('Error cleaning up Aladin:', e);
			}
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
				} catch (err) {
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
			
		} catch (err) {
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
			let dataLines = [];
			
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
					const detectionData = await gwtmApi.getAlertDetectionOverlays?.(selectedAlert.id);
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
				footprintData = await gwtmApi.getAlertInstrumentsFootprints(graceid, pointingStatus);
				
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
				overlayLists.grbOverlays = addMOCLayer(grbCoverage);
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
			function aladinSetImage(aladin, imgsource, imgname, pos_ra, pos_dec) {
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
				
				overlayLists.detectionOverlays.push({
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
			overlayLists.galaxyMarkers = markers;
		} catch (err) {
			console.error('Failed to add galaxy layer:', err);
		}
	}

	function addCandidateLayer() {
		if (!candidateData || candidateData.length === 0) return;
		
		try {
			const markers = addMarkersToAladin(candidateData, 'Candidates', '#8E44AD');
			overlayLists.candidateMarkers = markers;
		} catch (err) {
			console.error('Failed to add candidate layer:', err);
		}
	}

	function addIceCubeLayer() {
		if (!icecubeData || icecubeData.length === 0) return;
		
		try {
			const markers = addMarkersToAladin(icecubeData, 'IceCube Events', '#0080FF');
			overlayLists.icecubeMarkers = markers;
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
				const nameIdStr = markerGroup.name.replace(/\s+/g, '');
				if (groupIdStr === nameIdStr) {
					if (show) {
						markerGroup.markerlayer?.show();
						if (markerGroup.has_overlay) {
							markerGroup.overlaylayer?.show();
						}
					} else {
						markerGroup.markerlayer?.hide();
						if (markerGroup.has_overlay) {
							markerGroup.overlaylayer?.hide();
						}
					}
					markerGroup.toshow = show;
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
			const groupName = group.name;
			const idStr = groupName.replace(/\s+/g, '');
			const color = group.color || '#FF6B35';
			
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
			
			const markers = group.markers || [];
			for (const marker of markers) {
				html += `
					<li>
						<fieldset>
							<label>
								<div 
									id="${marker.name}" 
									class="text-xs text-blue-600 hover:text-blue-800 cursor-pointer py-1"
									onclick="handleMarkerClick('${marker.name}')"
								>
									${marker.name}
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
				x: coverageData.time || [],
				y: coverageData.probability || [],
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
			if (aladin && selectedAlert.avgra !== undefined && selectedAlert.avgdec !== undefined) {
				try {
					aladin.animateToRaDec(selectedAlert.avgra, selectedAlert.avgdec, 2); // 2-second animation
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

	// Remove this reactive statement since we now handle it in the slider events

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
				const overlays = overlayLists[key as keyof typeof overlayLists];
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
					(overlayLists[key as keyof typeof overlayLists] as any[]).length = 0;
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
			
			const result = await gwtmApi.renormalizeSkymap({
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
			overlayLists.instOverlays.forEach((overlay: any) => {
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
			
			overlayLists.instOverlays = newOverlays;
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
				if (overlay.tocolor === targetColor) {
					if (target.checked) {
						overlay.contour?.show();
						overlay.toshow = true;
					} else {
						overlay.contour?.hide();
						overlay.toshow = false;
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
		if (!overlayLists.instOverlays) return;
		
		try {
			overlayLists.instOverlays.forEach((overlay: any) => {
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

	<!-- Right column: Follow-up controls (30% width) -->
	<div style="width: 30%;">
		<div class="bg-white border rounded-lg">
			<div class="bg-gray-50 px-4 py-3 border-b">
				<h3 class="text-lg font-medium text-gray-900">Follow-Up</h3>
			</div>
			<div class="p-4 space-y-4">

	{#if loading}
		<div class="flex justify-center py-8">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<span class="ml-2 text-gray-600">Loading visualization...</span>
		</div>
	{:else if error}
		<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
			<strong>Visualization Error:</strong> {error}
			<details class="mt-2">
				<summary class="cursor-pointer text-sm">Debug Info</summary>
				<pre class="text-xs mt-2 bg-gray-100 p-2 rounded">
					graceid: {graceid}
					alert: {JSON.stringify(alert, null, 2)}
					aladinContainer: {aladinContainer ? 'available' : 'missing'}
					window.A: {typeof window !== 'undefined' ? typeof (window as any).A : 'undefined'}
					window.Plotly: {typeof window !== 'undefined' ? typeof (window as any).Plotly : 'undefined'}
				</pre>
			</details>
		</div>
	{:else}
				<!-- Compact controls for Follow-Up section -->
				<div class="space-y-3">
					<div>
						<h4 class="text-sm font-medium text-gray-700 mb-2">Instruments</h4>
						<div class="space-y-1 max-h-24 overflow-y-auto text-xs">
							{#if footprintData && Array.isArray(footprintData)}
								{#each footprintData as inst, i}
									<label class="flex items-center hover:bg-gray-50 p-1 rounded">
										<input 
											type="checkbox" 
											checked={true}
											class="mr-1 text-xs"
											data-color={inst.color || '#ff0000'}
											on:change={(e) => {
												toggleInstrumentOverlay(e.target, overlayLists.instOverlays);
												updateHideShowButton();
											}}
										/>
										<div 
											class="w-2 h-2 mr-1 border border-gray-300 rounded-sm"
											style="background-color: {inst.color || '#ff0000'}"
										></div>
										<span class="text-xs truncate">{inst.name || `Inst ${i + 1}`}</span>
									</label>
								{/each}
							{:else}
								<div class="text-gray-500 italic text-xs">Loading instruments...</div>
							{/if}
						</div>
					</div>
					
					<div>
						<h4 class="text-sm font-medium text-gray-700 mb-2">Time Range</h4>
						<div class="text-xs text-gray-600 mb-1">
							{timeRange[0].toFixed(1)} - {timeRange[1].toFixed(1)} days
						</div>
					</div>
				</div>
	{/if}
		</div>
	</div>
	</div>
</div>


<div class="space-y-6">
	{#if !loading && !error}

		<!-- Controls Section -->
		<div class="bg-white border rounded-lg p-4">
			<h3 class="text-lg font-semibold mb-3">Visualization Controls</h3>
					
					<!-- Instrument Controls -->
					<div class="mb-4">
						<div class="flex items-center gap-2 mb-2">
							<button 
								class="text-blue-600 hover:text-blue-800 text-sm"
								on:click={() => showFootprints = !showFootprints}
							>
								{showFootprints ? '▼' : '▶'}
							</button>
							<button 
								class="text-sm bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
								on:click={() => {
									overlayLists.instOverlays.forEach(overlay => {
										if (overlay.contour) {
											showFootprints ? overlay.contour.hide() : overlay.contour.show();
										}
									});
									showFootprints = !showFootprints;
								}}
							>
								{showFootprints ? 'Hide' : 'Show'}
							</button>
							<h4 class="font-medium text-gray-700">Instruments</h4>
						</div>
						
						<!-- Instrument list will be populated dynamically -->
						<div class="instruments-list space-y-1 max-h-32 overflow-y-auto text-sm">
							{#if footprintData && Array.isArray(footprintData)}
								{#each footprintData as inst, i}
									<label class="flex items-center hover:bg-gray-50 p-1 rounded">
										<input 
											type="checkbox" 
											checked={true}
											class="mr-2"
											data-color={inst.color || '#ff0000'}
											on:change={(e) => {
												toggleInstrumentOverlay(e.target, overlayLists.instOverlays);
												updateHideShowButton();
											}}
										/>
										<div 
											class="w-3 h-3 mr-2 border border-gray-300"
											style="background-color: {inst.color || '#ff0000'}"
										></div>
										<span class="text-xs">{inst.name || `Instrument ${i + 1}`}</span>
									</label>
								{/each}
							{:else}
								<div class="text-gray-500 italic">...Loading...</div>
							{/if}
						</div>
					</div>

					<!-- GRB Coverage -->
					<div class="mb-4">
						<div class="flex items-center gap-2 mb-2">
							<button 
								class="text-blue-600 hover:text-blue-800 text-sm"
								on:click={() => showGrbCoverage = !showGrbCoverage}
							>
								{showGrbCoverage ? '▼' : '▶'}
							</button>
							<button 
								class="text-sm bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
								on:click={() => showGrbCoverage = !showGrbCoverage}
							>
								{showGrbCoverage ? 'Hide' : 'Show'}
							</button>
							<h4 class="font-medium text-gray-700">GRB Coverage</h4>
						</div>
					</div>

					<!-- Sources Section -->
					<div class="mb-4">
						<h3 class="text-lg font-semibold mb-3">Sources</h3>
						
						<!-- Galaxies -->
						<div class="mb-3">
							<div class="flex items-center gap-2 mb-2">
								<button 
									class="text-blue-600 hover:text-blue-800 text-sm"
									on:click={() => showGalaxies = !showGalaxies}
								>
									{showGalaxies ? '▼' : '▶'}
								</button>
								<button 
									class="text-sm bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
									on:click={() => {
										if (!showGalaxies && galaxyData.length === 0) {
											loadGalaxies();
										} else if (galaxyData.length > 0) {
											// Toggle visibility of existing markers
											overlayLists.galaxyMarkers.forEach(markerGroup => {
												toggleMarkerGroup([markerGroup], markerGroup.name, !showGalaxies);
											});
										}
										showGalaxies = !showGalaxies;
									}}
								>
									{galaxyData.length > 0 ? (showGalaxies ? 'Hide' : 'Show') : 'Get'}
								</button>
								<h4 class="font-medium text-gray-700">Galaxies</h4>
							</div>
							
							<!-- Galaxy List (collapsible) -->
							{#if showGalaxies && galaxyData.length > 0}
								<div class="max-h-32 overflow-y-auto text-sm space-y-1">
									{#each galaxyData as group}
										<div class="border-l-2 border-orange-300 pl-2">
											<div class="font-medium text-orange-700 mb-1">{group.name}</div>
											{#if group.markers}
												{#each group.markers as marker}
													<button 
														class="block w-full text-left px-2 py-1 text-xs hover:bg-orange-50 rounded"
														on:click={() => animateToMarker(marker.name, galaxyData)}
													>
														{marker.name}
													</button>
												{/each}
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>

						<!-- Candidates -->
						<div class="mb-3">
							<div class="flex items-center gap-2 mb-2">
								<button 
									class="text-blue-600 hover:text-blue-800 text-sm"
									on:click={() => showCandidates = !showCandidates}
								>
									{showCandidates ? '▼' : '▶'}
								</button>
								<button 
									class="text-sm bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
									on:click={() => {
										if (!showCandidates && candidateData.length === 0) {
											loadCandidates();
										}
										showCandidates = !showCandidates;
									}}
								>
									{candidateData.length > 0 ? (showCandidates ? 'Hide' : 'Show') : 'Get'}
								</button>
								<h4 class="font-medium text-gray-700">Candidates</h4>
							</div>
							
							<!-- Candidate List (collapsible) -->
							{#if showCandidates && candidateData.length > 0}
								<div class="max-h-32 overflow-y-auto text-sm space-y-1">
									{#each candidateData as group}
										<div class="border-l-2 border-purple-300 pl-2">
											<div class="font-medium text-purple-700 mb-1">{group.name}</div>
											{#if group.markers}
												{#each group.markers as marker}
													<button 
														class="block w-full text-left px-2 py-1 text-xs hover:bg-purple-50 rounded"
														on:click={() => animateToMarker(marker.name, galaxyData)}
													>
														{marker.name}
													</button>
												{/each}
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>

						<!-- IceCube -->
						<div class="mb-3">
							<div class="flex items-center gap-2 mb-2">
								<button 
									class="text-blue-600 hover:text-blue-800 text-sm"
									on:click={() => showIceCube = !showIceCube}
								>
									{showIceCube ? '▼' : '▶'}
								</button>
								<button 
									class="text-sm bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
									on:click={() => {
										if (!showIceCube && icecubeData.length === 0) {
											loadIceCubeData();
										}
										showIceCube = !showIceCube;
									}}
								>
									{icecubeData.length > 0 ? (showIceCube ? 'Hide' : 'Show') : 'Get'}
								</button>
								<h4 class="font-medium text-gray-700">IceCube Events</h4>
							</div>
							
							<!-- IceCube List (collapsible) -->
							{#if showIceCube && icecubeData.length > 0}
								<div class="max-h-32 overflow-y-auto text-sm space-y-1">
									{#each icecubeData as group}
										<div class="border-l-2 border-blue-300 pl-2">
											<div class="font-medium text-blue-700 mb-1">{group.name}</div>
											{#if group.markers}
												{#each group.markers as marker}
													<button 
														class="block w-full text-left px-2 py-1 text-xs hover:bg-blue-50 rounded"
														on:click={() => animateToMarker(marker.name, icecubeData)}
													>
														{marker.name}
													</button>
												{/each}
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>
					</div>
				</div>

		<!-- Time Slider Section (matching Flask layout) -->
		<div class="mt-4 bg-white border rounded-lg p-4">
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
				
				<!-- Dual range slider (matching Flask) -->
				<div class="relative mt-4">
					<input 
						type="range" 
						min={minTime}
						max={maxTime}
						step="0.1"
						bind:value={timeRange[0]}
						class="absolute w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
						style="z-index: 1;"
						on:input={() => {
							if (timeRange[0] > timeRange[1]) {
								timeRange[0] = timeRange[1];
							}
							filterFootprintsByTime();
						}}
					/>
					<input 
						type="range" 
						min={minTime}
						max={maxTime}
						step="0.1"
						bind:value={timeRange[1]}
						class="absolute w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
						style="z-index: 2;"
						on:input={() => {
							if (timeRange[1] < timeRange[0]) {
								timeRange[1] = timeRange[0];
							}
							filterFootprintsByTime();
						}}
					/>
				</div>
			</div>
		</div>

		<!-- Event Explorer Tabs (matching Flask) -->
		<div class="bg-white border rounded-lg overflow-hidden mt-4">
			<!-- Tab Navigation -->
			<div class="bg-gray-50 border-b">
				<nav class="flex">
					<div class="px-4 py-3 text-sm font-medium text-gray-500">
						Event Explorer:
					</div>
					<button
						class="px-4 py-3 text-sm font-medium border-b-2 transition-colors
							{currentTab === 'info' 
								? 'text-blue-600 border-blue-600' 
								: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
						on:click={() => currentTab = 'info'}
					>
						Summary
					</button>
					<button
						class="px-4 py-3 text-sm font-medium border-b-2 transition-colors
							{currentTab === 'coverage' 
								? 'text-blue-600 border-blue-600' 
								: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
						on:click={() => currentTab = 'coverage'}
					>
						Coverage Calculator
					</button>
					<button
						class="px-4 py-3 text-sm font-medium border-b-2 transition-colors
							{currentTab === 'renorm' 
								? 'text-blue-600 border-blue-600' 
								: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
						on:click={() => currentTab = 'renorm'}
					>
						Renormalize Skymap
					</button>
				</nav>
			</div>

			<!-- Tab Content -->
			<div class="p-6">
				{#if currentTab === 'info'}
					<!-- Summary Tab -->
					<div class="text-center text-gray-600">
						<p>Summary information for consistency with Flask version</p>
					</div>
				{:else if currentTab === 'coverage'}
					<!-- Coverage Calculator Tab -->
					<div>
						<h3 class="text-lg font-semibold mb-4">Coverage Calculator</h3>
						<p class="text-sm text-gray-600 mb-4">
							Calculate the coverage of the GW localization over time, with choices to limit the coverage calculation to particular sets of instruments, wavelengths, or depth. All fields are optional.
						</p>
						
						<!-- Coverage Calculator Controls -->
						<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Instrument</label>
								<select class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
									<option value="">All Instruments</option>
									<!-- Instrument options would be populated dynamically -->
								</select>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Approximate</label>
								<select class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
									<option value="1" selected>Yes</option>
									<option value="0">No</option>
								</select>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Depth</label>
								<input 
									type="text" 
									placeholder="Optional"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Depth Unit</label>
								<select class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
									<option value="">Select Unit</option>
									<option value="mag">Magnitude</option>
									<option value="flux_erg">FLUX erg cm^-2 s^-1</option>
								</select>
							</div>
						</div>
						
						<div class="text-center mb-6">
							<button 
								class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
								on:click={calculateCoverage}
								disabled={loading}
							>
								{loading ? 'Calculating...' : 'Calculate'}
							</button>
						</div>
						
						<!-- Coverage Plot -->
						<div 
							bind:this={plotlyContainer}
							class="w-full border border-gray-200 rounded-lg"
							style="height: 400px;"
						></div>
					</div>
				{:else if currentTab === 'renorm'}
					<!-- Renormalize Skymap Tab -->
					<div>
						<h3 class="text-lg font-semibold mb-4">Renormalize Skymap</h3>
						<p class="text-sm text-gray-600 mb-4">
							Removes pointings from the GW skymap and renormalizes the remaining probability mass. Click Visualize to replace the localization contours with ones calculated from the renormalized skymap.
						</p>
						<p class="text-sm text-red-600 mb-4">
							Disclaimer: The DECam Footprint currently breaks in the calculator. We are temporarily approximating its coverage as a circle with 1 deg radius.
						</p>
						
						<!-- Renormalization Controls -->
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Completed Pointings</label>
								<select class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
									<option value="">All Instruments</option>
								</select>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Planned Pointings</label>
								<select class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
									<option value="">All Instruments</option>
								</select>
							</div>
						</div>
						
						<!-- Result Area -->
						<div id="renorm-result" class="mb-4 p-4 bg-gray-50 rounded-lg min-h-[50px] flex items-center justify-center text-gray-500">
							Select options and click a button to proceed
						</div>
						
						<div class="flex gap-4 justify-center">
							<button 
								class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
								on:click={downloadRenormalizedSkymap}
								disabled={loading}
							>
								{loading ? 'Processing...' : 'Download'}
							</button>
							<button 
								class="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
								on:click={visualizeRenormalizedSkymap}
								disabled={loading}
							>
								{loading ? 'Processing...' : 'Visualize'}
							</button>
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	/* Custom styles for visualization controls */
	input[type="range"] {
		appearance: none;
		height: 6px;
		background: #ddd;
		border-radius: 3px;
		outline: none;
	}
	
	input[type="range"]::-webkit-slider-thumb {
		appearance: none;
		width: 20px;
		height: 20px;
		background: #4CAF50;
		border-radius: 50%;
		cursor: pointer;
	}
	
	input[type="range"]::-moz-range-thumb {
		width: 20px;
		height: 20px;
		background: #4CAF50;
		border: none;
		border-radius: 50%;
		cursor: pointer;
	}
	
	/* Ensure Aladin container and canvas are visible */
	.aladin-container {
		min-height: 640px !important;
		overflow: visible !important;
	}
	
	:global(.aladin-container canvas) {
		width: 100% !important;
		height: 100% !important;
		display: block !important;
	}
	
	:global(.aladin-container .aladin-location) {
		color: white !important;
		background: rgba(0,0,0,0.7) !important;
		padding: 5px !important;
	}
</style>