import { pointingService } from './pointing.service';
import { doiService } from './doi.service';
import { ajaxService } from './ajax.service';
import type { PointingSearchFilters, DOIAuthorGroup } from '../types/api-responses';
import type { PointingSchema } from '../types/pointing.types';

export const searchService = {
	searchPointings: async (params: {
		graceid: string;
		bands?: string[];
		statuses?: string[];
		my_points_only?: boolean;
	}): Promise<PointingSchema[]> => {
		const filters: PointingSearchFilters = {
			graceid: params.graceid
		};

		if (params.bands && params.bands.length > 0) {
			filters.bands = params.bands.join(',');
		}

		if (params.statuses && params.statuses.length > 0) {
			filters.statuses = params.statuses.join(',');
		}

		if (params.my_points_only) {
			// This would typically require authentication and server-side filtering
		}

		return pointingService.getPointings(filters);
	},

	getUserCreatorGroups: async (): Promise<Array<{ id: string; name: string }>> => {
		try {
			const groups = await doiService.getDOIAuthorGroups();
			return groups.map((group: DOIAuthorGroup) => ({
				id: group.id.toString(),
				name: group.name
			}));
		} catch (err) {
			console.warn('Could not load DOI author groups:', err);
			return [];
		}
	},

	requestDoi: async (params: {
		pointing_ids: number[];
		graceid: string;
		doi_group_id: string;
		doi_url?: string;
	}): Promise<{ doi_url: string }> => {
		const ids = params.pointing_ids.join(',');
		const result = await ajaxService.requestDOIAjax(
			params.graceid,
			ids,
			params.doi_group_id,
			params.doi_url
		);

		return {
			doi_url: result.doi_url || ''
		};
	}
};
