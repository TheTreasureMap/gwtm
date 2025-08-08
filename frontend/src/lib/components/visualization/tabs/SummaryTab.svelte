<!--
@component SummaryTab
@description Summary tab component for Event Explorer displaying alert information
@category Visualization Components
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<SummaryTab {selectedAlert} />
```

@prop {GWAlertSchema | null} selectedAlert - The selected gravitational wave alert
-->
<script lang="ts">
	import type { GWAlertSchema } from '$lib/api';

	// Extended interface for processed alert data with Flask-compatible fields
	interface ProcessedGWAlert extends GWAlertSchema {
		far_human?: string;
		distance_with_error?: string;
	}

	/**
	 * The selected gravitational wave alert
	 * @type {GWAlertSchema | null}
	 * @default null
	 */
	export let selectedAlert: ProcessedGWAlert | null = null;

	// Format date for display
	function formatDate(dateString: string | null): string {
		if (!dateString) return 'N/A';
		return new Date(dateString).toISOString().replace('T', ' ').replace('Z', ' UTC');
	}

	// Format distance with error
	function formatDistance(distance: number | null, error: number | null): string {
		if (distance === null || distance === undefined || error === null || error === undefined) {
			return 'N/A';
		}
		return `${distance.toFixed(3)} +/- ${error.toFixed(3)} Mpc`;
	}

	// Format false alarm rate (convert from Hz to human-readable)
	function formatFalseAlarmRate(far: number | null): string {
		if (!far || far <= 0) return 'N/A';

		// Convert Hz to human-readable format using Flask algorithm
		let farrate = 1 / far;
		let farunit = 's';

		if (farrate > 86400) {
			farunit = 'days';
			farrate /= 86400;
			if (farrate > 365) {
				farrate /= 365.25;
				farunit = 'years';
			} else if (farrate > 30) {
				farrate /= 30;
				farunit = 'months';
			} else if (farrate > 7) {
				farrate /= 7;
				farunit = 'weeks';
			}
		}

		return `once per ${farrate.toFixed(2)} ${farunit}`;
	}

	$: isBurst = selectedAlert?.group === 'Burst';
</script>

<div class="tab-pane active p-6" id="calc-info-content" role="tabpanel" aria-labelledby="tab-info">
	<div class="container-fluid">
		<div class="grid md:grid-cols-2 gap-8">
			<!-- Left Column: Alert Information -->
			<div class="space-y-4">
				<h3 class="text-lg font-semibold text-gray-900 mb-4">Alert Information</h3>

				<div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
					<table class="min-w-full divide-y divide-gray-200">
						<tbody class="bg-white divide-y divide-gray-200">
							{#if selectedAlert?.group && selectedAlert.group !== 'None' && selectedAlert.group !== ''}
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Group
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_group">
										{selectedAlert.group}
									</td>
								</tr>
							{/if}

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									Detectors
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_detectors">
									{selectedAlert?.detectors || 'N/A'}
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									Time of Signal
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_time_of_signal">
									{formatDate(selectedAlert?.time_of_signal ?? null)}
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									Time Sent
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_timesent">
									{formatDate(selectedAlert?.timesent ?? null)}
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									False Alarm Rate
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_human_far">
									{selectedAlert?.far_human || formatFalseAlarmRate(selectedAlert?.far ?? null)}
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									50% Area
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_area_50">
									{#if typeof selectedAlert?.area_50 === 'string'}
										{@html selectedAlert.area_50}
									{:else if selectedAlert?.area_50}
										{selectedAlert.area_50.toFixed(3)} deg<sup>2</sup>
									{:else}
										None
									{/if}
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									90% Area
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_area_90">
									{#if typeof selectedAlert?.area_90 === 'string'}
										{@html selectedAlert.area_90}
									{:else if selectedAlert?.area_90}
										{selectedAlert.area_90.toFixed(3)} deg<sup>2</sup>
									{:else}
										None
									{/if}
								</td>
							</tr>

							{#if !isBurst}
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Distance
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_distance_plus_error">
										{selectedAlert?.distance_with_error ||
											formatDistance(selectedAlert?.distance ?? null, selectedAlert?.distance_error ?? null)}
									</td>
								</tr>
							{:else}
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Central Frequency
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_centralfreq">
										{selectedAlert?.centralfreq || 'N/A'} Hz
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Duration
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_duration">
										{selectedAlert?.duration || 'N/A'} seconds
									</td>
								</tr>
							{/if}
						</tbody>
					</table>
				</div>
			</div>

			<!-- Right Column: Classification (CBC Only) -->
			{#if !isBurst}
				<div class="space-y-4">
					<h3 class="text-lg font-semibold text-gray-900 mb-4">Classification (CBC Only)</h3>

					<div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
						<table class="min-w-full divide-y divide-gray-200">
							<tbody class="bg-white divide-y divide-gray-200">
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										BNS
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_bns">
										{selectedAlert?.prob_bns !== null && selectedAlert?.prob_bns !== undefined
											? selectedAlert.prob_bns
											: 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										NSBH
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_nsbh">
										{selectedAlert?.prob_nsbh !== null && selectedAlert?.prob_nsbh !== undefined
											? selectedAlert.prob_nsbh
											: 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Mass Gap
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_gap">
										{selectedAlert?.prob_gap !== null && selectedAlert?.prob_gap !== undefined
											? selectedAlert.prob_gap
											: 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										BBH
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_bbh">
										{selectedAlert?.prob_bbh !== null && selectedAlert?.prob_bbh !== undefined
											? selectedAlert.prob_bbh
											: 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Terrestrial
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_terrestrial">
										{selectedAlert?.prob_terrestrial !== null &&
										selectedAlert?.prob_terrestrial !== undefined
											? selectedAlert.prob_terrestrial
											: 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Has NS
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_hasns">
										{selectedAlert?.prob_hasns !== null && selectedAlert?.prob_hasns !== undefined
											? selectedAlert.prob_hasns
											: 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Has Remnant
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_hasremenant">
										{selectedAlert?.prob_hasremenant !== null &&
										selectedAlert?.prob_hasremenant !== undefined
											? selectedAlert.prob_hasremenant
											: 'N/A'}
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
