import client from '../client';
import type {
	AlertInstrumentFootprint,
	PlotlyFigure,
	EmailVerificationResult,
	CoverageCalculatorParams,
	CoverageCalculatorResult,
	SpectralRangeResult,
	PointingFromIdResult,
	GradeCalculatorResult,
	IceCubeNotice,
	EventGalaxiesResult,
	ScimmaXRTResult,
	CandidateResult,
	DOIRequestResult,
	AlertContour,
	AlertDetectionOverlaysResult
} from '../types/api-responses';

export const ajaxService = {
	getAlertInstrumentsFootprints: async (
		graceid?: string,
		pointing_status?: string,
		tos_mjd?: number
	): Promise<AlertInstrumentFootprint[]> => {
		const response = await client.get<AlertInstrumentFootprint[]>(
			'/ajax_alertinstruments_footprints',
			{
				params: {
					graceid,
					pointing_status,
					tos_mjd
				}
			}
		);
		return response.data;
	},

	previewFootprint: async (
		ra: number,
		dec: number,
		radius?: number,
		height?: number,
		width?: number,
		shape?: string,
		polygon?: string
	): Promise<PlotlyFigure> => {
		const response = await client.get<PlotlyFigure>('/ajax_preview_footprint', {
			params: {
				ra,
				dec,
				radius,
				height,
				width,
				shape,
				polygon
			}
		});
		return response.data;
	},

	resendVerificationEmail: async (email?: string): Promise<EmailVerificationResult> => {
		const response = await client.post<EmailVerificationResult>('/ajax_resend_verification_email', {
			email
		});
		return response.data;
	},

	coverageCalculator: async (
		params: CoverageCalculatorParams
	): Promise<CoverageCalculatorResult> => {
		const response = await client.post<CoverageCalculatorResult>(
			'/ajax_coverage_calculator',
			params
		);
		return response.data;
	},

	spectralRangeFromSelectedBands: async (
		band_cov: string,
		spectral_type: string,
		spectral_unit: string
	): Promise<SpectralRangeResult> => {
		const response = await client.get<SpectralRangeResult>(
			'/ajax_update_spectral_range_from_selected_bands',
			{
				params: {
					band_cov,
					spectral_type,
					spectral_unit
				}
			}
		);
		return response.data;
	},

	getPointingFromId: async (id: string): Promise<PointingFromIdResult> => {
		const response = await client.get<PointingFromIdResult>('/ajax_pointingfromid', {
			params: { id }
		});
		return response.data;
	},

	gradeCalculator: async (): Promise<GradeCalculatorResult> => {
		const response = await client.post<GradeCalculatorResult>('/ajax_grade_calculator', {});
		return response.data;
	},

	getIceCubeNotice: async (graceid: string): Promise<IceCubeNotice> => {
		const response = await client.get<IceCubeNotice>('/ajax_icecube_notice', {
			params: { graceid }
		});
		return response.data;
	},

	getEventGalaxiesAjax: async (alertid: string): Promise<EventGalaxiesResult> => {
		const response = await client.get<EventGalaxiesResult>('/ajax_event_galaxies', {
			params: { alertid }
		});
		return response.data;
	},

	getScimmaXRT: async (graceid: string): Promise<ScimmaXRTResult> => {
		const response = await client.get<ScimmaXRTResult>('/ajax_scimma_xrt', { params: { graceid } });
		return response.data;
	},

	getCandidateAjax: async (graceid: string): Promise<CandidateResult> => {
		const response = await client.get<CandidateResult>('/ajax_candidate', { params: { graceid } });
		return response.data;
	},

	requestDOIAjax: async (
		graceid: string,
		ids?: string,
		doi_group_id?: string,
		doi_url?: string
	): Promise<DOIRequestResult> => {
		const response = await client.get<DOIRequestResult>('/ajax_request_doi', {
			params: { graceid, ids, doi_group_id, doi_url }
		});
		return response.data;
	},

	getEventContour: async (urlid: string): Promise<AlertContour> => {
		const response = await client.get<AlertContour>('/ajax_alerttype', { params: { urlid } });
		return response.data;
	},

	getAlertDetectionOverlays: async (
		alertId: number,
		alertType: string
	): Promise<AlertDetectionOverlaysResult> => {
		const urlid = `${alertId}_${alertType}`;
		const response = await client.get<AlertDetectionOverlaysResult>('/ajax_alerttype', {
			params: { urlid }
		});
		return response.data;
	}
};
