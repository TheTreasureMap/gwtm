import client from '../client';
import type {
	GWAlertSchema,
	GWAlertQueryResponse,
	GWAlertFilterOptionsResponse
} from '../types/alert.types';

export const alertService = {
	queryAlerts: async (params?: Record<string, any>): Promise<GWAlertQueryResponse> => {
		// Always use paginated format for frontend
		const paginatedParams = { ...params, format: 'paginated' };
		const response = await client.get<GWAlertQueryResponse>('/api/v1/query_alerts', {
			params: paginatedParams,
			headers: { 'skip-auth': 'true' }
		});
		return response.data;
	},

	getInstrumentEventsContributed: async (instrumentId: number): Promise<GWAlertSchema[]> => {
		// Get events with completed pointings from this instrument, including pointing counts
		const params = {
			instrument_id: instrumentId,
			include_pointing_count: true,
			format: 'simple' // Return as simple list
		};
		const response = await client.get<GWAlertSchema[]>('/api/v1/query_alerts', {
			params,
			headers: { 'skip-auth': 'true' }
		});
		return response.data;
	},

	getAlertFilterOptions: async (): Promise<GWAlertFilterOptionsResponse> => {
		const response = await client.get<GWAlertFilterOptionsResponse>(
			'/api/v1/alert_filter_options',
			{ headers: { 'skip-auth': 'true' } }
		);
		return response.data;
	},

	postAlert: async (alert: GWAlertSchema): Promise<GWAlertSchema> => {
		const response = await client.post<GWAlertSchema>('/api/v1/post_alert', alert);
		return response.data;
	},

	getGWSkymap: async (graceid: string): Promise<Blob> => {
		const response = await client.get<Blob>(`/api/v1/gw_skymap`, {
			params: { graceid },
			responseType: 'blob'
		});
		return response.data;
	},

	getGWContour: async (graceid: string): Promise<any> => {
		const response = await client.get<any>('/api/v1/gw_contour', { params: { graceid } });
		return response.data;
	},

	getGRBMOCFile: async (graceid: string, instrument: string): Promise<any> => {
		const response = await client.get<any>('/api/v1/grb_moc_file', {
			params: { graceid, instrument },
			headers: { 'skip-auth': 'true' }
		});
		return response.data;
	},

	deleteTestAlerts: async (): Promise<{ message: string }> => {
		const response = await client.post<{ message: string }>('/api/v1/del_test_alerts', {});
		return response.data;
	}
};
