import client from '../client';
import type {
    DOIPointingsResponse,
    DOIAuthorGroupSchema,
    DOIAuthorSchema
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
    }
};
