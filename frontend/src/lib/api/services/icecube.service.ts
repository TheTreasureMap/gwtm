import client from '../client';
import type { IceCubeNoticeRequestSchema } from '../types/icecube.types';
import type { IceCubeNoticeResponse } from '../types/api-responses';

export const icecubeService = {
	postIceCubeNotice: async (
		request: IceCubeNoticeRequestSchema
	): Promise<IceCubeNoticeResponse> => {
		const response = await client.post<IceCubeNoticeResponse>(
			'/api/v1/post_icecube_notice',
			request
		);
		return response.data;
	}
};
