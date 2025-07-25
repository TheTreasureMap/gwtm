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

	/**
	 * The selected gravitational wave alert
	 * @type {GWAlertSchema | null}
	 * @default null
	 */
	export let selectedAlert: GWAlertSchema | null = null;

	// Format date for display
	function formatDate(dateString: string | null): string {
		if (!dateString) return 'N/A';
		return new Date(dateString).toISOString().replace('T', ' ').replace('Z', ' UTC');
	}

	// Format distance with error
	function formatDistance(distance: number | null, error: number | null): string {
		if (!distance || !error) return 'N/A';
		return `${distance} +/- ${error} Mpc`;
	}

	// Format false alarm rate
	function formatFalseAlarmRate(far: string | null, unit: string | null): string {
		if (!far) return 'N/A';
		return `once per ${far} ${unit || 'years'}`;
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
									{formatDate(selectedAlert?.time_of_signal)}
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									Time Sent
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_timesent">
									{formatDate(selectedAlert?.timesent)}
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									False Alarm Rate
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_human_far">
									{formatFalseAlarmRate(selectedAlert?.human_far, selectedAlert?.human_far_unit)}
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									50% Area
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_area_50">
									{selectedAlert?.area_50 || 'N/A'} deg<sup>2</sup>
								</td>
							</tr>

							<tr class="hover:bg-gray-50">
								<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
									90% Area
								</td>
								<td class="px-6 py-3 text-sm text-gray-700" id="alert_area_90">
									{selectedAlert?.area_90 || 'N/A'} deg<sup>2</sup>
								</td>
							</tr>

							{#if !isBurst}
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Distance
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_distance_plus_error">
										{formatDistance(selectedAlert?.distance, selectedAlert?.distance_error)}
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
										{selectedAlert?.prob_bns || 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										NSBH
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_nsbh">
										{selectedAlert?.prob_nsbh || 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Mass Gap
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_gap">
										{selectedAlert?.prob_gap || 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										BBH
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_bbh">
										{selectedAlert?.prob_bbh || 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Terrestrial
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_terrestrial">
										{selectedAlert?.prob_terrestrial || 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Has NS
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_hasns">
										{selectedAlert?.prob_hasns || 'N/A'}
									</td>
								</tr>

								<tr class="hover:bg-gray-50">
									<td class="px-6 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">
										Has Remnant
									</td>
									<td class="px-6 py-3 text-sm text-gray-700" id="alert_prob_hasremenant">
										{selectedAlert?.prob_hasremenant || 'N/A'}
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
