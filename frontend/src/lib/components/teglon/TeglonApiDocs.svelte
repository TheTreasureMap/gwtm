<script lang="ts">
	// API documentation for Teglon's suggested pointings. Shown only while the backend reports the
	// feature enabled, so the docs disappear with the routes when Teglon is switched off.
	import { onMount } from 'svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import { teglon } from './teglon';

	let enabled = false;
	let origin = 'https://treasuremap.space';

	onMount(async () => {
		origin = window.location.origin;
		try {
			enabled = await teglon.enabled();
		} catch {
			enabled = false;
		}
	});

	$: example = `import time
import requests

BASE = "${origin}/api/v1/teglon"
HEADERS = {"api_token": "YOUR_API_TOKEN"}


def body(r):
    """The JSON reply, or an error with whatever explanation the reply carries."""
    try:
        data = r.json()
    except ValueError:
        r.raise_for_status()  # a proxy or gateway error page rather than a JSON reply
        raise RuntimeError(f"Unexpected reply (HTTP {r.status_code}): {r.text[:200]}")
    return data if isinstance(data, dict) else {"data": data}


def explain(data):
    return data.get("message") or data.get("detail") or data


def suggested_pointings(graceid, instrument_id, exclude_planned=False):
    params = {"graceid": graceid, "instrument_id": instrument_id,
              "exclude_planned": str(exclude_planned).lower()}
    for _ in range(60):  # up to ten minutes
        r = requests.get(f"{BASE}/suggested_pointings", params=params, headers=HEADERS, timeout=30)
        data = body(r)
        if r.status_code == 200:
            return data["pointings"]  # highest probability first
        if r.status_code == 404 and data.get("state") in ("PENDING", "STARTED"):
            time.sleep(10)  # Teglon is setting this instrument up for the event
            continue
        raise RuntimeError(explain(data))
    raise TimeoutError("Teglon is still working; try again later")


for p in suggested_pointings("S251115a", 80):
    print(p["field_name"], p["ra"], p["dec"], p["prob"])`;

	const plannedExample = `def avoid_planned(graceid, instrument_id):
    params = {"graceid": graceid, "instrument_id": instrument_id}
    run = body(requests.post(f"{BASE}/planned_runs", params=params, headers=HEADERS, timeout=30))
    for _ in range(60):  # up to ten minutes
        if run.get("state") not in ("PENDING", "STARTED"):
            break
        time.sleep(10)
        run = body(requests.get(f"{BASE}/planned_runs/{run['task_id']}", headers=HEADERS, timeout=30))
    else:
        raise TimeoutError("Teglon is still working; try again later")
    if run.get("state") != "SUCCESS":  # failed, or the request itself was refused
        raise RuntimeError(run.get("error") or explain(run))
    return suggested_pointings(graceid, instrument_id, exclude_planned=True)


pointings = avoid_planned("S251115a", 80)`;
</script>

{#if enabled}
	<Card>
		<h2 class="text-2xl font-semibold mb-2">Suggested Pointings (Teglon)</h2>
		<p class="mb-6 text-gray-700">
			Teglon ranks fields for a GW event and one of your instruments, weighting the localization by
			galaxies and skipping sky that has already been covered. The same suggestions are shown on
			each alert page; these routes let your scripts fetch them.
		</p>

		<div class="space-y-6">
			<div>
				<h3 class="text-xl font-semibold text-blue-600 mb-3">Authentication and identifiers</h3>
				<ul class="list-disc list-inside space-y-1 text-sm">
					<li>
						Send your API token in an <code class="bg-gray-100 px-1 rounded">api_token</code> header,
						as for other API routes.
					</li>
					<li>
						<code class="bg-gray-100 px-1 rounded">graceid</code> is the event id; alternate names
						such as <code class="bg-gray-100 px-1 rounded">GW190425</code> are accepted.
					</li>
					<li>
						<code class="bg-gray-100 px-1 rounded">instrument_id</code> is the Treasure Map instrument
						id, the same one you use when submitting pointings. Only photometric instruments are supported.
					</li>
				</ul>
			</div>

			<div>
				<h3 class="text-xl font-semibold text-blue-600 mb-3">Routes</h3>
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead class="bg-gray-50 text-left">
							<tr>
								<th class="px-3 py-2">Route</th>
								<th class="px-3 py-2">Returns</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							<tr>
								<td class="px-3 py-2 font-mono text-xs"
									>GET
									/api/v1/teglon/suggested_pointings?graceid=&amp;instrument_id=&amp;exclude_planned=false</td
								>
								<td class="px-3 py-2"
									>The suggested fields, or a 404 explaining why not (see below).</td
								>
							</tr>
							<tr>
								<td class="px-3 py-2 font-mono text-xs"
									>POST /api/v1/teglon/planned_runs?graceid=&amp;instrument_id=</td
								>
								<td class="px-3 py-2"
									>Starts a run that also avoids fields others have planned. Returns the run.</td
								>
							</tr>
							<tr>
								<td class="px-3 py-2 font-mono text-xs"
									>GET /api/v1/teglon/planned_runs/{'{task_id}'}</td
								>
								<td class="px-3 py-2">A run's status.</td>
							</tr>
							<tr>
								<td class="px-3 py-2 font-mono text-xs"
									>GET /api/v1/teglon/contours?graceid=&amp;include_planned=false</td
								>
								<td class="px-3 py-2"
									>Localization contours adjusted for the sky already covered:
									<code class="bg-gray-100 px-1 rounded">detection_overlays</code>, each with
									<code class="bg-gray-100 px-1 rounded">contours</code> whose
									<code class="bg-gray-100 px-1 rounded">polygon</code> is a list of [RA, Dec] in degrees.</td
								>
							</tr>
						</tbody>
					</table>
				</div>
			</div>

			<div>
				<h3 class="text-xl font-semibold text-blue-600 mb-3">Reading the replies</h3>
				<ul class="list-disc list-inside space-y-1 text-sm">
					<li>
						<strong>200</strong>: a table with
						<code class="bg-gray-100 px-1 rounded">pointings</code>, each having
						<code class="bg-gray-100 px-1 rounded">field_name</code>,
						<code class="bg-gray-100 px-1 rounded">ra</code>,
						<code class="bg-gray-100 px-1 rounded">dec</code> (degrees),
						<code class="bg-gray-100 px-1 rounded">prob</code> and
						<code class="bg-gray-100 px-1 rounded">cum_prob</code>, highest probability first.
						Missing values are <code class="bg-gray-100 px-1 rounded">null</code>.
					</li>
					<li>
						<strong>404 with a <code class="bg-gray-100 px-1 rounded">task_id</code></strong>: the
						first request for an event and instrument starts a setup run.
						<code class="bg-gray-100 px-1 rounded">state</code> is
						<code class="bg-gray-100 px-1 rounded">PENDING</code> or
						<code class="bg-gray-100 px-1 rounded">STARTED</code> while it runs; ask again every 10
						seconds. A <code class="bg-gray-100 px-1 rounded">FAILURE</code> is reported for an hour
						before Teglon retries.
					</li>
					<li>
						<strong>404 without a <code class="bg-gray-100 px-1 rounded">task_id</code></strong>:
						Teglon can't help yet, for example because it hasn't processed the event. The
						<code class="bg-gray-100 px-1 rounded">message</code> says why.
					</li>
					<li>
						<strong>502 or 504</strong>: Teglon is unavailable or slow. Errors from these routes
						carry a
						<code class="bg-gray-100 px-1 rounded">message</code>; a few, such as a route that
						doesn't exist, carry <code class="bg-gray-100 px-1 rounded">detail</code> instead, and a
						gateway error may not be JSON at all. The examples handle all three.
					</li>
				</ul>
			</div>

			<div>
				<h3 class="text-xl font-semibold text-blue-600 mb-3">Example: fetch suggested pointings</h3>
				<div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
					<pre class="text-green-400 text-sm"><code>{example}</code></pre>
				</div>
			</div>

			<div>
				<h3 class="text-xl font-semibold text-blue-600 mb-3">
					Example: avoid fields others have planned
				</h3>
				<p class="text-sm mb-3">
					Start a planned run, wait for it, then ask for the table with
					<code class="bg-gray-100 px-1 rounded">exclude_planned=true</code>. Teglon reuses its last
					run if the event's pointings haven't changed since.
				</p>
				<div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
					<pre class="text-green-400 text-sm"><code>{plannedExample}</code></pre>
				</div>
			</div>

			<div class="bg-gray-50 rounded p-4 text-sm">
				<p class="font-semibold mb-1">Please be gentle</p>
				<p>
					Teglon works out one table at a time, so poll no faster than every 10 seconds. Requests
					for the same event and instrument share one run, and finished tables come back
					immediately.
				</p>
			</div>
		</div>
	</Card>
{/if}
