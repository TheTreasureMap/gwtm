import client from '../client';
import type {
	GWAlertSchema,
	GWAlertQueryResponse,
	GWAlertFilterOptionsResponse
} from '../types/alert.types';
import type { GWContourResponse, GWContourGeoJSON, GRBMOCResponse } from '../types/api-responses';

export const alertService = {
	queryAlerts: async (params?: Record<string, unknown>): Promise<GWAlertQueryResponse> => {
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

	getGWContour: async (graceid: string): Promise<GWContourResponse> => {
		const response = await client.get<GWContourGeoJSON>('/api/v1/gw_contour', {
			params: { graceid }
		});

		// Transform GeoJSON to the format expected by OverlayManager
		const geoJson = response.data;
		const contours: Array<{ polygon: number[][]; probability_level?: number }> = [];

		// Process each feature in the GeoJSON
		geoJson.features.forEach((feature) => {
			const credibleLevel = feature.properties.credible_level;
			const geometry = feature.geometry;

			if (geometry.type === 'MultiLineString') {
				// MultiLineString has array of line strings
				(geometry.coordinates as number[][][]).forEach((lineString) => {
					contours.push({
						polygon: lineString,
						probability_level: credibleLevel
					});
				});
			} else if (geometry.type === 'LineString') {
				// Single LineString
				contours.push({
					polygon: geometry.coordinates as number[][],
					probability_level: credibleLevel
				});
			}
		});

		// Use the same color as Flask backend for consistency
		return {
			contours,
			color: '#e6194B', // Red - matches Flask backend
			name: 'GW Contour'
		};
	},

	getGRBMOCFile: async (graceid: string, instrument: string): Promise<GRBMOCResponse> => {
		const response = await client.get<GRBMOCResponse>('/api/v1/grb_moc_file', {
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
