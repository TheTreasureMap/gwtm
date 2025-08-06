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
