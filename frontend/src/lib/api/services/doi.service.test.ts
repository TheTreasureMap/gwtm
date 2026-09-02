import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the axios client before importing the service
vi.mock('../client', () => ({
	default: {
		get: vi.fn(),
		post: vi.fn(),
		put: vi.fn(),
		delete: vi.fn()
	}
}));

import client from '../client';
import { doiService } from './doi.service';
import type { DOIAuthorGroupSchema, DOIAuthorGroupSaveRequest } from '../types/doi.types';

const mockClient = client as unknown as {
	get: ReturnType<typeof vi.fn>;
	post: ReturnType<typeof vi.fn>;
	put: ReturnType<typeof vi.fn>;
	delete: ReturnType<typeof vi.fn>;
};

describe('doiService — author group mutations', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	const sampleGroup: DOIAuthorGroupSchema = { id: 42, name: 'My Group', userid: 1 };

	const samplePayload: DOIAuthorGroupSaveRequest = {
		name: 'My Group',
		authors: [{ name: 'Alice Smith', affiliation: 'MIT' }]
	};

	// ----------------------------------------------------------------
	// createDOIAuthorGroup
	// ----------------------------------------------------------------

	describe('createDOIAuthorGroup', () => {
		it('posts to /api/v1/doi_author_groups and returns the created group', async () => {
			mockClient.post.mockResolvedValueOnce({ data: sampleGroup });

			const result = await doiService.createDOIAuthorGroup(samplePayload);

			expect(mockClient.post).toHaveBeenCalledOnce();
			expect(mockClient.post).toHaveBeenCalledWith('/api/v1/doi_author_groups', samplePayload);
			expect(result).toEqual(sampleGroup);
		});

		it('forwards rejection from the client', async () => {
			mockClient.post.mockRejectedValueOnce(new Error('Network error'));

			await expect(doiService.createDOIAuthorGroup(samplePayload)).rejects.toThrow('Network error');
		});
	});

	// ----------------------------------------------------------------
	// updateDOIAuthorGroup
	// ----------------------------------------------------------------

	describe('updateDOIAuthorGroup', () => {
		it('puts to /api/v1/doi_author_groups/{id} and returns the updated group', async () => {
			const updated = { ...sampleGroup, name: 'Renamed Group' };
			mockClient.put.mockResolvedValueOnce({ data: updated });

			const result = await doiService.updateDOIAuthorGroup(42, {
				...samplePayload,
				name: 'Renamed Group'
			});

			expect(mockClient.put).toHaveBeenCalledOnce();
			expect(mockClient.put).toHaveBeenCalledWith(
				'/api/v1/doi_author_groups/42',
				expect.objectContaining({ name: 'Renamed Group' })
			);
			expect(result.name).toBe('Renamed Group');
		});

		it('encodes the group id in the URL correctly', async () => {
			mockClient.put.mockResolvedValueOnce({ data: { ...sampleGroup, id: 99 } });

			await doiService.updateDOIAuthorGroup(99, samplePayload);

			expect(mockClient.put).toHaveBeenCalledWith(
				'/api/v1/doi_author_groups/99',
				expect.anything()
			);
		});

		it('forwards rejection from the client', async () => {
			mockClient.put.mockRejectedValueOnce({ response: { status: 404 } });

			await expect(doiService.updateDOIAuthorGroup(42, samplePayload)).rejects.toMatchObject({
				response: { status: 404 }
			});
		});
	});

	// ----------------------------------------------------------------
	// deleteDOIAuthorGroup
	// ----------------------------------------------------------------

	describe('deleteDOIAuthorGroup', () => {
		it('sends DELETE to /api/v1/doi_author_groups/{id}', async () => {
			mockClient.delete.mockResolvedValueOnce({});

			await doiService.deleteDOIAuthorGroup(42);

			expect(mockClient.delete).toHaveBeenCalledOnce();
			expect(mockClient.delete).toHaveBeenCalledWith('/api/v1/doi_author_groups/42');
		});

		it('encodes the group id in the URL correctly', async () => {
			mockClient.delete.mockResolvedValueOnce({});

			await doiService.deleteDOIAuthorGroup(7);

			expect(mockClient.delete).toHaveBeenCalledWith('/api/v1/doi_author_groups/7');
		});

		it('forwards rejection from the client', async () => {
			mockClient.delete.mockRejectedValueOnce({ response: { status: 403 } });

			await expect(doiService.deleteDOIAuthorGroup(42)).rejects.toMatchObject({
				response: { status: 403 }
			});
		});
	});
});
