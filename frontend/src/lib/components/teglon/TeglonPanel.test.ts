import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';

// vi.mock factories are hoisted above imports, so the store they share is created in vi.hoisted.
const { authState } = await vi.hoisted(async () => {
	const { writable } = await import('svelte/store');
	return {
		authState: writable({ isAuthenticated: true, user: null, token: 't', loading: false })
	};
});
vi.mock('$lib/stores/auth', () => ({ auth: { subscribe: authState.subscribe } }));

vi.mock('$lib/api', () => ({
	api: {
		instruments: {
			getInstruments: vi.fn().mockResolvedValue([
				{ id: 9, instrument_name: 'Sinistro', instrument_type: 1 },
				{ id: 47, instrument_name: 'ZTF', instrument_type: 1 }
			])
		}
	}
}));

vi.mock('./teglon', async (importOriginal) => {
	const actual = await importOriginal<typeof import('./teglon')>();
	return {
		...actual,
		teglon: { enabled: vi.fn(), table: vi.fn(), startPlannedRun: vi.fn(), run: vi.fn() }
	};
});

import { api } from '$lib/api';
import { teglon } from './teglon';
import TeglonPanel from './TeglonPanel.svelte';

const mocked = teglon as unknown as Record<keyof typeof teglon, ReturnType<typeof vi.fn>>;

const TABLE = {
	graceid: 'S1',
	healpix_file: 'bayestar.fits',
	generated_at: null,
	detector: 'SINISTRO',
	band: 'r',
	pointings: [{ field_name: 'F1', ra: 10, dec: -20, prob: 0.2, cum_prob: 0.2 }]
};

async function chooseInstrumentAndRequest() {
	const select = await screen.findByRole('combobox');
	await waitFor(() => expect(screen.getByRole('option', { name: 'Sinistro' })).toBeTruthy());
	await fireEvent.change(select, { target: { value: '9' } });
	await fireEvent.click(screen.getByRole('button', { name: 'Get suggested pointings' }));
}

beforeEach(() => {
	vi.clearAllMocks();
	authState.set({ isAuthenticated: true, user: null, token: 't', loading: false });
	mocked.enabled.mockResolvedValue(true);
});

afterEach(() => {
	vi.useRealTimers();
});

describe('TeglonPanel', () => {
	it('renders nothing when Teglon is switched off', async () => {
		mocked.enabled.mockResolvedValue(false);
		const { container } = render(TeglonPanel, { graceid: 'S1' });
		await waitFor(() => expect(mocked.enabled).toHaveBeenCalled());
		await new Promise((resolve) => setTimeout(resolve, 0));
		expect(container.textContent?.trim()).toBe('');
		expect(api.instruments.getInstruments).not.toHaveBeenCalled();
		expect(mocked.table).not.toHaveBeenCalled();
	});

	it('asks logged-out users to log in without calling Teglon', async () => {
		authState.set({ isAuthenticated: false, user: null, token: null, loading: false });
		render(TeglonPanel, { graceid: 'S1' });
		expect(await screen.findByText('Log in to see suggested pointings.')).toBeTruthy();
		expect(api.instruments.getInstruments).not.toHaveBeenCalled();
		expect(mocked.table).not.toHaveBeenCalled();
	});

	it("shows Teglon's table for the chosen instrument", async () => {
		mocked.table.mockResolvedValue({ status: 200, data: TABLE });
		render(TeglonPanel, { graceid: 'S1' });
		await chooseInstrumentAndRequest();
		expect(await screen.findByText('F1')).toBeTruthy();
		expect(mocked.table).toHaveBeenCalledWith('S1', 9, false);
	});

	it('polls a setup run and shows the table when it finishes', async () => {
		vi.useFakeTimers({ shouldAdvanceTime: true });
		mocked.table
			.mockResolvedValueOnce({
				status: 404,
				data: { message: 'Teglon is setting up.', task_id: 'run-1', state: 'STARTED' }
			})
			.mockResolvedValueOnce({ status: 200, data: TABLE });
		mocked.run.mockResolvedValue({ status: 200, data: { task_id: 'run-1', state: 'SUCCESS' } });

		render(TeglonPanel, { graceid: 'S1' });
		await chooseInstrumentAndRequest();
		expect(await screen.findByText(/Teglon is setting up\./)).toBeTruthy();

		await vi.advanceTimersByTimeAsync(10000);
		expect(await screen.findByText('F1')).toBeTruthy();
		expect(mocked.run).toHaveBeenCalledWith('run-1');
	});

	it('starts a planned run first when avoiding planned pointings', async () => {
		mocked.startPlannedRun.mockResolvedValue({
			status: 200,
			data: { task_id: 'p-1', state: 'SUCCESS', reused: true }
		});
		mocked.table.mockResolvedValue({ status: 200, data: TABLE });
		render(TeglonPanel, { graceid: 'S1' });
		await fireEvent.click(await screen.findByRole('checkbox'));
		await chooseInstrumentAndRequest();
		expect(await screen.findByText('F1')).toBeTruthy();
		expect(mocked.startPlannedRun).toHaveBeenCalledWith('S1', 9);
		expect(mocked.table).toHaveBeenCalledWith('S1', 9, true);
	});

	it('does not start polling after the panel is removed mid-request', async () => {
		vi.useFakeTimers({ shouldAdvanceTime: true });
		let answer: (reply: unknown) => void = () => {};
		mocked.table.mockReturnValue(new Promise((resolve) => (answer = resolve)));
		const { unmount } = render(TeglonPanel, { graceid: 'S1' });
		await chooseInstrumentAndRequest();
		unmount();
		// The reply arrives after the panel has gone; it must not schedule a poll.
		answer({ status: 404, data: { message: 'Setting up.', task_id: 'run-1', state: 'STARTED' } });
		await vi.advanceTimersByTimeAsync(30000);
		expect(mocked.run).not.toHaveBeenCalled();
	});

	it('clears the table when the event changes', async () => {
		mocked.table.mockResolvedValue({ status: 200, data: TABLE });
		const { rerender } = render(TeglonPanel, { graceid: 'S1' });
		await chooseInstrumentAndRequest();
		await screen.findByText('F1');
		await rerender({ graceid: 'S2' });
		await waitFor(() => expect(screen.queryByText('F1')).toBeNull());
	});

	it('frees the button after a network error', async () => {
		mocked.table.mockRejectedValue(new Error('Network Error'));
		render(TeglonPanel, { graceid: 'S1' });
		await chooseInstrumentAndRequest();
		expect((await screen.findByRole('alert')).textContent).toContain(
			'Could not reach Treasure Map'
		);
		const button = screen.getByRole('button', {
			name: 'Get suggested pointings'
		}) as HTMLButtonElement;
		expect(button.disabled).toBe(false);
	});

	it('drops a pending job when the instrument changes', async () => {
		vi.useFakeTimers({ shouldAdvanceTime: true });
		mocked.table.mockResolvedValue({
			status: 404,
			data: { message: 'Teglon is setting up.', task_id: 'run-1', state: 'STARTED' }
		});
		mocked.run.mockResolvedValue({ status: 200, data: { task_id: 'run-1', state: 'SUCCESS' } });
		render(TeglonPanel, { graceid: 'S1' });
		await chooseInstrumentAndRequest();
		await screen.findByText(/Teglon is setting up\./);

		await fireEvent.change(screen.getByRole('combobox'), { target: { value: '47' } });
		await vi.advanceTimersByTimeAsync(30000);
		expect(mocked.run).not.toHaveBeenCalled();
		expect(mocked.table).toHaveBeenCalledTimes(1);
		expect(screen.queryByText(/Teglon is setting up\./)).toBeNull();
	});
});
