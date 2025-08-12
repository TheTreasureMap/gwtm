import client from '../client';
import type {
	CandidateSchema,
	PostCandidateRequest,
	CandidateResponse,
	PutCandidateRequest,
	DeleteCandidateParams,
	DeleteCandidateResponse,
	CandidateFilters,
	GWCandidateSchema,
	GWCandidateCreate
} from '../types/candidate.types';
import type { CandidateEventResponse } from '../types/api-responses';

export const candidateService = {
	getCandidates: async (filters?: CandidateFilters, ids?: number[]): Promise<CandidateSchema[]> => {
		const response = await client.get<CandidateSchema[]>('/api/v1/candidate', {
			params: {
				...filters,
				...(ids && { body: JSON.stringify(ids) })
			}
		});
		return response.data;
	},

	postCandidates: async (request: PostCandidateRequest): Promise<CandidateResponse> => {
		const response = await client.post<CandidateResponse>('/api/v1/candidate', request);
		return response.data;
	},

	updateCandidate: async (request: PutCandidateRequest): Promise<PutCandidateRequest> => {
		const response = await client.put<PutCandidateRequest>('/api/v1/candidate', request);
		return response.data;
	},

	deleteCandidates: async (params: DeleteCandidateParams): Promise<DeleteCandidateResponse> => {
		const response = await client.delete<DeleteCandidateResponse>('/api/v1/candidate', { params });
		return response.data;
	},

	getCandidateEvents: async (id?: number, user_id?: number): Promise<GWCandidateSchema[]> => {
		const response = await client.get<GWCandidateSchema[]>('/api/v1/candidate/event', {
			params: { id, user_id }
		});
		return response.data;
	},

	createCandidateEvent: async (candidate: GWCandidateCreate): Promise<CandidateEventResponse> => {
		const response = await client.post<CandidateEventResponse>(
			'/api/v1/candidate/event',
			candidate
		);
		return response.data;
	},

	updateCandidateEvent: async (
		candidateId: number,
		candidate: GWCandidateSchema
	): Promise<CandidateEventResponse> => {
		const response = await client.put<CandidateEventResponse>(
			`/api/v1/candidate/event/${candidateId}`,
			candidate
		);
		return response.data;
	},

	deleteCandidateEvent: async (
		candidateId: number
	): Promise<{ success: boolean; message: string }> => {
		const response = await client.delete<{ success: boolean; message: string }>(
			`/api/v1/candidate/event/${candidateId}`
		);
		return response.data;
	}
};
