/**
 * @fileoverview Astronomical calculation utilities for sun and moon positions
 * @author GWTM Team
 * @since 2024-01-25
 */

/**
 * Sun and moon position data structure
 */
export interface SunMoonData {
	sun_ra: number;
	sun_dec: number;
	moon_ra: number;
	moon_dec: number;
}

/**
 * Fetch sun and moon positions from FastAPI backend using Astropy calculations
 * @param timeOfSignal - Time of gravitational wave signal as ISO string
 * @returns Promise resolving to sun/moon positions or null if unavailable
 */
export async function fetchSunMoonPositions(timeOfSignal: string): Promise<SunMoonData | null> {
	console.log('fetchSunMoonPositions called with timeOfSignal:', timeOfSignal);

	if (!timeOfSignal) {
		console.log('No time_of_signal available, returning null');
		return null;
	}

	try {
		console.log('Fetching sun/moon positions from FastAPI backend for:', timeOfSignal);

		// Call our temporary FastAPI endpoint (same calculation as Flask version)
		// Use relative URL so it works in all environments (local dev, K8s, production)
		const url = `/temp_sun_moon_positions?time_of_signal=${encodeURIComponent(timeOfSignal)}`;
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
		return calculateApproximateSunMoonPositions(timeOfSignal);
	}
}

/**
 * Calculate approximate sun and moon positions when API is unavailable
 * @param timeOfSignal - Time of gravitational wave signal as ISO string
 * @returns Approximate sun/moon position data
 */
function calculateApproximateSunMoonPositions(timeOfSignal: string): SunMoonData {
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

/**
 * Convert a Date object to Modified Julian Date (MJD)
 * @param date - Date to convert
 * @returns Modified Julian Date rounded to 3 decimal places
 */
export function convertToMJD(date: Date): number {
	// MJD = JD - 2400000.5
	// JD = (Unix timestamp / 86400) + 2440587.5
	const unixTimestamp = date.getTime() / 1000; // Convert to seconds
	const julianDate = unixTimestamp / 86400 + 2440587.5;
	const mjd = julianDate - 2400000.5;
	return Math.round(mjd * 1000) / 1000; // Round to 3 decimal places like Flask
}

/**
 * Get default sun/moon positions when no data is available
 * @returns Default sun/moon position data
 */
export function getDefaultSunMoonPositions(): SunMoonData {
	return {
		sun_ra: 180.0, // Default sun position
		sun_dec: 0.0,
		moon_ra: 270.0, // Default moon position
		moon_dec: 10.0
	};
}
