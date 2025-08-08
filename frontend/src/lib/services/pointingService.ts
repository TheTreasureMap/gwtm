/**
 * @fileoverview API service for pointing operations
 * @description Handles all pointing-related API calls including submission, loading, and validation
 * @category Services
 * @version 1.0.0
 * @author GWTM Team
 * @since 2024-01-25
 */

import { API_ENDPOINTS } from '$lib/config/api';
import { api } from '$lib/api';

// Types
export interface PointingData {
	id?: number;
	graceid: string;
	instrumentid: string;
	obs_status: string;
	ra: number;
	dec: number;
	obs_bandpass: string;
	depth?: number;
	depth_err?: number;
	depth_unit: string;
	planned_obs_time?: string;
	completed_obs_time?: string;
	pos_angle?: number;
	request_doi?: boolean;
	doi_creator_groups?: string;
	doi_url?: string;
}

export interface PointingCreateRequest {
	graceid: string;
	pointings: PointingData[];
	request_doi?: boolean;
	creators?: string[];
	doi_group_id?: number;
}

export interface PointingResponse {
	success: boolean;
	message?: string;
	points?: PointingData[];
	errors?: string[];
	warnings?: string[];
}

export interface GraceIdOption {
	graceid: string;
	alternateid?: string;
}

export interface InstrumentOption {
	id: number;
	instrument_name: string;
	instrument_type: string;
}

export interface BandpassOption {
	name: string;
	value: string;
}

export interface DepthUnitOption {
	name: string;
	value: string;
}

export interface DoiAuthorGroup {
	id: number;
	name: string;
	userid: number;
}

// Note: Authentication and error handling is now managed by the axios client

/**
 * Submit a new pointing observation
 */
export async function submitPointing(pointingData: PointingData): Promise<PointingResponse> {
	// Transform the data to match the API schema
	const transformedPointing = {
		ra: pointingData.ra,
		dec: pointingData.dec,
		instrumentid: parseInt(pointingData.instrumentid), // Convert string to int
		status: pointingData.obs_status, // Map obs_status to status
		band: pointingData.obs_bandpass, // Map obs_bandpass to band
		depth: pointingData.depth,
		depth_err: pointingData.depth_err,
		depth_unit: pointingData.depth_unit,
		pos_angle: pointingData.pos_angle,
		// Use appropriate time field based on status
		time:
			pointingData.obs_status === 'planned'
				? pointingData.planned_obs_time
				: pointingData.completed_obs_time
	};

	const request: PointingCreateRequest = {
		graceid: pointingData.graceid,
		pointings: [transformedPointing],
		request_doi: pointingData.request_doi,
		...(pointingData.doi_creator_groups &&
			pointingData.doi_creator_groups !== 'None' && {
				doi_group_id: parseInt(pointingData.doi_creator_groups)
			})
	};

	// Debug logging
	console.log('Original pointing data:', pointingData);
	console.log('Transformed pointing:', transformedPointing);
	console.log('Final request payload:', request);

	const response = await api.client.post(API_ENDPOINTS.pointings, request);
	return response.data;
}

/**
 * Load existing pointing data by ID
 */
export async function loadPointingById(pointingId: number): Promise<any> {
	const response = await api.client.get(`${API_ENDPOINTS.pointingFromId}?id=${pointingId}`);
	return response.data;
}

/**
 * Get available Grace IDs
 */
export async function getGraceIds(): Promise<GraceIdOption[]> {
	const response = await api.client.get(`${API_ENDPOINTS.queryAlerts}?role=observation`);
	const data = response.data;

	// Process alerts to get unique Grace IDs
	const graceIds = new Map<string, GraceIdOption>();

	data.forEach((alert: any) => {
		if (alert.graceid && !alert.graceid.includes('TEST')) {
			const graceid = alert.alternateid || alert.graceid;
			graceIds.set(graceid, {
				graceid,
				alternateid: alert.alternateid
			});
		}
	});

	// Convert to array and sort
	const sortedGraceIds = Array.from(graceIds.values()).sort((a, b) =>
		b.graceid.localeCompare(a.graceid)
	);

	// Add test event
	sortedGraceIds.push({ graceid: 'TEST_EVENT' });

	return sortedGraceIds;
}

/**
 * Get available instruments
 */
export async function getInstruments(): Promise<InstrumentOption[]> {
	const response = await api.client.get(API_ENDPOINTS.instruments);
	return response.data;
}

/**
 * Get available bandpass options
 */
export async function getBandpassOptions(): Promise<BandpassOption[]> {
	// These match the FastAPI Bandpass enum exactly
	return [
		{ name: 'U', value: 'U' },
		{ name: 'B', value: 'B' },
		{ name: 'V', value: 'V' },
		{ name: 'R', value: 'R' },
		{ name: 'I', value: 'I' },
		{ name: 'J', value: 'J' },
		{ name: 'H', value: 'H' },
		{ name: 'K', value: 'K' },
		{ name: 'u', value: 'u' },
		{ name: 'g', value: 'g' },
		{ name: 'r', value: 'r' },
		{ name: 'i', value: 'i' },
		{ name: 'z', value: 'z' },
		{ name: 'UVW1', value: 'UVW1' },
		{ name: 'UVW2', value: 'UVW2' },
		{ name: 'UVM2', value: 'UVM2' },
		{ name: 'XRT', value: 'XRT' },
		{ name: 'clear', value: 'clear' },
		{ name: 'open', value: 'open' },
		{ name: 'UHF', value: 'UHF' },
		{ name: 'VHF', value: 'VHF' },
		{ name: 'L', value: 'L' },
		{ name: 'S', value: 'S' },
		{ name: 'C', value: 'C' },
		{ name: 'X', value: 'X' },
		{ name: 'other', value: 'other' },
		{ name: 'TESS', value: 'TESS' },
		{ name: 'BAT', value: 'BAT' },
		{ name: 'HESS', value: 'HESS' },
		{ name: 'WISEL', value: 'WISEL' },
		{ name: 'q', value: 'q' }
	];
}

/**
 * Get available depth unit options
 */
export async function getDepthUnitOptions(): Promise<DepthUnitOption[]> {
	// These match the FastAPI enum values
	return [
		{ name: 'AB Magnitude', value: 'ab_mag' },
		{ name: 'Vega Magnitude', value: 'vega_mag' },
		{ name: 'Flux (erg/cm²/s)', value: 'flux_erg' },
		{ name: 'Flux (Jy)', value: 'flux_jy' }
	];
}

/**
 * Get DOI author groups for current user
 */
export async function getDoiAuthorGroups(): Promise<DoiAuthorGroup[]> {
	try {
		const response = await api.client.get(API_ENDPOINTS.doiAuthorGroups);
		return response.data;
	} catch (error) {
		// Return empty array if endpoint doesn't exist or user has no groups
		console.warn('Failed to load DOI author groups:', error);
		return [];
	}
}

/**
 * Load all form options needed for submit pointings
 */
export async function loadFormOptions(): Promise<{
	graceIds: GraceIdOption[];
	instruments: InstrumentOption[];
	bandpassOptions: BandpassOption[];
	depthUnitOptions: DepthUnitOption[];
	doiAuthorGroups: DoiAuthorGroup[];
}> {
	const [graceIds, instruments, bandpassOptions, depthUnitOptions, doiAuthorGroups] =
		await Promise.all([
			getGraceIds(),
			getInstruments(),
			getBandpassOptions(),
			getDepthUnitOptions(),
			getDoiAuthorGroups()
		]);

	return {
		graceIds,
		instruments,
		bandpassOptions,
		depthUnitOptions,
		doiAuthorGroups
	};
}

/**
 * Validate coordinates
 */
export function validateCoordinates(
	ra: number,
	dec: number
): { isValid: boolean; errors: string[] } {
	const errors: string[] = [];

	if (ra < 0 || ra > 360) {
		errors.push('RA must be between 0 and 360 degrees');
	}

	if (dec < -90 || dec > 90) {
		errors.push('Dec must be between -90 and +90 degrees');
	}

	return {
		isValid: errors.length === 0,
		errors
	};
}

/**
 * Format datetime for API submission
 */
export function formatDateTimeForApi(dateTime: string | null): string | undefined {
	if (!dateTime) return undefined;

	try {
		// Ensure the datetime is in ISO format
		const date = new Date(dateTime);
		if (isNaN(date.getTime())) return undefined;

		return date.toISOString();
	} catch {
		return undefined;
	}
}

/**
 * Parse instrument ID and type from combined string
 */
export function parseInstrumentId(instrumentValue: string): { id: number; type: string } | null {
	if (!instrumentValue) return null;

	const parts = instrumentValue.split('_');
	if (parts.length !== 2) return null;

	const id = parseInt(parts[0]);
	if (isNaN(id)) return null;

	return {
		id,
		type: parts[1]
	};
}
