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

export interface InstrumentFilters {
	id?: number;
	ids?: string;
	name?: string;
	names?: string;
	type?: number;
	reporting_only?: boolean;
}
