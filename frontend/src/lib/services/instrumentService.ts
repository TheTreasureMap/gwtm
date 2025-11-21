/**
 * @fileoverview API service for instrument operations
 * @description Handles all instrument-related API calls including submission, loading options, and preview
 * @category Services
 * @version 1.0.0
 * @author GWTM Team
 * @since 2025-01-10
 */

import { API_ENDPOINTS } from '$lib/config/api';
import { api } from '$lib/api';

// Types and interfaces
export interface InstrumentData {
	instrument_name: string;
	nickname?: string;
	instrument_type: string; // String value from enum (e.g., "1", "2") - converted to int for API
	footprint_type: string;
	unit: string;
	height?: number;
	width?: number;
	radius?: number;
	polygon?: string;
}

export interface InstrumentResponse {
	success: boolean;
	message?: string;
	instrument?: {
		id: number;
		instrument_name: string;
		nickname?: string;
		instrument_type: number;
		footprint_type: string;
		unit: string;
		height?: number;
		width?: number;
		radius?: number;
		polygon?: string;
	};
	errors?: string[];
}

export interface InstrumentOption {
	id: number;
	instrument_name: string;
	nickname?: string;
	instrument_type: string;
	datecreated?: string;
	submitterid?: number;
}

export interface EnumOption {
	name: string;
	value: string;
	description?: string;
}

/**
 * Submit a new instrument
 */
export async function submitInstrument(
	instrumentData: InstrumentData
): Promise<InstrumentResponse> {
	try {
		// Convert string instrument_type back to integer for API
		const apiData = {
			...instrumentData,
			instrument_type: parseInt(instrumentData.instrument_type, 10)
		};

		const response = await api.client.post(API_ENDPOINTS.instruments, apiData);
		return response.data;
	} catch (error: unknown) {
		// Handle validation errors from the API
		const axiosError = error as {
			response?: {
				status?: number;
				data?: { detail?: Array<{ loc?: string[]; msg?: string }> | string };
			};
		};
		if (axiosError.response?.status === 422 && Array.isArray(axiosError.response.data?.detail)) {
			const validationErrors = axiosError.response.data.detail.map(
				(err) => `${err.loc?.[1] || 'Field'}: ${err.msg || err}`
			);
			return {
				success: false,
				message: 'Validation failed',
				errors: validationErrors
			};
		}

		// Handle 400 Bad Request errors
		if (axiosError.response?.status === 400) {
			const detail =
				typeof axiosError.response.data?.detail === 'string'
					? axiosError.response.data.detail
					: 'Bad request - invalid data';
			return {
				success: false,
				message: detail,
				errors: [detail]
			};
		}

		const errorMessage =
			axiosError.response?.data &&
			typeof axiosError.response.data === 'object' &&
			'message' in axiosError.response.data
				? String(axiosError.response.data.message)
				: 'Instrument submission failed';
		const errorDetail = error instanceof Error ? error.message : String(error);
		return {
			success: false,
			message: errorMessage,
			errors: [errorDetail]
		};
	}
}

/**
 * Get existing instruments
 */
export async function getInstruments(): Promise<InstrumentOption[]> {
	try {
		const response = await api.client.get(API_ENDPOINTS.instruments);
		return response.data;
	} catch (error) {
		console.error('Failed to load instruments:', error);
		return [];
	}
}

/**
 * Get instrument type options
 */
export async function getInstrumentTypeOptions(): Promise<EnumOption[]> {
	const response = await api.client.get('/api/v1/enums/instrument_type');
	return response.data.options.map(
		(option: { name: string; value: string; description?: string }) => ({
			name: option.name,
			value: option.value,
			description: option.description
		})
	);
}

/**
 * Get footprint type options
 */
export async function getFootprintTypeOptions(): Promise<EnumOption[]> {
	const response = await api.client.get('/api/v1/enums/footprint_type');
	return response.data.options.map(
		(option: { name: string; value: string; description?: string }) => ({
			name: option.name,
			value: option.value,
			description: option.description
		})
	);
}

/**
 * Get footprint unit options
 */
export async function getFootprintUnitOptions(): Promise<EnumOption[]> {
	const response = await api.client.get('/api/v1/enums/footprint_unit');
	return response.data.options.map(
		(option: { name: string; value: string; description?: string }) => ({
			name: option.name,
			value: option.value,
			description: option.description
		})
	);
}

/**
 * Preview footprint visualization
 */
export async function previewFootprint(
	instrumentData: Partial<InstrumentData>
): Promise<{ data: unknown; layout: unknown }> {
	try {
		const params = new URLSearchParams();

		// Set default coordinates for preview (centered at 0,0)
		params.append('ra', '0');
		params.append('dec', '0');
		params.append('shape', instrumentData.footprint_type || 'Circular');

		if (instrumentData.footprint_type === 'Rectangular') {
			if (instrumentData.height) params.append('height', instrumentData.height.toString());
			if (instrumentData.width) params.append('width', instrumentData.width.toString());
		} else if (instrumentData.footprint_type === 'Circular') {
			if (instrumentData.radius) params.append('radius', instrumentData.radius.toString());
		} else if (instrumentData.footprint_type === 'Polygon') {
			if (instrumentData.polygon) params.append('polygon', instrumentData.polygon);
		}

		const response = await api.client.get(`/ajax_preview_footprint?${params.toString()}`);
		return response.data;
	} catch (error) {
		console.error('Failed to preview footprint:', error);
		throw error;
	}
}

/**
 * Load all form options needed for submit instruments
 */
export async function loadFormOptions(): Promise<{
	instrumentTypes: EnumOption[];
	footprintTypes: EnumOption[];
	footprintUnits: EnumOption[];
	existingInstruments: InstrumentOption[];
}> {
	const [instrumentTypes, footprintTypes, footprintUnits, existingInstruments] = await Promise.all([
		getInstrumentTypeOptions(),
		getFootprintTypeOptions(),
		getFootprintUnitOptions(),
		getInstruments()
	]);

	return {
		instrumentTypes,
		footprintTypes,
		footprintUnits,
		existingInstruments
	};
}

/**
 * Validate instrument form data
 */
export function validateInstrumentData(
	data: Partial<InstrumentData>,
	existingInstruments: InstrumentOption[] = []
): { isValid: boolean; errors: string[] } {
	const errors: string[] = [];

	if (!data.instrument_name?.trim()) {
		errors.push('Instrument name is required');
	} else {
		// Check for duplicate instrument names (case-insensitive)
		const trimmedName = data.instrument_name.trim();
		const isDuplicate = existingInstruments.some(
			(instrument) => instrument.instrument_name.toLowerCase() === trimmedName.toLowerCase()
		);
		if (isDuplicate) {
			errors.push('An instrument with this name already exists. Please choose a different name.');
		}
	}

	if (!data.instrument_type) {
		errors.push('Instrument type is required');
	}

	if (!data.footprint_type) {
		errors.push('Footprint type is required');
	}

	if (!data.unit) {
		errors.push('Unit is required');
	}

	// Footprint-specific validation
	if (data.footprint_type === 'Rectangular') {
		if (!data.height || data.height <= 0) {
			errors.push('Height is required and must be positive for rectangular footprint');
		}
		if (!data.width || data.width <= 0) {
			errors.push('Width is required and must be positive for rectangular footprint');
		}
	} else if (data.footprint_type === 'Circular') {
		if (!data.radius || data.radius <= 0) {
			errors.push('Radius is required and must be positive for circular footprint');
		}
	} else if (data.footprint_type === 'Polygon') {
		if (!data.polygon?.trim()) {
			errors.push('Polygon coordinates are required for polygon footprint');
		}
	}

	return {
		isValid: errors.length === 0,
		errors
	};
}
