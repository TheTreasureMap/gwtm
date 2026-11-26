<script lang="ts">
	// Teglon's suggested pointings for this event. Renders nothing unless the backend reports the
	// feature enabled (GET /api/v1/teglon/status), so switching Teglon off removes this panel.
	import { onMount, onDestroy } from 'svelte';
	import { auth } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import {
		teglon,
		afterTable,
		afterRun,
		formatNumber,
		formatProbability,
		formatUtc,
		messageOf,
		contourPolygons,
		drawContours,
		CONTOUR_STYLE,
		LAYER_REMOVED_EVENT,
		type AladinLib,
		type AladinLike,
		type Polygon,
		type Step,
		type SuggestedTable
	} from './teglon';

	export let graceid: string;
	export let aladin: AladinLike | null = null;

	const POLL_MS = 10000;
	// About five minutes. Teglon reports a hung run as still STARTED, so polling needs its own limit.
	const MAX_POLLS = 30;

	let enabled = false;
	let instruments: { id: number; name: string }[] = [];
	let instrumentsRequested = false;
	let instrumentId: number | null = null;
	let excludePlanned = false;

	let busy = false;
	let waiting = '';
	let message = '';
	let failed = false;
	let table: SuggestedTable | null = null;

	let showContours = false;
	let polygons: Polygon[] | null = null;
	let contourLayer: unknown = null;
	// The viewer the layer was drawn on: the sky map builds a new one when the event changes.
	let layerOwner: AladinLike | null = null;
	let destroyed = false;
	let contourMessage = '';
	let contoursLoading = false;
	let contourGeneration = 0;

	// Bumped on every new request or event, so replies and polls from an older one are dropped.
	let generation = 0;
	let timer: ReturnType<typeof setTimeout> | undefined;

	onMount(async () => {
		try {
			enabled = await teglon.enabled();
		} catch {
			enabled = false;
		}
	});

	// reset() also bumps generation, so a reply still in flight can't schedule a poll after unmount.
	onDestroy(() => {
		// Clear polygons first so a re-add queued by the map's own teardown can't draw on a dead viewer.
		destroyed = true;
		polygons = null;
		reset();
		contourGeneration += 1;
		removeContours();
		listenTo(null);
	});

	// Contours depend on the event and on whether planned sky is taken out, not on the instrument.
	$: contourKey =
		showContours && enabled && $auth.isAuthenticated ? `${graceid}|${excludePlanned}` : '';
	$: loadContours(contourKey);

	// A new viewer: take the layer off the old one; the next statement draws it on the new one.
	$: if (contourLayer && aladin !== layerOwner) removeContours();
	$: if (aladin && polygons?.length && !contourLayer) showLayer();

	// The sky map removes every overlay when it redraws or the time range moves. Aladin announces each
	// removal, so put the layer back once the removal has finished (a synchronous re-add is wiped).
	let listeningOn: EventTarget | null = null;
	$: listenTo(aladin?.aladinDiv ?? null);

	function listenTo(target: EventTarget | null) {
		if (target === listeningOn) return;
		listeningOn?.removeEventListener(LAYER_REMOVED_EVENT, onLayerRemoved);
		target?.addEventListener(LAYER_REMOVED_EVENT, onLayerRemoved);
		listeningOn = target;
	}

	function onLayerRemoved(event: Event) {
		const layer = (event as CustomEvent).detail?.layer;
		if (!layer || layer !== contourLayer) return;
		// Nothing changes synchronously: setting contourLayer here would let the redraw statement run
		// during the map's teardown, before this panel is destroyed.
		queueMicrotask(() => {
			if (destroyed || layer !== contourLayer) return;
			contourLayer = null;
			layerOwner = null;
			showLayer();
		});
	}

	$: if (enabled && $auth.isAuthenticated && !instrumentsRequested) loadInstruments();

	// A new event, instrument or avoid-planned choice makes any pending job and shown table stale.
	const settingsKey = (event: string, id: number | null, avoidPlanned: boolean) =>
		`${event}|${id}|${avoidPlanned}`;
	let shownFor = settingsKey(graceid, instrumentId, excludePlanned);
	$: if (settingsKey(graceid, instrumentId, excludePlanned) !== shownFor) {
		shownFor = settingsKey(graceid, instrumentId, excludePlanned);
		reset();
	}

	async function loadInstruments() {
		instrumentsRequested = true;
		try {
			const list = await api.instruments.getInstruments({ type: 1 });
			instruments = list
				.map((i) => ({
					id: i.id,
					name: i.nickname ? `${i.instrument_name} (${i.nickname})` : i.instrument_name
				}))
				.sort((a, b) => a.name.localeCompare(b.name));
		} catch {
			// Not retried automatically: a reactive retry would loop while the server is down.
			message = 'Could not load the instrument list. Reload the page to try again.';
			failed = true;
		}
	}

	async function loadContours(key: string) {
		contourGeneration += 1;
		const gen = contourGeneration;
		removeContours();
		polygons = null;
		contourMessage = '';
		contoursLoading = false;
		if (!key) return;
		contoursLoading = true;
		try {
			const reply = await teglon.contours(graceid, excludePlanned);
			if (gen !== contourGeneration) return;
			contoursLoading = false;
			if (reply.status !== 200) {
				contourMessage = messageOf(reply);
				return;
			}
			polygons = contourPolygons(reply.data);
			if (polygons.length === 0) contourMessage = 'Teglon has no contours for this event.';
		} catch {
			if (gen !== contourGeneration) return;
			contoursLoading = false;
			contourMessage = 'Could not reach Treasure Map.';
		}
	}

	function showLayer() {
		const A = (window as unknown as { A?: AladinLib }).A;
		if (destroyed || !aladin || !A || !polygons?.length) return;
		contourLayer = drawContours(aladin, A, polygons);
		layerOwner = aladin;
	}

	function removeContours() {
		// Forget the layer first, so its removal event isn't taken as the sky map wiping it.
		const layer = contourLayer;
		const owner = layerOwner;
		contourLayer = null;
		layerOwner = null;
		if (layer && owner) owner.removeOverlay(layer);
	}

	function reset() {
		generation += 1;
		clearTimeout(timer);
		busy = false;
		waiting = '';
		message = '';
		failed = false;
		table = null;
	}

	function stop(text: string, isFailure: boolean) {
		busy = false;
		waiting = '';
		message = text;
		failed = isFailure;
	}

	async function request() {
		if (instrumentId === null) return;
		reset();
		const job = {
			gen: generation,
			graceid,
			id: instrumentId,
			avoidPlanned: excludePlanned,
			polls: 0
		};
		busy = true;
		try {
			// Avoiding planned pointings needs a fresh run first; Teglon reuses it if nothing changed.
			const step = job.avoidPlanned
				? afterRun(await teglon.startPlannedRun(job.graceid, job.id))
				: afterTable(await teglon.table(job.graceid, job.id, false));
			await follow(step, job);
		} catch {
			if (job.gen === generation) stop('Could not reach Treasure Map. Please try again.', true);
		}
	}

	interface Job {
		gen: number;
		graceid: string;
		id: number;
		avoidPlanned: boolean;
		polls: number;
	}

	async function follow(step: Step, job: Job) {
		if (job.gen !== generation) return;
		if (step.kind === 'ready') {
			busy = false;
			waiting = '';
			table = step.table;
		} else if (step.kind === 'stop') {
			stop(step.message, step.failed);
		} else if (step.kind === 'fetch') {
			await follow(afterTable(await teglon.table(job.graceid, job.id, job.avoidPlanned)), job);
		} else if (job.polls >= MAX_POLLS) {
			stop('Teglon is still working on this. Please try again in a few minutes.', false);
		} else {
			waiting = step.message;
			job.polls += 1;
			timer = setTimeout(async () => {
				try {
					await follow(afterRun(await teglon.run(step.taskId)), job);
				} catch {
					if (job.gen === generation) stop('Lost contact with Teglon. Please try again.', true);
				}
			}, POLL_MS);
		}
	}
</script>

{#if enabled}
	<div class="teglon-panel w-full max-w-sm space-y-3">
		<div class="border-b pb-2">
			<h3 class="text-lg font-semibold text-gray-900">Suggested Pointings</h3>
			<p class="text-xs text-gray-500">From Teglon, weighted by galaxies in the localization.</p>
		</div>

		{#if !$auth.isAuthenticated}
			<p class="text-sm text-gray-600">Log in to see suggested pointings.</p>
		{:else}
			<div class="space-y-2">
				<label class="block text-sm">
					<span class="text-gray-700">Instrument</span>
					<select
						bind:value={instrumentId}
						disabled={busy && !waiting}
						class="mt-1 block w-full border rounded px-2 py-1 text-sm"
					>
						<option value={null} disabled>Choose an instrument</option>
						{#each instruments as instrument (instrument.id)}
							<option value={instrument.id}>{instrument.name}</option>
						{/each}
					</select>
				</label>
				<label class="flex items-center gap-2 text-sm text-gray-700">
					<input type="checkbox" bind:checked={excludePlanned} disabled={busy && !waiting} />
					Avoid fields others have planned
				</label>
				<label class="flex items-center gap-2 text-sm text-gray-700">
					<input type="checkbox" bind:checked={showContours} />
					Show Teglon's contours on the map
				</label>
				{#if showContours}
					<p class="flex items-center gap-2 text-xs text-gray-600">
						<svg width="24" height="6" aria-hidden="true">
							<line
								x1="0"
								y1="3"
								x2="24"
								y2="3"
								stroke={CONTOUR_STYLE.color}
								stroke-width="2"
								stroke-dasharray={CONTOUR_STYLE.lineDash.join(' ')}
							/>
						</svg>
						Teglon's contours, with sky already observed{excludePlanned ? ' or planned' : ''} removed
					</p>
				{/if}
				<div class="text-xs text-gray-600" role="status">
					{#if contoursLoading}
						Loading contours…
					{:else if contourMessage}
						{contourMessage}
					{/if}
				</div>
				<button
					class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
					on:click={request}
					disabled={(busy && !waiting) || instrumentId === null}
				>
					Get suggested pointings
				</button>
			</div>

			<!-- Kept in the DOM so screen readers announce changes to it. -->
			<div
				class="text-sm"
				class:text-blue-700={waiting}
				class:text-gray-500={!waiting}
				role="status"
			>
				{#if waiting}
					{waiting} Checking again every {POLL_MS / 1000} seconds.
				{:else if busy}
					Loading…
				{/if}
			</div>

			{#if message}
				<p
					class="text-sm"
					class:text-red-700={failed}
					class:text-gray-600={!failed}
					role={failed ? 'alert' : null}
				>
					{message}
				</p>
			{/if}

			{#if table}
				{#if table.pointings.length === 0}
					<p class="text-sm text-gray-600">
						Teglon has no suggested pointings for this instrument.
					</p>
				{:else}
					<div class="max-h-64 overflow-y-auto border rounded">
						<table class="w-full text-xs">
							<caption class="sr-only">Suggested pointings, highest probability first</caption>
							<thead class="bg-gray-50 sticky top-0">
								<tr class="text-left text-gray-600">
									<th class="px-2 py-1">#</th>
									<th class="px-2 py-1">Field</th>
									<th class="px-2 py-1 text-right">RA (°)</th>
									<th class="px-2 py-1 text-right">Dec (°)</th>
									<th class="px-2 py-1 text-right">Prob</th>
									<th class="px-2 py-1 text-right"
										><abbr title="Cumulative probability">Cum.</abbr></th
									>
								</tr>
							</thead>
							<tbody>
								{#each table.pointings as pointing, i (i)}
									<tr class="border-t">
										<td class="px-2 py-1 text-gray-500">{i + 1}</td>
										<td class="px-2 py-1">{pointing.field_name ?? '—'}</td>
										<td class="px-2 py-1 text-right">{formatNumber(pointing.ra, 4)}</td>
										<td class="px-2 py-1 text-right">{formatNumber(pointing.dec, 4)}</td>
										<td class="px-2 py-1 text-right">{formatProbability(pointing.prob)}</td>
										<td class="px-2 py-1 text-right">{formatProbability(pointing.cum_prob)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
				<p class="text-xs text-gray-500">
					{table.pointings.length}
					{table.pointings.length === 1 ? 'field' : 'fields'}{table.detector
						? ` · ${table.detector}`
						: ''}{table.band ? ` · ${table.band} band` : ''} · map {table.healpix_file}{table.generated_at
						? ` · generated ${formatUtc(table.generated_at)}`
						: ''}
				</p>
			{/if}
		{/if}
	</div>
{/if}
