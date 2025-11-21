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
	// Computed fields for display (calculated from far)
	human_far?: number;
	human_far_unit?: string;
	// Additional pointing count field
	pointing_count?: number;
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
