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
