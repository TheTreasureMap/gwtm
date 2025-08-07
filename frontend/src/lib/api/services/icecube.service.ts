import client from '../client';
import type { IceCubeNoticeRequestSchema } from '../types/icecube.types';

export const icecubeService = {
	postIceCubeNotice: async (request: IceCubeNoticeRequestSchema): Promise<Record<string, any>> => {
		const response = await client.post<Record<string, any>>('/api/v1/post_icecube_notice', request);
		return response.data;
	}
};
