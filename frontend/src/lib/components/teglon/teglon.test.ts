import { describe, it, expect, vi } from 'vitest';
import {
	afterTable,
	afterRun,
	formatNumber,
	formatProbability,
	formatUtc,
	contourPolygons,
	drawContours,
	CONTOUR_STYLE
} from './teglon';

const table = {
	graceid: 'S1',
	healpix_file: 'bayestar.fits',
	generated_at: '2026-11-25T12:00:00Z',
	detector: 'SWOPE',
	band: 'r',
	pointings: [{ field_name: 'A', ra: 1, dec: 2, prob: 0.1, cum_prob: 0.1 }]
};

describe('afterTable', () => {
	it('shows a table', () => {
		expect(afterTable({ status: 200, data: table })).toEqual({ kind: 'ready', table });
	});

	it('waits on a setup run that is still going', () => {
		const step = afterTable({
			status: 404,
			data: { message: 'Teglon is setting up', task_id: 't-1', state: 'STARTED' }
		});
		expect(step).toEqual({ kind: 'wait', taskId: 't-1', message: 'Teglon is setting up' });
	});

	it('reports a failed setup run as a failure', () => {
		const step = afterTable({
			status: 404,
			data: {
				message: "Teglon couldn't set up this instrument: boom",
				task_id: 't-1',
				state: 'FAILURE'
			}
		});
		expect(step).toEqual({
			kind: 'stop',
			message: "Teglon couldn't set up this instrument: boom",
			failed: true
		});
	});

	it("passes on Teglon's message when it can't help yet", () => {
		const step = afterTable({
			status: 404,
			data: { message: "Teglon hasn't processed this event yet" }
		});
		expect(step).toEqual({
			kind: 'stop',
			message: "Teglon hasn't processed this event yet",
			failed: false
		});
	});

	it('does not loop when a finished run left no table', () => {
		const step = afterTable({
			status: 404,
			data: { message: 'x', task_id: 't-1', state: 'SUCCESS' }
		});
		expect(step.kind).toBe('stop');
	});

	it("uses FastAPI's detail when there is no message", () => {
		expect(afterTable({ status: 404, data: { detail: 'Not Found' } })).toEqual({
			kind: 'stop',
			message: 'Not Found',
			failed: false
		});
	});

	it('explains an expired login instead of echoing the 401', () => {
		const reply = {
			status: 401,
			data: { message: 'Authentication required. Please provide a valid JWT token or API token.' }
		};
		const expected = {
			kind: 'stop',
			message: 'Your session has expired. Please log out and log in again.',
			failed: false
		};
		expect(afterTable(reply)).toEqual(expected);
		expect(afterRun(reply)).toEqual(expected);
	});

	it('falls back to a generic message', () => {
		expect(afterTable({ status: 502, data: null })).toEqual({
			kind: 'stop',
			message: 'Teglon request failed (HTTP 502)',
			failed: true
		});
	});
});

describe('afterRun', () => {
	it('fetches the table once a run has succeeded or was reused', () => {
		expect(
			afterRun({ status: 200, data: { task_id: 't', state: 'SUCCESS', reused: true } })
		).toEqual({
			kind: 'fetch'
		});
	});

	it('waits while a run is queued or running', () => {
		const step = afterRun({ status: 202, data: { task_id: 't-2', state: 'PENDING' } });
		expect(step).toMatchObject({ kind: 'wait', taskId: 't-2' });
	});

	it('reports a failed run with its error', () => {
		const step = afterRun({
			status: 200,
			data: { task_id: 't', state: 'FAILURE', error: 'no map' }
		});
		expect(step).toEqual({
			kind: 'stop',
			message: "Teglon couldn't work out suggested pointings: no map",
			failed: true
		});
	});

	it('stops on an error reply, such as a run Teglon has forgotten', () => {
		const step = afterRun({ status: 404, data: { message: 'No run with id t' } });
		expect(step).toEqual({ kind: 'stop', message: 'No run with id t', failed: false });
	});
});

describe('formatNumber', () => {
	it('formats numbers and shows a dash for missing values', () => {
		expect(formatNumber(1.23456, 3)).toBe('1.235');
		expect(formatNumber(null, 3)).toBe('—');
	});
});

describe('formatProbability', () => {
	it('keeps small probabilities readable', () => {
		expect(formatProbability(0.000012345)).toBe('0.0000123');
		expect(formatProbability(0.25)).toBe('0.250');
		expect(formatProbability(null)).toBe('—');
	});
});

describe('formatUtc', () => {
	it('shows the time in UTC whatever the browser time zone', () => {
		expect(formatUtc('2026-11-25T12:34:56Z')).toBe('2026-11-25 12:34 UTC');
	});
});

describe('contourPolygons', () => {
	it('collects polygons from every overlay and skips malformed ones', () => {
		const data = {
			detection_overlays: [
				{
					name: '50%',
					color: '#e6194B',
					contours: [
						{
							polygon: [
								[1, 2],
								[3, 4],
								[5, 6]
							]
						}
					]
				},
				{
					name: '90%',
					contours: [
						{
							polygon: [
								[7, 8],
								[9, 10],
								[11, 12]
							]
						},
						{}
					]
				}
			]
		};
		expect(contourPolygons(data)).toEqual([
			[
				[1, 2],
				[3, 4],
				[5, 6]
			],
			[
				[7, 8],
				[9, 10],
				[11, 12]
			]
		]);
		expect(contourPolygons({ message: 'nope' })).toEqual([]);
	});
});

describe('drawContours', () => {
	it("draws in gwtm's Teglon style, not Teglon's own colours", () => {
		const added: unknown[] = [];
		const layer = { addFootprints: vi.fn() };
		const A = { graphicOverlay: vi.fn(() => layer), polygon: vi.fn((p) => ({ p })) };
		const aladin = { addOverlay: (l: unknown) => added.push(l), removeOverlay: vi.fn() };
		expect(
			drawContours(aladin, A, [
				[
					[1, 2],
					[3, 4],
					[5, 6]
				]
			])
		).toBe(layer);
		expect(A.graphicOverlay).toHaveBeenCalledWith(expect.objectContaining(CONTOUR_STYLE));
		expect(added).toEqual([layer]);
		expect(layer.addFootprints).toHaveBeenCalledWith([
			{
				p: [
					[1, 2],
					[3, 4],
					[5, 6]
				]
			}
		]);
	});
});
