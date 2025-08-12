import type { DOICreator } from './doi.types';

export interface GWGalaxyEntrySchema {
	id?: number;
	listid: number;
	name: string;
	score: number;
	position?: string;
	rank: number;
	info?: Record<string, unknown>;
}

export interface GalaxyEntryCreate {
	name: string;
	score: number;
	position?: string;
	ra?: number;
	dec?: number;
	rank: number;
	info?: Record<string, unknown>;
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
	errors: string[];
	warnings: string[];
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
