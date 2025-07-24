import axios, { type AxiosInstance, type AxiosResponse } from 'axios';
import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

// ========================================================================================
// TYPE DEFINITIONS - Based on GWTM FastAPI OpenAPI schema
// ========================================================================================

// Authentication and security
export interface ApiKeyAuth {
	api_token: string;
}

// Base response types
export interface ApiResponse<T> {
	data?: T;
	message?: string;
	errors?: any[];
	warnings?: any[];
}

// Health and status types
export interface HealthResponse {
	status: string;
	timestamp?: string;
}

export interface ServiceStatusResponse {
	database: 'connected' | 'disconnected';
	redis: 'connected' | 'disconnected';
	details?: Record<string, any>;
}

// Pointing related types
export interface PointingSchema {
	id?: number;
	position?: string;
	ra?: number;
	dec?: number;
	instrumentid?: number;
	depth?: number;
	depth_err?: number;
	depth_unit?: number | string;
	band?: number | string;
	pos_angle?: number;
	time?: string;
	status?: number | string;
	central_wave?: number;
	bandwidth?: number;
	submitterid?: number;
	datecreated?: string;
	dateupdated?: string;
	doi_url?: string;
	doi_id?: number;
}

export interface PointingCreate {
	position?: string;
	ra?: number;
	dec?: number;
	instrumentid?: number;
	depth?: number;
	depth_err?: number;
	depth_unit?: number | string;
	band?: number | string;
	pos_angle?: number;
	time?: string;
	status?: number | string;
	central_wave?: number;
	bandwidth?: number;
	id?: number; // For updating existing pointings
}

export interface PointingCreateRequest {
	graceid: string;
	pointing?: PointingCreate;
	pointings?: PointingCreate[];
	request_doi?: boolean;
	creators?: Record<string, string>[];
	doi_group_id?: number;
	doi_url?: string;
}

export interface PointingResponse {
	pointing_ids: number[];
	ERRORS?: any[];
	WARNINGS?: any[];
	DOI?: string;
}

export interface PointingUpdate {
	status: number | string;
	ids: number[];
}

export interface CancelAllRequest {
	graceid: string;
	instrumentid: number;
}

// GW Alert types
export interface GWAlertSchema {
	id?: number;
	datecreated?: string;
	graceid: string;
	alternateid?: string;
	role: string;
	timesent?: string;
	time_of_signal?: string;
	packet_type?: number;
	alert_type: string;
	detectors?: string;
	description?: string;
	far?: number;
	skymap_fits_url?: string;
	distance?: number;
	distance_error?: number;
	prob_bns?: number;
	prob_nsbh?: number;
	prob_gap?: number;
	prob_bbh?: number;
	prob_terrestrial?: number;
	prob_hasns?: number;
	prob_hasremenant?: number;
	group?: string;
	centralfreq?: number;
	duration?: number;
	avgra?: number;
	avgdec?: number;
	observing_run?: string;
	pipeline?: string;
	search?: string;
	area_50?: number;
	area_90?: number;
	gcn_notice_id?: number;
	ivorn?: string;
	ext_coinc_observatory?: string;
	ext_coinc_search?: string;
	time_coincidence_far?: number;
	time_sky_position_coincidence_far?: number;
	time_difference?: number;
}

export interface GWAlertQueryResponse {
	alerts: GWAlertSchema[];
	total: number;
	page: number;
	per_page: number;
	total_pages: number;
	has_next: boolean;
	has_prev: boolean;
}

export interface GWAlertFilterOptionsResponse {
	observing_runs: string[];
	roles: string[];
	alert_types: string[];
}

// Candidate types
export interface CandidateSchema {
	id: number;
	graceid: string;
	submitterid: number;
	candidate_name: string;
	datecreated?: string;
	tns_name?: string;
	tns_url?: string;
	position: string;
	discovery_date?: string;
	discovery_magnitude?: number;
	magnitude_central_wave?: number;
	magnitude_bandwidth?: number;
	magnitude_unit?: string;
	magnitude_bandpass?: string;
	associated_galaxy?: string;
	associated_galaxy_redshift?: number;
	associated_galaxy_distance?: number;
}

export interface CandidateRequest {
	candidate_name: string;
	position?: string;
	ra?: number;
	dec?: number;
	tns_name?: string;
	tns_url?: string;
	discovery_date: string;
	discovery_magnitude: number;
	magnitude_unit: number | string;
	magnitude_bandpass?: string;
	magnitude_central_wave?: number;
	magnitude_bandwidth?: number;
	wavelength_regime?: number[];
	wavelength_unit?: string;
	frequency_regime?: number[];
	frequency_unit?: string;
	energy_regime?: number[];
	energy_unit?: string;
	associated_galaxy?: string;
	associated_galaxy_redshift?: number;
	associated_galaxy_distance?: number;
}

export interface PostCandidateRequest {
	graceid: string;
	candidate?: CandidateRequest;
	candidates?: CandidateRequest[];
}

export interface CandidateResponse {
	candidate_ids: number[];
	ERRORS: any[][];
	WARNINGS: any[][];
}

export interface PutCandidateRequest {
	id: number;
	candidate: {
		graceid?: string;
		candidate_name?: string;
		tns_name?: string;
		tns_url?: string;
		position?: string;
		ra?: number;
		dec?: number;
		discovery_date?: string;
		discovery_magnitude?: number;
		magnitude_central_wave?: number;
		magnitude_bandwidth?: number;
		magnitude_unit?: string;
		magnitude_bandpass?: string;
		associated_galaxy?: string;
		associated_galaxy_redshift?: number;
		associated_galaxy_distance?: number;
		wavelength_regime?: number[];
		wavelength_unit?: string;
		frequency_regime?: number[];
		frequency_unit?: string;
		energy_regime?: number[];
		energy_unit?: string;
	};
}

export interface DeleteCandidateParams {
	id?: number;
	ids?: number[];
}

export interface DeleteCandidateResponse {
	message: string;
	deleted_ids?: number[];
	warnings?: string[];
}

// Instrument types
export interface InstrumentSchema {
	id: number;
	instrument_name: string;
	nickname?: string;
	instrument_type: number;
	datecreated?: string;
	submitterid?: number;
	num_pointings?: number; // Only included when reporting_only=true
}

export interface InstrumentCreate {
	instrument_name: string;
	nickname?: string;
	instrument_type: number;
}

export interface FootprintCCDSchema {
	id: number;
	instrumentid: number;
	footprint?: string;
}

export interface FootprintCCDCreate {
	instrumentid: number;
	footprint: string;
}

// Galaxy types
export interface GWGalaxyEntrySchema {
	id?: number;
	listid: number;
	name: string;
	score: number;
	position?: string;
	rank: number;
	info?: Record<string, any>;
}

export interface GalaxyEntryCreate {
	name: string;
	score: number;
	position?: string;
	ra?: number;
	dec?: number;
	rank: number;
	info?: Record<string, any>;
}

export interface PostEventGalaxiesRequest {
	graceid: string;
	timesent_stamp: string;
	groupname?: string;
	reference?: string;
	request_doi?: boolean;
	creators?: DOICreator[];
	doi_group_id?: number | string;
	galaxies: GalaxyEntryCreate[];
}

export interface PostEventGalaxiesResponse {
	message: string;
	errors: any[];
	warnings: any[];
}

// DOI types
export interface DOICreator {
	name: string;
	affiliation: string;
	orcid?: string;
	gnd?: string;
}

export interface DOIRequest {
	graceid?: string;
	id?: number;
	ids?: number[];
	doi_group_id?: string;
	creators?: Record<string, string>[];
	doi_url?: string;
}

export interface DOIRequestResponse {
	DOI_URL?: string;
	WARNINGS?: any[];
}

export interface DOIAuthorGroupSchema {
	name: string;
	userid?: number;
	id: number;
}

export interface DOIAuthorSchema {
	name: string;
	affiliation: string;
	orcid?: string;
	gnd?: string;
	pos_order?: number;
	id: number;
	author_groupid: number;
}

export interface DOIPointingInfo {
	id: number;
	graceid: string;
	instrument_name: string;
	status: string;
	doi_url?: string;
	doi_id?: number;
}

export interface DOIPointingsResponse {
	pointings: DOIPointingInfo[];
}

// IceCube types
export interface IceCubeNoticeCreateSchema {
	ref_id: string;
	graceid: string;
	alert_datetime?: string;
	observation_start?: string;
	observation_stop?: string;
	pval_generic?: number;
	pval_bayesian?: number;
	most_probable_direction_ra?: number;
	most_probable_direction_dec?: number;
	flux_sens_low?: number;
	flux_sens_high?: number;
	sens_energy_range_low?: number;
	sens_energy_range_high?: number;
}

export interface IceCubeNoticeCoincEventCreateSchema {
	event_dt?: number;
	ra?: number;
	dec?: number;
	containment_probability?: number;
	event_pval_generic?: number;
	event_pval_bayesian?: number;
	ra_uncertainty?: number;
	uncertainty_shape?: string;
}

export interface IceCubeNoticeRequestSchema {
	notice_data: IceCubeNoticeCreateSchema;
	events_data: IceCubeNoticeCoincEventCreateSchema[];
}

// Candidate Event types
export interface GWCandidateSchema {
	graceid: string;
	candidate_name: string;
	submitterid?: number;
	datecreated?: string;
	tns_name?: string;
	tns_url?: string;
	discovery_date?: string;
	discovery_magnitude?: number;
	magnitude_central_wave?: number;
	magnitude_bandwidth?: number;
	magnitude_unit?: string;
	magnitude_bandpass?: string;
	associated_galaxy?: string;
	associated_galaxy_redshift?: number;
	associated_galaxy_distance?: number;
	id?: number;
	ra?: number;
	dec?: number;
}

export interface GWCandidateCreate {
	graceid: string;
	candidate_name: string;
	submitterid?: number;
	datecreated?: string;
	tns_name?: string;
	tns_url?: string;
	discovery_date?: string;
	discovery_magnitude?: number;
	magnitude_central_wave?: number;
	magnitude_bandwidth?: number;
	magnitude_unit?: string;
	magnitude_bandpass?: string;
	associated_galaxy?: string;
	associated_galaxy_redshift?: number;
	associated_galaxy_distance?: number;
	ra?: number;
	dec?: number;
}

// Query filter types
export interface PointingFilters {
	graceid?: string;
	graceids?: string;
	id?: number;
	ids?: string;
	status?: string;
	statuses?: string;
	completed_after?: string;
	completed_before?: string;
	planned_after?: string;
	planned_before?: string;
	user?: string;
	users?: string;
	instrument?: string;
	instruments?: string;
	band?: string;
	bands?: string;
	wavelength_regime?: string;
	wavelength_unit?: string;
	frequency_regime?: string;
	frequency_unit?: string;
	energy_regime?: string;
	energy_unit?: string;
	depth_gt?: number;
	depth_lt?: number;
	depth_unit?: string;
}

export interface CandidateFilters {
	id?: number;
	graceid?: string;
	userid?: number;
	submitted_date_after?: string;
	submitted_date_before?: string;
	discovery_magnitude_gt?: number;
	discovery_magnitude_lt?: number;
	discovery_date_after?: string;
	discovery_date_before?: string;
	associated_galaxy_name?: string;
	associated_galaxy_redshift_gt?: number;
	associated_galaxy_redshift_lt?: number;
	associated_galaxy_distance_gt?: number;
	associated_galaxy_distance_lt?: number;
}

export interface InstrumentFilters {
	id?: number;
	ids?: string;
	name?: string;
	names?: string;
	type?: number;
	reporting_only?: boolean;
}

export interface GalaxyFilters {
	graceid: string;
	timesent_stamp?: string;
	listid?: number;
	groupname?: string;
	score_gt?: number;
	score_lt?: number;
}

export interface GladeFilters {
	ra?: number;
	dec?: number;
	name?: string;
}

// ========================================================================================
// API SERVICE CLASS
// ========================================================================================

class GWTMApiService {
	private client: AxiosInstance;
	private baseURL: string;

	constructor() {
		// Determine base URL based on environment
		// For browser (client-side), always use localhost or external URL
		// The PUBLIC_API_BASE_URL should be set to the externally accessible URL
		const defaultUrl = 'http://localhost:8000';
		this.baseURL = env.PUBLIC_API_BASE_URL || defaultUrl;

		this.client = axios.create({
			baseURL: this.baseURL,
			timeout: 30000,
			headers: {
				'Content-Type': 'application/json'
			}
		});

		this.setupInterceptors();
	}

	private setupInterceptors(): void {
		// Request interceptor - add API token (unless explicitly disabled)
		this.client.interceptors.request.use(
			(config) => {
				// Skip auth if explicitly disabled via custom header
				if (!config.headers['skip-auth']) {
					const token = browser ? localStorage.getItem('api_token') : null;
					if (token) {
						config.headers['api_token'] = token;
					}
				}

				// Remove the skip-auth header before sending request
				delete config.headers['skip-auth'];

				// Log requests in development
				if (browser && import.meta.env.DEV) {
					console.log(`GWTM API Request: ${config.method?.toUpperCase()} ${config.url}`, {
						params: config.params,
						data: config.data
					});
				}

				return config;
			},
			(error) => {
				console.error('Request error:', error);
				return Promise.reject(error);
			}
		);

		// Response interceptor
		this.client.interceptors.response.use(
			(response) => {
				if (browser && import.meta.env.DEV) {
					console.log(
						`GWTM API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`,
						response.data
					);
				}
				return response;
			},
			(error) => {
				console.error('GWTM API Error:', error);
				if (error.response?.status === 401) {
					if (browser) {
						localStorage.removeItem('api_token');
						// Redirect to login or show auth error
					}
				}
				return Promise.reject(error);
			}
		);
	}

	// ========================================================================================
	// GENERIC HTTP METHODS
	// ========================================================================================

	private async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
		const response: AxiosResponse<T> = await this.client.get(endpoint, { params });
		return response.data;
	}

	private async post<T, U>(endpoint: string, data?: U): Promise<T> {
		const response: AxiosResponse<T> = await this.client.post(endpoint, data);
		return response.data;
	}

	private async put<T, U>(endpoint: string, data: U): Promise<T> {
		const response: AxiosResponse<T> = await this.client.put(endpoint, data);
		return response.data;
	}

	private async delete<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
		const response: AxiosResponse<T> = await this.client.delete(endpoint, { params });
		return response.data;
	}

	// Public GET method that skips authentication
	private async getPublic<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
		const response: AxiosResponse<T> = await this.client.get(endpoint, {
			params,
			headers: { 'skip-auth': 'true' }
		});
		return response.data;
	}

	// ========================================================================================
	// HEALTH AND STATUS ENDPOINTS
	// ========================================================================================

	async health(): Promise<HealthResponse> {
		return this.get<HealthResponse>('/health');
	}

	async serviceStatus(): Promise<ServiceStatusResponse> {
		return this.get<ServiceStatusResponse>('/service-status');
	}

	// ========================================================================================
	// POINTING ENDPOINTS
	// ========================================================================================

	async getPointings(filters?: PointingFilters): Promise<PointingSchema[]> {
		return this.get<PointingSchema[]>('/api/v1/pointings', filters);
	}

	async addPointings(request: PointingCreateRequest): Promise<PointingResponse> {
		return this.post<PointingResponse, PointingCreateRequest>('/api/v1/pointings', request);
	}

	async updatePointings(update: PointingUpdate): Promise<{ message: string }> {
		return this.post<{ message: string }, PointingUpdate>('/api/v1/update_pointings', update);
	}

	async cancelAllPointings(request: CancelAllRequest): Promise<{ message: string }> {
		return this.post<{ message: string }, CancelAllRequest>('/api/v1/cancel_all', request);
	}

	async requestDOI(request: DOIRequest): Promise<DOIRequestResponse> {
		return this.post<DOIRequestResponse, DOIRequest>('/api/v1/request_doi', request);
	}

	async testRefactoring(): Promise<{ message: string }> {
		return this.get<{ message: string }>('/api/v1/test_refactoring');
	}

	// ========================================================================================
	// GW ALERT ENDPOINTS
	// ========================================================================================

	async queryAlerts(params?: Record<string, any>): Promise<GWAlertQueryResponse> {
		// Always use paginated format for frontend
		const paginatedParams = { ...params, format: 'paginated' };
		return this.getPublic<GWAlertQueryResponse>('/api/v1/query_alerts', paginatedParams);
	}

	async getInstrumentEventsContributed(instrumentId: number): Promise<GWAlertSchema[]> {
		// Get events with completed pointings from this instrument, including pointing counts
		const params = {
			instrument_id: instrumentId,
			include_pointing_count: true,
			format: 'simple' // Return as simple list
		};
		return this.getPublic<GWAlertSchema[]>('/api/v1/query_alerts', params);
	}

	async getAlertFilterOptions(): Promise<GWAlertFilterOptionsResponse> {
		return this.getPublic<GWAlertFilterOptionsResponse>('/api/v1/alert_filter_options');
	}

	async postAlert(alert: GWAlertSchema): Promise<GWAlertSchema> {
		return this.post<GWAlertSchema, GWAlertSchema>('/api/v1/post_alert', alert);
	}

	async getGWSkymap(graceid: string): Promise<Blob> {
		const response = await this.client.get(`/api/v1/gw_skymap`, {
			params: { graceid },
			responseType: 'blob'
		});
		return response.data;
	}

	async getGWContour(graceid: string): Promise<any> {
		return this.get<any>('/api/v1/gw_contour', { graceid });
	}

	async getGRBMOCFile(graceid: string, instrument: string): Promise<any> {
		return this.getPublic<any>('/api/v1/grb_moc_file', { graceid, instrument });
	}

	async deleteTestAlerts(): Promise<{ message: string }> {
		return this.post<{ message: string }, {}>('/api/v1/del_test_alerts', {});
	}

	// ========================================================================================
	// CANDIDATE ENDPOINTS
	// ========================================================================================

	async getCandidates(filters?: CandidateFilters, ids?: number[]): Promise<CandidateSchema[]> {
		return this.get<CandidateSchema[]>('/api/v1/candidate', {
			...filters,
			...(ids && { body: JSON.stringify(ids) })
		});
	}

	async postCandidates(request: PostCandidateRequest): Promise<CandidateResponse> {
		return this.post<CandidateResponse, PostCandidateRequest>('/api/v1/candidate', request);
	}

	async updateCandidate(request: PutCandidateRequest): Promise<PutCandidateRequest> {
		return this.put<PutCandidateRequest, PutCandidateRequest>('/api/v1/candidate', request);
	}

	async deleteCandidates(params: DeleteCandidateParams): Promise<DeleteCandidateResponse> {
		return this.delete<DeleteCandidateResponse>('/api/v1/candidate', params);
	}

	// ========================================================================================
	// INSTRUMENT ENDPOINTS
	// ========================================================================================

	async getInstruments(filters?: InstrumentFilters): Promise<InstrumentSchema[]> {
		return this.get<InstrumentSchema[]>('/api/v1/instruments', filters);
	}

	async getReportingInstruments(): Promise<InstrumentSchema[]> {
		return this.get<InstrumentSchema[]>('/api/v1/instruments', { reporting_only: true });
	}

	async createInstrument(instrument: InstrumentCreate): Promise<InstrumentSchema> {
		return this.post<InstrumentSchema, InstrumentCreate>('/api/v1/instruments', instrument);
	}

	async getFootprints(id?: number, name?: string): Promise<FootprintCCDSchema[]> {
		return this.get<FootprintCCDSchema[]>('/api/v1/footprints', { id, name });
	}

	async createFootprint(footprint: FootprintCCDCreate): Promise<FootprintCCDSchema> {
		return this.post<FootprintCCDSchema, FootprintCCDCreate>('/api/v1/footprints', footprint);
	}

	// ========================================================================================
	// GALAXY ENDPOINTS
	// ========================================================================================

	async getEventGalaxies(filters: GalaxyFilters): Promise<GWGalaxyEntrySchema[]> {
		return this.get<GWGalaxyEntrySchema[]>('/api/v1/event_galaxies', filters);
	}

	async postEventGalaxies(request: PostEventGalaxiesRequest): Promise<PostEventGalaxiesResponse> {
		return this.post<PostEventGalaxiesResponse, PostEventGalaxiesRequest>(
			'/api/v1/event_galaxies',
			request
		);
	}

	async removeEventGalaxies(listid: number): Promise<{ message: string }> {
		return this.delete<{ message: string }>('/api/v1/remove_event_galaxies', { listid });
	}

	async getGladeGalaxies(filters?: GladeFilters): Promise<any> {
		return this.get<any>('/api/v1/glade', filters);
	}

	// ========================================================================================
	// ICECUBE ENDPOINTS
	// ========================================================================================

	async postIceCubeNotice(request: IceCubeNoticeRequestSchema): Promise<Record<string, any>> {
		return this.post<Record<string, any>, IceCubeNoticeRequestSchema>(
			'/api/v1/post_icecube_notice',
			request
		);
	}

	// ========================================================================================
	// DOI ENDPOINTS
	// ========================================================================================

	async getDOIPointings(): Promise<DOIPointingsResponse> {
		return this.get<DOIPointingsResponse>('/api/v1/doi_pointings');
	}

	async getDOIAuthorGroups(): Promise<DOIAuthorGroupSchema[]> {
		return this.get<DOIAuthorGroupSchema[]>('/api/v1/doi_author_groups');
	}

	async getDOIAuthors(groupId: number): Promise<DOIAuthorSchema[]> {
		return this.get<DOIAuthorSchema[]>(`/api/v1/doi_authors/${groupId}`);
	}

	// ========================================================================================
	// CANDIDATE EVENT ENDPOINTS
	// ========================================================================================

	async getCandidateEvents(id?: number, user_id?: number): Promise<GWCandidateSchema[]> {
		return this.get<GWCandidateSchema[]>('/api/v1/candidate/event', { id, user_id });
	}

	async createCandidateEvent(candidate: GWCandidateCreate): Promise<any> {
		return this.post<any, GWCandidateCreate>('/api/v1/candidate/event', candidate);
	}

	async updateCandidateEvent(candidateId: number, candidate: GWCandidateSchema): Promise<any> {
		return this.put<any, GWCandidateSchema>(`/api/v1/candidate/event/${candidateId}`, candidate);
	}

	async deleteCandidateEvent(candidateId: number): Promise<any> {
		return this.delete<any>(`/api/v1/candidate/event/${candidateId}`);
	}

	// ========================================================================================
	// ADMIN ENDPOINTS
	// ========================================================================================

	async fixData(): Promise<{ message: string }> {
		return this.get<{ message: string }>('/fixdata');
	}

	async fixDataPost(): Promise<{ message: string }> {
		return this.post<{ message: string }, {}>('/fixdata', {});
	}

	// ========================================================================================
	// UI/AJAX ENDPOINTS (for backwards compatibility with existing UI)
	// ========================================================================================

	async getAlertInstrumentsFootprints(
		graceid?: string,
		pointing_status?: string,
		tos_mjd?: number
	): Promise<any> {
		return this.get<any>('/ajax_alertinstruments_footprints', {
			graceid,
			pointing_status,
			tos_mjd
		});
	}

	async previewFootprint(
		ra: number,
		dec: number,
		radius?: number,
		height?: number,
		width?: number,
		shape?: string,
		polygon?: string
	): Promise<any> {
		return this.get<any>('/ajax_preview_footprint', {
			ra,
			dec,
			radius,
			height,
			width,
			shape,
			polygon
		});
	}

	async resendVerificationEmail(email?: string): Promise<any> {
		return this.post<any, {}>('/ajax_resend_verification_email', {}, { params: { email } });
	}

	async coverageCalculator(params: {
		graceid: string;
		mappathinfo?: string;
		inst_cov?: string;
		band_cov?: string;
		depth_cov?: number;
		depth_unit?: string;
		approx_cov?: number;
		spec_range_type?: string;
		spec_range_unit?: string;
	}): Promise<any> {
		return this.post<any, typeof params>('/ajax_coverage_calculator', params);
	}

	async spectralRangeFromSelectedBands(
		band_cov: string,
		spectral_type: string,
		spectral_unit: string
	): Promise<any> {
		return this.get<any>('/ajax_update_spectral_range_from_selected_bands', {
			band_cov,
			spectral_type,
			spectral_unit
		});
	}

	async getPointingFromId(id: string): Promise<any> {
		return this.get<any>('/ajax_pointingfromid', { id });
	}

	async gradeCalculator(): Promise<any> {
		return this.post<any, {}>('/ajax_grade_calculator', {});
	}

	async getIceCubeNotice(graceid: string): Promise<any> {
		return this.get<any>('/ajax_icecube_notice', { graceid });
	}

	async getEventGalaxiesAjax(alertid: string): Promise<any> {
		return this.get<any>('/ajax_event_galaxies', { alertid });
	}

	async getScimmaXRT(graceid: string): Promise<any> {
		return this.get<any>('/ajax_scimma_xrt', { graceid });
	}

	async getCandidateAjax(graceid: string): Promise<any> {
		return this.get<any>('/ajax_candidate', { graceid });
	}

	async requestDOIAjax(
		graceid: string,
		ids?: string,
		doi_group_id?: string,
		doi_url?: string
	): Promise<any> {
		return this.get<any>('/ajax_request_doi', { graceid, ids, doi_group_id, doi_url });
	}

	async getEventContour(urlid: string): Promise<any> {
		return this.get<any>('/ajax_alerttype', { urlid });
	}

	async getAlertDetectionOverlays(alertId: number, alertType: string): Promise<any> {
		const urlid = `${alertId}_${alertType}`;
		return this.get<any>('/ajax_alerttype', { urlid });
	}

	// ========================================================================================
	// AUTHENTICATION METHODS
	// ========================================================================================

	async login(email: string, password: string): Promise<any> {
		const response = await this.client.post('/api/v1/login', {
			email,
			password
		});
		return response;
	}

	async register(userData: {
		email: string;
		password: string;
		username: string;
		first_name?: string;
		last_name?: string;
	}): Promise<any> {
		const response = await this.client.post('/api/v1/register', userData);
		return response;
	}

	// ========================================================================================
	// UTILITY METHODS
	// ========================================================================================

	setApiToken(token: string): void {
		if (browser) {
			localStorage.setItem('api_token', token);
		}
	}

	getApiToken(): string | null {
		return browser ? localStorage.getItem('api_token') : null;
	}

	clearApiToken(): void {
		if (browser) {
			localStorage.removeItem('api_token');
		}
	}

	isAuthenticated(): boolean {
		return !!this.getApiToken();
	}
}

// ========================================================================================
// EXPORT SINGLETON INSTANCE
// ========================================================================================

export const gwtmApi = new GWTMApiService();

// Also export the class for testing purposes
export { GWTMApiService };

// Export all types for use in components
export type {
	PointingSchema,
	PointingCreate,
	PointingCreateRequest,
	PointingResponse,
	PointingFilters,
	GWAlertSchema,
	GWAlertQueryResponse,
	GWAlertFilterOptionsResponse,
	CandidateSchema,
	CandidateRequest,
	PostCandidateRequest,
	CandidateResponse,
	CandidateFilters,
	InstrumentSchema,
	InstrumentCreate,
	InstrumentFilters,
	FootprintCCDSchema,
	FootprintCCDCreate,
	GWGalaxyEntrySchema,
	GalaxyEntryCreate,
	PostEventGalaxiesRequest,
	PostEventGalaxiesResponse,
	DOIRequest,
	DOIRequestResponse,
	DOIAuthorGroupSchema,
	DOIAuthorSchema,
	IceCubeNoticeRequestSchema,
	GWCandidateSchema,
	GWCandidateCreate,
	HealthResponse,
	ServiceStatusResponse
};
