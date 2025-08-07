import client from '../client';
import type { HealthResponse, ServiceStatusResponse } from '../types/misc.types';

export const miscService = {
	health: async (): Promise<HealthResponse> => {
		const response = await client.get<HealthResponse>('/health');
		return response.data;
	},

	serviceStatus: async (): Promise<ServiceStatusResponse> => {
		const response = await client.get<ServiceStatusResponse>('/service-status');
		return response.data;
	},

	fixData: async (): Promise<{ message: string }> => {
		const response = await client.get<{ message: string }>('/fixdata');
		return response.data;
	},

	fixDataPost: async (): Promise<{ message: string }> => {
		const response = await client.post<{ message: string }>('/fixdata', {});
		return response.data;
	}
};
