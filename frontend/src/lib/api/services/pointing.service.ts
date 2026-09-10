import client from '../client';
import type {
	PointingSchema,
	PointingCreateRequest,
	PointingResponse,
	PointingUpdate,
	CancelAllRequest,
	PointingFilters,
	PointingDeleteRequest,
	PointingUpdateBody
} from '../types/pointing.types';
import type { DOIRequest, DOIRequestResponse } from '../types/doi.types';

export const pointingService = {
	getPointings: async (filters?: PointingFilters): Promise<PointingSchema[]> => {
		const response = await client.get<PointingSchema[]>('/api/v1/pointings', { params: filters });
		return response.data;
	},

	addPointings: async (request: PointingCreateRequest): Promise<PointingResponse> => {
		const response = await client.post<PointingResponse>('/api/v1/pointings', request);
		return response.data;
	},

	updatePointings: async (update: PointingUpdate): Promise<{ message: string }> => {
		const response = await client.post<{ message: string }>('/api/v1/update_pointings', update);
		return response.data;
	},

	cancelAllPointings: async (request: CancelAllRequest): Promise<{ message: string }> => {
		const response = await client.post<{ message: string }>('/api/v1/cancel_all', request);
		return response.data;
	},

	// Not yet called from the web UI - the PUT endpoint is currently exercised
	// only at the API level, for external API consumers.
	updatePointing: async (id: number, update: PointingUpdateBody): Promise<{ message: string }> => {
		const response = await client.put<{ message: string }>(`/api/v1/pointings/${id}`, update);
		return response.data;
	},

	deletePointings: async (
		request: PointingDeleteRequest
	): Promise<{ message: string; deleted_ids: number[]; failed_ids: number[] }> => {
		const response = await client.delete<{
			message: string;
			deleted_ids: number[];
			failed_ids: number[];
		}>('/api/v1/pointings', {
			data: request
		});
		return response.data;
	},

	requestDOI: async (request: DOIRequest): Promise<DOIRequestResponse> => {
		const response = await client.post<DOIRequestResponse>('/api/v1/request_doi', request);
		return response.data;
	},

	testRefactoring: async (): Promise<{ message: string }> => {
		const response = await client.get<{ message: string }>('/api/v1/test_refactoring');
		return response.data;
	}
};
