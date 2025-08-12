/**
 * @fileoverview Type definitions for API responses
 * @description Centralized type definitions for all API response structures
 * @category Types
 * @version 1.0.0
 * @author GWTM Team
 * @since 2025-01-11
 */

// Plotly data structures
export interface PlotlyData {
	x: number[];
	y: number[];
	mode?: string;
	type?: string;
	name?: string;
	line?: {
		color: string;
		width?: number;
	};
	fill?: string;
	fillcolor?: string;
	marker?: {
		color: string;
		size?: number;
	};
}

export interface PlotlyLayout {
	title?: string;
	xaxis?: {
		title?: string;
		type?: string;
		range?: number[];
	};
	yaxis?: {
		title?: string;
		type?: string;
		range?: number[];
		matches?: string;
		scaleanchor?: string;
		scaleratio?: number;
		constrain?: string;
	};
	showlegend?: boolean;
	width?: number;
	height?: number;
	margin?: {
		l?: number;
		r?: number;
		t?: number;
		b?: number;
	};
}

export interface PlotlyFigure {
	data: PlotlyData[];
	layout: PlotlyLayout;
}

// Geographic/Footprint data
export interface FootprintData {
	id: number;
	instrumentid: number;
	ra: number;
	dec: number;
	footprint: string; // WKT or GeoJSON string
	pos_angle?: number;
	status: string;
	band: string;
	depth?: number;
	depth_unit?: string;
	time?: string;
}

export interface AlertInstrumentFootprint {
	graceid: string;
	alertid: number;
	instrument_name: string;
	instrument_type: string;
	footprints: FootprintData[];
	coverage_area?: number;
	total_pointings?: number;
}

// Coverage calculator types
export interface CoverageCalculatorParams {
	graceid: string;
	mappathinfo?: string;
	inst_cov?: string;
	band_cov?: string;
	depth_cov?: number;
	depth_unit?: string;
	approx_cov?: number;
	spec_range_type?: string;
	spec_range_unit?: string;
}

export interface CoverageCalculatorResult {
	coverage_percentage: number;
	total_area: number;
	covered_area: number;
	plot_data?: PlotlyFigure;
	summary: string;
}

// Spectral range types
export interface SpectralRangeResult {
	min_wavelength: number;
	max_wavelength: number;
	effective_wavelength: number;
	unit: string;
	bands: string[];
}

// Pointing data types
export interface PointingFromIdResult {
	id: number;
	graceid: string;
	instrumentid: number;
	instrument_name: string;
	ra: number;
	dec: number;
	pos_angle?: number;
	status: string;
	band: string;
	depth?: number;
	depth_err?: number;
	depth_unit?: string;
	time?: string;
	completed_obs_time?: string;
	planned_obs_time?: string;
}

// IceCube notice types
export interface IceCubeNotice {
	notice_id: string;
	notice_type: string;
	detection_time: string;
	ra: number;
	dec: number;
	error_radius: number;
	signalness: number;
	far: number;
	energy: number;
	has_followup: boolean;
	alert_sent: boolean;
}

// Event galaxies types
export interface EventGalaxy {
	id: number;
	name: string;
	ra: number;
	dec: number;
	distance: number;
	distance_error?: number;
	magnitude: number;
	magnitude_band: string;
	probability: number;
	rank: number;
}

export interface EventGalaxiesResult {
	galaxies: EventGalaxy[];
	total_count: number;
	parameters: {
		distance_limit: number;
		magnitude_limit: number;
		probability_threshold: number;
	};
}

// SCIMMA XRT types
export interface ScimmaXRTSource {
	name: string;
	ra: number;
	dec: number;
	error_radius: number;
	flux: number;
	flux_error?: number;
	significance: number;
	detection_time: string;
}

export interface ScimmaXRTResult {
	sources: ScimmaXRTSource[];
	observation_id: string;
	observation_time: string;
	exposure_time: number;
	total_sources: number;
}

// Candidate types
export interface Candidate {
	id: number;
	name: string;
	ra: number;
	dec: number;
	discovery_date: string;
	magnitude: number;
	magnitude_band: string;
	classification?: string;
	redshift?: number;
	host_galaxy?: string;
	notes?: string;
}

export interface CandidateResult {
	candidates: Candidate[];
	total_count: number;
	graceid: string;
}

// DOI request types
export interface DOIRequestParams {
	graceid: string;
	ids?: string;
	doi_group_id?: string;
	doi_url?: string;
}

export interface DOIRequestResult {
	success: boolean;
	doi_url?: string;
	message: string;
	errors?: string[];
}

// Alert contour types
export interface AlertContour {
	contour_data: number[][];
	contour_levels: number[];
	probability_map?: number[][];
	center_ra: number;
	center_dec: number;
	search_radius: number;
}

// Detection overlay types
export interface DetectionOverlay {
	type: 'point' | 'region' | 'contour';
	ra: number;
	dec: number;
	radius?: number;
	shape?: string;
	data?: number[][];
	metadata: {
		detection_time: string;
		significance: number;
		instrument: string;
	};
}

export interface AlertDetectionOverlaysResult {
	overlays: DetectionOverlay[];
	alert_id: number;
	alert_type: string;
	total_detections: number;
}

// Email verification types
export interface EmailVerificationResult {
	success: boolean;
	message: string;
	email: string;
}

// Generic API response wrapper
export interface ApiResponse<T = unknown> {
	success: boolean;
	data?: T;
	message?: string;
	errors?: string[];
	warnings?: string[];
}

// Grade calculator (might need adjustment based on actual response)
export interface GradeCalculatorResult {
	grade: string;
	score: number;
	criteria: {
		completeness: number;
		timeliness: number;
		accuracy: number;
	};
	recommendations: string[];
}

// Authentication types
export interface LoginResponse {
	access_token: string;
	token_type: string;
	expires_in: number;
	user: UserProfile;
}

export interface UserProfile {
	id: number;
	username: string;
	email: string;
	first_name?: string;
	last_name?: string;
	is_active: boolean;
	created_at: string;
	last_login?: string;
}

export interface RegisterResponse {
	success: boolean;
	message: string;
	user?: UserProfile;
}

export interface UserResponse {
	user: UserProfile;
}

// Candidate event types
export interface CandidateEventResponse {
	id: number;
	success: boolean;
	message: string;
	candidate?: {
		id: number;
		name: string;
		ra: number;
		dec: number;
		discovery_date: string;
		magnitude?: number;
		classification?: string;
	};
}

// GW contour types
export interface GWContourResponse {
	contour_data: Array<{
		ra: number[];
		dec: number[];
		probability_level: number;
	}>;
	metadata: {
		graceid: string;
		total_probability: number;
		generation_time: string;
		coordinate_system: string;
	};
}

// GRB MOC file response
export interface GRBMOCResponse {
	moc_data: string; // MOC format data
	metadata: {
		graceid: string;
		instrument: string;
		coverage_area: number;
		generation_time: string;
		format: 'fits' | 'json' | 'ascii';
	};
}

// GLADE galaxy data
export interface GLADEGalaxyEntry {
	id: number;
	name: string;
	ra: number;
	dec: number;
	distance: number;
	distance_error?: number;
	luminosity?: number;
	magnitude_B?: number;
	magnitude_K?: number;
	stellar_mass?: number;
	galaxy_type?: string;
	redshift?: number;
}

export interface GLADEGalaxiesResponse {
	galaxies: GLADEGalaxyEntry[];
	total_count: number;
	query_parameters: {
		ra_range?: [number, number];
		dec_range?: [number, number];
		distance_range?: [number, number];
		magnitude_limit?: number;
	};
}

// Search service types
export interface DOIAuthorGroup {
	id: number;
	name: string;
	description?: string;
	contact_email?: string;
}

export interface PointingSearchFilters {
	graceid?: string;
	bands?: string;
	statuses?: string;
	my_points_only?: boolean;
	[key: string]: unknown;
}

// IceCube notice response
export interface IceCubeNoticeResponse {
	success: boolean;
	notice_id?: string;
	message: string;
	notice_created?: boolean;
	alert_triggered?: boolean;
}
