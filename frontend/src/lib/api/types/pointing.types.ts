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
