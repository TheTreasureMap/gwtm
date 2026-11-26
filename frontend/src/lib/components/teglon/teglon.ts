// Teglon suggested pointings: API calls and how to read their replies.
// Everything Teglon-specific lives in this folder so the feature can be removed in one place.
import client from '$lib/api/client';

export interface SuggestedPointing {
	field_name: string | null;
	ra: number | null;
	dec: number | null;
	prob: number | null;
	cum_prob: number | null;
}

export interface SuggestedTable {
	graceid: string;
	healpix_file: string;
	generated_at: string | null;
	detector: string | null;
	band: string | null;
	pointings: SuggestedPointing[];
}

// The fields gwtm and Teglon put in a reply body: feature status, a table, a run, or an error.
interface ReplyBody {
	message?: string;
	task_id?: string;
	state?: string;
	error?: string | null;
	pointings?: unknown;
	enabled?: boolean;
	reused?: boolean;
	detection_overlays?: unknown;
	// FastAPI's own errors, such as a 404 for a route that is no longer registered.
	detail?: unknown;
}

export interface Reply {
	status: number;
	data: ReplyBody | null;
}

// What to do with a reply.
export type Step =
	| { kind: 'ready'; table: SuggestedTable }
	| { kind: 'wait'; taskId: string; message: string }
	| { kind: 'fetch' }
	| { kind: 'stop'; message: string; failed: boolean };

const ACTIVE = new Set(['PENDING', 'STARTED']);
const WORKING = 'Teglon is working out suggested pointings for this instrument.';

// gwtm's login check is the only source of a 401 here: the backend turns Teglon's own 401s into 502s.
// Logins last 30 minutes while the page still looks logged in, so say what to do rather than echo it.
const SESSION_EXPIRED = 'Your session has expired. Please log out and log in again.';

export function messageOf(reply: Reply): string {
	if (reply.status === 401) return SESSION_EXPIRED;
	const detail = reply.data?.detail;
	return (
		reply.data?.message ||
		(typeof detail === 'string' && detail) ||
		`Teglon request failed (HTTP ${reply.status})`
	);
}

/** A reply from GET /suggested_pointings. */
export function afterTable(reply: Reply): Step {
	if (reply.status === 200 && Array.isArray(reply.data?.pointings)) {
		return { kind: 'ready', table: reply.data as unknown as SuggestedTable };
	}
	// A 404 that carries a run means Teglon is setting the instrument up, or failed to.
	const run = reply.data;
	if (reply.status === 404 && run?.task_id) {
		if (ACTIVE.has(run.state))
			return { kind: 'wait', taskId: run.task_id, message: messageOf(reply) };
		return { kind: 'stop', message: messageOf(reply), failed: run.state === 'FAILURE' };
	}
	return { kind: 'stop', message: messageOf(reply), failed: reply.status >= 500 };
}

/** A reply from POST /planned_runs or GET /planned_runs/{task_id}. */
export function afterRun(reply: Reply): Step {
	const run = reply.data;
	if (reply.status >= 400 || !run?.task_id) {
		return { kind: 'stop', message: messageOf(reply), failed: reply.status >= 500 };
	}
	if (run.state === 'SUCCESS') return { kind: 'fetch' };
	if (ACTIVE.has(run.state)) return { kind: 'wait', taskId: run.task_id, message: WORKING };
	return {
		kind: 'stop',
		message: `Teglon couldn't work out suggested pointings: ${run.error || run.state}`,
		failed: true
	};
}

async function call(method: 'get' | 'post', path: string, params?: object): Promise<Reply> {
	try {
		const response = await client.request({ method, url: `/api/v1/teglon${path}`, params });
		return { status: response.status, data: response.data };
	} catch (error) {
		// Teglon's 404s (setting up, not processed yet) are answers, not failures.
		const response = (error as { response?: { status: number; data: ReplyBody | null } }).response;
		if (response) return { status: response.status, data: response.data };
		throw error;
	}
}

export const teglon = {
	enabled: async (): Promise<boolean> => (await call('get', '/status')).data?.enabled === true,
	table: (graceid: string, instrumentId: number, excludePlanned: boolean) =>
		call('get', '/suggested_pointings', {
			graceid,
			instrument_id: instrumentId,
			exclude_planned: excludePlanned
		}),
	startPlannedRun: (graceid: string, instrumentId: number) =>
		call('post', '/planned_runs', { graceid, instrument_id: instrumentId }),
	run: (taskId: string) => call('get', `/planned_runs/${encodeURIComponent(taskId)}`),
	contours: (graceid: string, includePlanned: boolean) =>
		call('get', '/contours', { graceid, include_planned: includePlanned })
};

// Teglon's own contour colours include the red gwtm uses for the GW contour, so they are ignored
// and its contours are drawn in this style instead.
export const CONTOUR_STYLE = { color: '#00e5ff', lineWidth: 2, lineDash: [6, 4] };
const CONTOUR_LAYER_NAME = 'Teglon contours';
// Aladin dispatches this on its container for each layer it removes, by whatever code path.
export const LAYER_REMOVED_EVENT = 'AL:GraphicOverlayLayer.removed';

export type Polygon = [number, number][];

/** The [RA, Dec] polygons in a /contours reply, from every overlay Teglon returned. */
export function contourPolygons(data: unknown): Polygon[] {
	const overlays = (data as { detection_overlays?: { contours?: { polygon?: Polygon }[] }[] })
		?.detection_overlays;
	if (!Array.isArray(overlays)) return [];
	return overlays.flatMap((overlay) =>
		(overlay.contours ?? []).map((c) => c.polygon).filter((p): p is Polygon => Array.isArray(p))
	);
}

/** Draw polygons on an Aladin view as one Teglon layer; returns the layer so it can be removed. */
export function drawContours(aladin: AladinLike, A: AladinLib, polygons: Polygon[]): unknown {
	const layer = A.graphicOverlay({ ...CONTOUR_STYLE, name: CONTOUR_LAYER_NAME });
	aladin.addOverlay(layer);
	layer.addFootprints(polygons.map((p) => A.polygon(p)));
	return layer;
}

export interface AladinLike {
	addOverlay(layer: unknown): void;
	removeOverlay(layer: unknown): void;
	aladinDiv?: EventTarget;
}

export interface AladinLib {
	graphicOverlay(options: object): { addFootprints(footprints: unknown[]): void };
	polygon(vertices: Polygon): unknown;
}

export function formatNumber(value: number | null, digits: number): string {
	return value === null || value === undefined ? '—' : value.toFixed(digits);
}

/** Probabilities span orders of magnitude, so show significant figures rather than fixed decimals. */
export function formatProbability(value: number | null): string {
	return value === null || value === undefined ? '—' : value.toPrecision(3);
}

/** An ISO timestamp as `YYYY-MM-DD HH:MM UTC`. */
export function formatUtc(iso: string): string {
	return `${new Date(iso).toISOString().slice(0, 16).replace('T', ' ')} UTC`;
}
