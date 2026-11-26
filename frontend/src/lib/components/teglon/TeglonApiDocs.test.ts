import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';

vi.mock('./teglon', async (importOriginal) => {
	const actual = await importOriginal<typeof import('./teglon')>();
	return { ...actual, teglon: { enabled: vi.fn() } };
});

const { apiBase } = vi.hoisted(() => ({ apiBase: { value: '' } }));
vi.mock('$lib/api/client', () => ({ getApiBaseUrl: () => apiBase.value }));

import { teglon } from './teglon';
import TeglonApiDocs from './TeglonApiDocs.svelte';

const enabled = teglon.enabled as unknown as ReturnType<typeof vi.fn>;

describe('TeglonApiDocs', () => {
	it('is hidden when Teglon is switched off', async () => {
		enabled.mockResolvedValue(false);
		const { container } = render(TeglonApiDocs);
		await waitFor(() => expect(enabled).toHaveBeenCalled());
		await new Promise((resolve) => setTimeout(resolve, 0));
		expect(container.textContent?.trim()).toBe('');
	});

	it('documents the routes for this site when Teglon is on', async () => {
		enabled.mockResolvedValue(true);
		apiBase.value = '';
		render(TeglonApiDocs);
		expect(await screen.findByText('Suggested Pointings (Teglon)')).toBeTruthy();
		expect(screen.getByText(/BASE = "http:\/\/localhost(:\d+)?\/api\/v1\/teglon"/)).toBeTruthy();
	});

	it('shows a separately configured API address', async () => {
		enabled.mockResolvedValue(true);
		apiBase.value = 'https://api.example.org/';
		render(TeglonApiDocs);
		expect(
			await screen.findByText(/BASE = "https:\/\/api\.example\.org\/api\/v1\/teglon"/)
		).toBeTruthy();
	});

	it("uses the page's own address for a relative API base", async () => {
		enabled.mockResolvedValue(true);
		apiBase.value = '/';
		render(TeglonApiDocs);
		expect(
			await screen.findByText(new RegExp(`BASE = "${window.location.origin}/api/v1/teglon"`))
		).toBeTruthy();
	});

	it('keeps the path of a relative API base', async () => {
		enabled.mockResolvedValue(true);
		apiBase.value = '/gateway/';
		render(TeglonApiDocs);
		expect(
			await screen.findByText(
				new RegExp(`BASE = "${window.location.origin}/gateway/api/v1/teglon"`)
			)
		).toBeTruthy();
	});
});
