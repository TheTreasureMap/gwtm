<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let aladin: any = null;
	export let footprintData: any = null;
	export let contourData: any = null;
	export let detectionContours: any = null;
	export let galaxyData: any[] = [];
	export let candidateData: any[] = [];
	export let icecubeData: any[] = [];
	export let sunMoonData: {
		sun_ra: number;
		sun_dec: number;
		moon_ra: number;
		moon_dec: number;
	} | null = null;
	export const grbCoverage: any = null;
	export let timeRange: number[] = [-1, 7];

	const dispatch = createEventDispatcher();

	// Tracks instrument colors the user has explicitly hidden via checkboxes
	let hiddenInstrumentColors: Set<string> = new Set();

	export function setHiddenInstruments(colors: Set<string>): void {
		hiddenInstrumentColors = colors;
	}

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
			Object.keys(overlayLists).forEach((key) => {
				const overlays = (overlayLists as any)[key as keyof typeof overlayLists];
				if (Array.isArray(overlays)) {
					overlays.forEach((overlay: any) => {
						try {
							if (overlay.markerlayer) overlay.markerlayer.removeAll();
							if (overlay.overlaylayer && overlay.overlaylayer.removeAll)
								overlay.overlaylayer.removeAll();
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
			function aladinSetImage(
				aladin: any,
				imgsource: any,
				imgname: any,
				pos_ra: any,
				pos_dec: any
			) {
				const IMG = new Image();
				IMG.src = imgsource;
				const cat = A.catalog({ shape: IMG, name: imgname });
				aladin.addCatalog(cat);
				cat.addSources(A.source(pos_ra, pos_dec));
			}

			// Add sun and moon images using the exact Flask approach
			aladinSetImage(
				aladin,
				'/sun-logo-100.png',
				'Sun at GW T0',
				sunMoonData.sun_ra,
				sunMoonData.sun_dec
			);
			aladinSetImage(
				aladin,
				'/moon-supersmall.png',
				'Moon at GW T0',
				sunMoonData.moon_ra,
				sunMoonData.moon_dec
			);

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
		if (!footprintData || !Array.isArray(footprintData)) {
			console.log('No footprint data available:', {
				footprintData,
				isArray: Array.isArray(footprintData)
			});
			return;
		}

		console.log('Adding footprint layer with data:', {
			footprintCount: footprintData.length,
			timeRange,
			sampleData: footprintData[0]
		});

		try {
			const A = (window as any).A;
			const newOverlays: any[] = [];

			footprintData.forEach((instData: any, i: number) => {
				let hasVisibleContours = false;
				let totalContours = 0;
				let visibleContours = 0;

				console.log(`Processing instrument ${i}:`, {
					name: instData.name,
					color: instData.color,
					contourCount: instData.contours?.length || 0,
					sampleContour: instData.contours?.[0]
				});

				// First, check if this instrument has any contours within time range
				if (instData.contours && Array.isArray(instData.contours)) {
					totalContours = instData.contours.length;
					instData.contours.forEach((contour: any) => {
						// Check if contour time is within range (strict filtering like Flask)
						if (
							typeof contour.time === 'number' &&
							contour.time >= timeRange[0] &&
							contour.time <= timeRange[1]
						) {
							if (contour.polygon && Array.isArray(contour.polygon)) {
								hasVisibleContours = true;
								visibleContours++;
							}
						}
					});
				}

				console.log(`Instrument ${i} processed:`, {
					totalContours,
					visibleContours,
					hasVisibleContours,
					timeRange
				});

				// Only create and add overlay if there are visible contours (like Flask)
				if (hasVisibleContours) {
					const overlay = A.graphicOverlay({
						id: i,
						color: instData.color || '#ff0000',
						lineWidth: 2,
						name: instData.name || `Instrument ${i + 1}`
					});

					aladin.addOverlay(overlay);

					// Batch all footprints within time range into a single array
					const footprintsToAdd: any[] = [];
					instData.contours.forEach((contour: any) => {
						if (
							typeof contour.time === 'number' &&
							contour.time >= timeRange[0] &&
							contour.time <= timeRange[1]
						) {
							if (contour.polygon && Array.isArray(contour.polygon)) {
								footprintsToAdd.push(A.polygon(contour.polygon));
							}
						}
					});

					// Add all footprints at once for better performance
					if (footprintsToAdd.length > 0) {
						overlay.addFootprints(footprintsToAdd);
					}

					const instColor = instData.color || '#ff0000';
					const userHidden = hiddenInstrumentColors.has(instColor);
					if (userHidden) {
						overlay.hide();
					}
					newOverlays.push({
						contour: overlay,
						toshow: !userHidden,
						tocolor: instColor,
						name: instData.name || `Instrument ${i + 1}`
					});
				}
				// If no visible contours, don't create overlay at all (like Flask)
			});

			overlayLists.instOverlays = newOverlays as any[];
			console.log(
				`Footprint layer complete: ${newOverlays.length} instruments visible in time range [${timeRange[0]}, ${timeRange[1]}]`
			);
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
		const A = (window as any).A;
		console.log(`[Galaxy debug] addMarkersToAladin called for '${catalogName}':`, {
			aladinReady: !!aladin,
			windowAReady: typeof A !== 'undefined',
			markerDataLength: markerData?.length,
			firstGroupMarkersLength: markerData?.[0]?.markers?.length
		});
		if (!aladin || !markerData.length) {
			console.warn(
				`[Galaxy debug] addMarkersToAladin early return — aladin: ${!!aladin}, markerData.length: ${markerData?.length}`
			);
			return [];
		}

		try {
			const markerLayers: any[] = [];

			markerData.forEach((group: any, i: number) => {
				const groupName = group.name || `${catalogName} ${i + 1}`;
				const markers = group.markers || [];
				console.log(
					`[Galaxy debug] group ${i} '${groupName}': ${markers.length} markers, sample:`,
					markers[0]
				);

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
	export function addGalaxyLayer(data: any[] = galaxyData) {
		console.log('[Galaxy debug] addGalaxyLayer called:', {
			galaxyDataLength: data?.length,
			aladinReady: !!aladin
		});
		if (!data || data.length === 0) {
			console.warn('[Galaxy debug] addGalaxyLayer early return — data empty or null');
			return;
		}

		try {
			const markers = addMarkersToAladin(data, 'Galaxies', '#FF6B35');
			console.log('[Galaxy debug] addMarkersToAladin returned', markers?.length, 'marker layers');
			overlayLists.galaxyMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add galaxy layer:', err);
		}
	}

	// Add candidate layer
	export function addCandidateLayer(data: any[] = candidateData) {
		if (!data || data.length === 0) return;

		try {
			const markers = addMarkersToAladin(data, 'Candidates', '#8E44AD');
			overlayLists.candidateMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add candidate layer:', err);
		}
	}

	// Add IceCube layer
	export function addIceCubeLayer(data: any[] = icecubeData) {
		if (!data || data.length === 0) return;

		try {
			const markers = addMarkersToAladin(data, 'IceCube Events', '#0080FF');
			overlayLists.icecubeMarkers = markers as any[];
		} catch (err) {
			console.error('Failed to add IceCube layer:', err);
		}
	}

	// Show or hide marker layers by data type, optionally scoped to a specific group name
	export function toggleMarkers(dataType: string, show: boolean, groupName: string = 'all') {
		const layerMap: Record<string, any[]> = {
			galaxies: overlayLists.galaxyMarkers,
			candidates: overlayLists.candidateMarkers,
			icecube: overlayLists.icecubeMarkers
		};
		const layers = layerMap[dataType];
		if (!layers) return;
		const targets = groupName === 'all' ? layers : layers.filter((l: any) => l.name === groupName);
		targets.forEach((layer: any) => {
			if (show) {
				layer.markerlayer?.show();
				if (layer.has_overlay) layer.overlaylayer?.show();
			} else {
				layer.markerlayer?.hide();
				if (layer.has_overlay) layer.overlaylayer?.hide();
			}
		});
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
			// Use Flask approach: complete removal and recreation like the slider function
			console.log('Filtering footprints by time, using v3 removeOverlays approach');

			// v3: aladin.removeOverlays() - clear ALL overlays except base sky survey
			// This is the key difference - removes EVERYTHING and rebuilds
			aladin.removeOverlays();

			// Clear our tracked overlay lists
			Object.keys(overlayLists).forEach((key) => {
				const overlays = (overlayLists as any)[key as keyof typeof overlayLists];
				if (Array.isArray(overlays)) {
					overlays.length = 0;
				}
			});

			// Flask approach: Rebuild everything from scratch after clearing
			// Re-add sun/moon images (they should always be visible)
			if (sunMoonData) {
				addSunMoonOverlays();
			}

			// Recreate footprints with time filtering (this will only create overlays for visible contours)
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
