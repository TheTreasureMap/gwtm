import client from '../client';
import type {
	GWGalaxyEntrySchema,
	PostEventGalaxiesRequest,
	PostEventGalaxiesResponse,
	GalaxyFilters,
	GladeFilters
} from '../types/galaxy.types';
import type { GLADEGalaxiesResponse } from '../types/api-responses';

export const galaxyService = {
	getEventGalaxies: async (filters: GalaxyFilters): Promise<GWGalaxyEntrySchema[]> => {
		const response = await client.get<GWGalaxyEntrySchema[]>('/api/v1/event_galaxies', {
			params: filters
		});
		return response.data;
	},

	postEventGalaxies: async (
		request: PostEventGalaxiesRequest
	): Promise<PostEventGalaxiesResponse> => {
		const response = await client.post<PostEventGalaxiesResponse>(
			'/api/v1/event_galaxies',
			request
		);
		return response.data;
	},

	removeEventGalaxies: async (listid: number): Promise<{ message: string }> => {
		const response = await client.delete<{ message: string }>('/api/v1/remove_event_galaxies', {
			params: { listid }
		});
		return response.data;
	},

	getGladeGalaxies: async (filters?: GladeFilters): Promise<GLADEGalaxiesResponse> => {
		const response = await client.get<GLADEGalaxiesResponse>('/api/v1/glade', { params: filters });
		return response.data;
	}
};
