<script lang="ts">
	import type { InstrumentSchema } from '$lib/api';

	export let instruments: InstrumentSchema[] = [];
	export let loading: boolean = false;

	$: stats = calculateStats(instruments);

	function calculateStats(instruments: InstrumentSchema[]) {
		const total = instruments.length;
		const typeCount: Record<number, number> = {};
		let recentCount = 0;

		const thirtyDaysAgo = new Date();
		thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

		instruments.forEach((instrument) => {
			// Count by type
			typeCount[instrument.instrument_type] = (typeCount[instrument.instrument_type] || 0) + 1;

			// Count recent instruments
			if (instrument.datecreated) {
				const createdDate = new Date(instrument.datecreated);
				if (createdDate >= thirtyDaysAgo) {
					recentCount++;
				}
			}
		});

		const mostCommonType = Object.entries(typeCount).sort(([, a], [, b]) => b - a)[0];

		return {
			total,
			recentCount,
			typeCount,
			mostCommonType: mostCommonType
				? {
						type: parseInt(mostCommonType[0]),
						count: mostCommonType[1]
					}
				: null
		};
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

<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
	<!-- Total Instruments -->
	<div class="bg-white rounded-lg shadow-lg p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<svg class="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
					/>
				</svg>
			</div>
			<div class="ml-4">
				<div class="text-sm font-medium text-gray-500">Total Instruments</div>
				<div class="text-2xl font-bold text-gray-900">
					{#if loading}
						<div class="animate-pulse bg-gray-200 h-8 w-16 rounded"></div>
					{:else}
						{stats.total}
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- Recent Additions -->
	<div class="bg-white rounded-lg shadow-lg p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 4v16m8-8H4"
					/>
				</svg>
			</div>
			<div class="ml-4">
				<div class="text-sm font-medium text-gray-500">Added (30 days)</div>
				<div class="text-2xl font-bold text-gray-900">
					{#if loading}
						<div class="animate-pulse bg-gray-200 h-8 w-16 rounded"></div>
					{:else}
						{stats.recentCount}
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- Most Common Type -->
	<div class="bg-white rounded-lg shadow-lg p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<svg class="h-8 w-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
					/>
				</svg>
			</div>
			<div class="ml-4">
				<div class="text-sm font-medium text-gray-500">Most Common Type</div>
				<div class="text-lg font-bold text-gray-900">
					{#if loading}
						<div class="animate-pulse bg-gray-200 h-6 w-24 rounded"></div>
					{:else if stats.mostCommonType}
						<span class="block truncate">
							{getInstrumentTypeLabel(stats.mostCommonType.type)}
						</span>
						<span class="text-sm text-gray-500">({stats.mostCommonType.count})</span>
					{:else}
						<span class="text-gray-400">N/A</span>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- Active Status -->
	<div class="bg-white rounded-lg shadow-lg p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<svg class="h-8 w-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M13 10V3L4 14h7v7l9-11h-7z"
					/>
				</svg>
			</div>
			<div class="ml-4">
				<div class="text-sm font-medium text-gray-500">Reporting Status</div>
				<div class="text-lg font-bold text-green-600">
					{#if loading}
						<div class="animate-pulse bg-gray-200 h-6 w-16 rounded"></div>
					{:else}
						Active
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>
