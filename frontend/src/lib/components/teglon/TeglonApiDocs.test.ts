import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';

vi.mock('./teglon', async (importOriginal) => {
	const actual = await importOriginal<typeof import('./teglon')>();
	return { ...actual, teglon: { enabled: vi.fn() } };
});

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
		render(TeglonApiDocs);
		expect(await screen.findByText('Suggested Pointings (Teglon)')).toBeTruthy();
		expect(screen.getByText(/BASE = "http:\/\/localhost(:\d+)?\/api\/v1\/teglon"/)).toBeTruthy();
	});
});
