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
