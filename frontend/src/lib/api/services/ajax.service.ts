import client from '../client';

export const ajaxService = {
    getAlertInstrumentsFootprints: async (
        graceid?: string,
        pointing_status?: string,
        tos_mjd?: number
    ): Promise<any> => {
        const response = await client.get<any>('/ajax_alertinstruments_footprints', {
            params: {
                graceid,
                pointing_status,
                tos_mjd
            }
        });
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
    ): Promise<any> => {
        const response = await client.get<any>('/ajax_preview_footprint', {
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

    resendVerificationEmail: async (email?: string): Promise<any> => {
        const response = await client.post<any>('/ajax_resend_verification_email', { email });
        return response.data;
    },

    coverageCalculator: async (params: {
        graceid: string;
        mappathinfo?: string;
        inst_cov?: string;
        band_cov?: string;
        depth_cov?: number;
        depth_unit?: string;
        approx_cov?: number;
        spec_range_type?: string;
        spec_range_unit?: string;
    }): Promise<any> => {
        const response = await client.post<any>('/ajax_coverage_calculator', params);
        return response.data;
    },

    spectralRangeFromSelectedBands: async (
        band_cov: string,
        spectral_type: string,
        spectral_unit: string
    ): Promise<any> => {
        const response = await client.get<any>('/ajax_update_spectral_range_from_selected_bands', {
            params: {
                band_cov,
                spectral_type,
                spectral_unit
            }
        });
        return response.data;
    },

    getPointingFromId: async (id: string): Promise<any> => {
        const response = await client.get<any>('/ajax_pointingfromid', { params: { id } });
        return response.data;
    },

    gradeCalculator: async (): Promise<any> => {
        const response = await client.post<any>('/ajax_grade_calculator', {});
        return response.data;
    },

    getIceCubeNotice: async (graceid: string): Promise<any> => {
        const response = await client.get<any>('/ajax_icecube_notice', { params: { graceid } });
        return response.data;
    },

    getEventGalaxiesAjax: async (alertid: string): Promise<any> => {
        const response = await client.get<any>('/ajax_event_galaxies', { params: { alertid } });
        return response.data;
    },

    getScimmaXRT: async (graceid: string): Promise<any> => {
        const response = await client.get<any>('/ajax_scimma_xrt', { params: { graceid } });
        return response.data;
    },

    getCandidateAjax: async (graceid: string): Promise<any> => {
        const response = await client.get<any>('/ajax_candidate', { params: { graceid } });
        return response.data;
    },

    requestDOIAjax: async (
        graceid: string,
        ids?: string,
        doi_group_id?: string,
        doi_url?: string
    ): Promise<any> => {
        const response = await client.get<any>('/ajax_request_doi', { params: { graceid, ids, doi_group_id, doi_url } });
        return response.data;
    },

    getEventContour: async (urlid: string): Promise<any> => {
        const response = await client.get<any>('/ajax_alerttype', { params: { urlid } });
        return response.data;
    },

    getAlertDetectionOverlays: async (alertId: number, alertType: string): Promise<any> => {
        const urlid = `${alertId}_${alertType}`;
        const response = await client.get<any>('/ajax_alerttype', { params: { urlid } });
        return response.data;
    }
};
