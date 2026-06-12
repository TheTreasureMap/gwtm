import client from '../client';
import type {
	DOIPointingsResponse,
	DOIAuthorGroupSchema,
	DOIAuthorSchema,
	DOIAuthorGroupSaveRequest
} from '../types/doi.types';

export const doiService = {
	getDOIPointings: async (): Promise<DOIPointingsResponse> => {
		const response = await client.get<DOIPointingsResponse>('/api/v1/doi_pointings');
		return response.data;
	},

	getDOIAuthorGroups: async (): Promise<DOIAuthorGroupSchema[]> => {
		const response = await client.get<DOIAuthorGroupSchema[]>('/api/v1/doi_author_groups');
		return response.data;
	},

	getDOIAuthors: async (groupId: number): Promise<DOIAuthorSchema[]> => {
		const response = await client.get<DOIAuthorSchema[]>(`/api/v1/doi_authors/${groupId}`);
		return response.data;
	},

	createDOIAuthorGroup: async (data: DOIAuthorGroupSaveRequest): Promise<DOIAuthorGroupSchema> => {
		const response = await client.post<DOIAuthorGroupSchema>('/api/v1/doi_author_groups', data);
		return response.data;
	},

	updateDOIAuthorGroup: async (
		groupId: number,
		data: DOIAuthorGroupSaveRequest
	): Promise<DOIAuthorGroupSchema> => {
		const response = await client.put<DOIAuthorGroupSchema>(
			`/api/v1/doi_author_groups/${groupId}`,
			data
		);
		return response.data;
	},

	deleteDOIAuthorGroup: async (groupId: number): Promise<void> => {
		await client.delete(`/api/v1/doi_author_groups/${groupId}`);
	}
};
