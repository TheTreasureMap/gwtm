<script lang="ts">
	import { page } from '$app/stores';
	import { gwtmApi, type InstrumentSchema, type GWAlertSchema } from '$lib/api';
	import { onMount } from 'svelte';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import FootprintVisualization from '$lib/components/ui/FootprintVisualization.svelte';

	let instrument: InstrumentSchema | null = null;
	let eventsContributed: GWAlertSchema[] = [];
	let loading = true;
	let eventsLoading = false;
	let error: string | null = null;
	let eventsError: string | null = null;

	$: instrumentId = parseInt($page.params.id);

	onMount(() => {
		loadInstrument();
	});

	async function loadInstrument() {
		if (!instrumentId || isNaN(instrumentId)) {
			error = 'Invalid instrument ID';
			loading = false;
			return;
		}

		try {
			loading = true;
			error = null;
			const instruments = await gwtmApi.getInstruments({ id: instrumentId });

			if (instruments.length === 0) {
				error = 'Instrument not found';
			} else {
				instrument = instruments[0];
				// Load events contributed after instrument is loaded
				loadEventsContributed();
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load instrument';
			console.error('Error loading instrument:', err);
		} finally {
			loading = false;
		}
	}

	async function loadEventsContributed() {
		if (!instrumentId) return;

		try {
			eventsLoading = true;
			eventsError = null;
			eventsContributed = await gwtmApi.getInstrumentEventsContributed(instrumentId);
		} catch (err) {
			eventsError = err instanceof Error ? err.message : 'Failed to load events contributed';
			console.error('Error loading events contributed:', err);
		} finally {
			eventsLoading = false;
		}
	}

	function getInstrumentTypeLabel(type: number): string {
		const typeMap: Record<number, string> = {
			1: 'Photometric',
			2: 'Spectroscopic',
			3: 'Gravitational Wave',
			4: 'Radio',
			5: 'X-ray',
			6: 'Gamma-ray',
			7: 'Neutrino'
		};
		return typeMap[type] || `Type ${type}`;
	}
</script>

<svelte:head>
	<title>{instrument ? instrument.instrument_name : 'Instrument Info'} - GWTM</title>
</svelte:head>

<PageContainer>
	<PageHeader
		title={instrument ? instrument.instrument_name : loading ? 'Loading...' : 'Instrument Info'}
		description="Instrument details and footprint information"
	/>

	{#if loading}
		<LoadingSpinner message="Loading instrument information..." />
	{:else if error}
		<ErrorMessage message={error} title="Error Loading Instrument" type="error" />
	{:else if instrument}
		<!-- Flask-style two-column layout -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
			<!-- Left Column: Basic Info + Events Contributed -->
			<div>
				<!-- Basic Information -->
				<Card class="mb-6">
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Basic Information</h2>

					<div class="space-y-3">
						<div>
							<span class="font-medium text-gray-700">Name:</span>
							<span class="ml-2">{instrument.instrument_name}</span>
						</div>

						{#if instrument.nickname}
							<div>
								<span class="font-medium text-gray-700">Short Name:</span>
								<span class="ml-2">{instrument.nickname}</span>
							</div>
						{/if}

						<div>
							<span class="font-medium text-gray-700">Type:</span>
							<span class="ml-2">{getInstrumentTypeLabel(instrument.instrument_type)}</span>
						</div>

						<div>
							<span class="font-medium text-gray-700">Submitted User:</span>
							<span class="ml-2">User #{instrument.submitterid || 'Unknown'}</span>
						</div>
					</div>
				</Card>

				<!-- Events Contributed -->
				<Card>
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Events Contributed</h2>

					{#if eventsLoading}
						<LoadingSpinner size="sm" message="Loading events..." />
					{:else if eventsError}
						<ErrorMessage message={eventsError} title="Error Loading Events" type="error" />
					{:else if eventsContributed.length === 0}
						<p class="text-gray-500 italic">No completed pointings found for this instrument.</p>
					{:else}
						<div class="overflow-x-auto">
							<table class="w-full border-collapse border border-gray-300">
								<thead>
									<tr class="bg-gray-50">
										<th class="border border-gray-300 px-3 py-2 text-left font-medium">Grace ID</th>
										<th class="border border-gray-300 px-3 py-2 text-left font-medium">Pointings</th
										>
									</tr>
								</thead>
								<tbody>
									{#each eventsContributed as event (event.graceid)}
										<tr class="hover:bg-gray-50">
											<td class="border border-gray-300 px-3 py-2">
												<a
													href="/alerts?graceids={event.graceid}"
													class="text-blue-600 hover:text-blue-800 underline"
												>
													{event.graceid}
												</a>
											</td>
											<td class="border border-gray-300 px-3 py-2 text-center">
												{event.pointing_count || 0}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</Card>
			</div>

			<!-- Right Column: Footprint Visualization -->
			<div>
				<Card>
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Footprint Visualization</h2>
					<FootprintVisualization {instrumentId} />
				</Card>
			</div>
		</div>
	{/if}
</PageContainer>
