<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	
	export let aladin: any = null;
	export let footprintData: any = null;
	export let contourData: any = null;
	export let detectionContours: any = null;
	export let galaxyData: any[] = [];
	export let candidateData: any[] = [];
	export let icecubeData: any[] = [];
	export let sunMoonData: { sun_ra: number, sun_dec: number, moon_ra: number, moon_dec: number } | null = null;
	export let grbCoverage: any = null;
	export let timeRange: number[] = [-1, 7];
	
	const dispatch = createEventDispatcher();
	
	// Overlay management state
	let overlayLists = {
		instOverlays: [],
		detectionOverlays: [],
		grbOverlays: [],
		galaxyMarkers: [],
		candidateMarkers: [],
		icecubeMarkers: []
	};
	
	// Expose overlay lists to parent
	export function getOverlayLists() {
		return overlayLists;
	}
	
	// Clear all data overlays
	export function clearDataOverlays() {
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
	
	// Add sun and moon overlays
	export function addSunMoonOverlays() {
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
	
	// Add contour layer
	export function addContourLayer() {
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
	
	// Add footprint layer with time filtering
	export function addFootprintLayerWithTimeFilter() {
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
	
	// Add basic footprint layer (delegates to time-filtered version)
	export function addFootprintLayer() {
		if (!footprintData) return;
		addFootprintLayerWithTimeFilter();
	}
	
	// Generic function to add markers to Aladin (matching Flask pattern)
	export function addMarkersToAladin(markerData: any[], catalogName: string, color: string) {
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
	
	// Add galaxy layer
	export function addGalaxyLayer() {
		if (!galaxyData || galaxyData.length === 0) return;
		
		try {
			const markers = addMarkersToAladin(galaxyData, 'Galaxies', '#FF6B35');
			overlayLists.galaxyMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add galaxy layer:', err);
		}
	}
	
	// Add candidate layer
	export function addCandidateLayer() {
		if (!candidateData || candidateData.length === 0) return;
		
		try {
			const markers = addMarkersToAladin(candidateData, 'Candidates', '#8E44AD');
			overlayLists.candidateMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add candidate layer:', err);
		}
	}
	
	// Add IceCube layer
	export function addIceCubeLayer() {
		if (!icecubeData || icecubeData.length === 0) return;
		
		try {
			const markers = addMarkersToAladin(icecubeData, 'IceCube Events', '#0080FF');
			overlayLists.icecubeMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add IceCube layer:', err);
		}
	}
	
	// Add MOC layer
	export function addMOCLayer(mocData: any[]) {
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
	
	// Filter footprints by time range (called from time controls)
	export function filterFootprintsByTime() {
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
			if (contourData || detectionContours) {
				addContourLayer();
			}
			
			aladin.view.requestRedraw();
		} catch (err) {
			console.error('Failed to filter footprints by time:', err);
		}
	}
	
	// Animation helper function for markers
	export function animateToMarker(targetName: string, markerData: any[]) {
		if (!aladin || !markerData.length) return;
		
		try {
			// Find the marker with matching name
			for (const group of markerData) {
				if (group.markers) {
					const marker = group.markers.find((m: any) => m.name === targetName);
					if (marker) {
						aladin.gotoRaDec(marker.ra, marker.dec);
						aladin.setFov(1); // Zoom in
						return;
					}
				}
			}
		} catch (err) {
			console.error('Failed to animate to marker:', err);
		}
	}
</script>

<!-- This component is purely functional - no template needed -->