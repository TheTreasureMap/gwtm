<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { GWAlertSchema } from '$lib/api.js';

	export let selectedAlert: GWAlertSchema | null = null;
	export let loading: boolean = false;
	export let error: string = '';
	export let plotlyContainer: HTMLDivElement | null = null;

	const dispatch = createEventDispatcher();

	let currentTab = 'info'; // 'info', 'coverage', 'renorm'

	function calculateCoverage() {
		dispatch('calculateCoverage');
	}

	function visualizeRenormalizedSkymap() {
		dispatch('visualizeRenormalizedSkymap');
	}

	function downloadRenormalizedSkymap() {
		dispatch('downloadRenormalizedSkymap');
	}
</script>

{#if !loading && !error}
	<!-- Event Explorer Tabs (exactly matching Flask) -->
	<div class="bg-white border rounded-lg overflow-hidden mt-4">
		<!-- Tab Navigation (matching Flask Bootstrap nav-tabs) -->
		<ul class="nav nav-tabs flex border-b border-gray-200 bg-gray-50">
			<li class="nav-item px-4 py-3">
				<span class="nav-link disabled text-sm font-medium text-gray-500" style="font-weight: bold;"
					>Event Explorer:</span
				>
			</li>
			<li class="nav-item cursor-pointer">
				<button
					class="nav-link px-4 py-3 text-sm font-medium border-b-2 transition-colors
						{currentTab === 'info'
						? 'text-blue-600 border-blue-600 bg-white'
						: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
					on:click={() => (currentTab = 'info')}
				>
					Summary
				</button>
			</li>
			<li class="nav-item cursor-pointer">
				<button
					class="nav-link px-4 py-3 text-sm font-medium border-b-2 transition-colors
						{currentTab === 'coverage'
						? 'text-blue-600 border-blue-600 bg-white'
						: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
					on:click={() => (currentTab = 'coverage')}
				>
					Coverage Calculator
				</button>
			</li>
			<li class="nav-item cursor-pointer">
				<button
					class="nav-link px-4 py-3 text-sm font-medium border-b-2 transition-colors
						{currentTab === 'renorm'
						? 'text-blue-600 border-blue-600 bg-white'
						: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
					on:click={() => (currentTab = 'renorm')}
				>
					Renormalize Skymap
				</button>
			</li>
		</ul>

		<!-- Tab Content -->
		<div class="tab-content p-6">
			{#if currentTab === 'info'}
				<!-- Summary Tab (matching Flask exactly) -->
				<div class="tab-pane active" id="calc-info-content">
					<div class="container-fluid">
						<div class="row flex flex-wrap">
							<!-- Left Column: Alert Information -->
							<div class="col-sm-6 w-1/2 pr-4">
								<table class="table w-full border-collapse">
									<thead>
										<tr class="border-b">
											<th class="text-left py-2 font-semibold">Information</th>
											<th class="text-left py-2"></th>
										</tr>
									</thead>
									<tbody>
										{#if selectedAlert?.group && selectedAlert.group !== 'None' && selectedAlert.group !== ''}
											<tr class="alert-info border-b">
												<td class="py-2">Group</td>
												<td class="py-2" id="alert_group">{selectedAlert.group}</td>
											</tr>
										{/if}
										<tr class="alert-info border-b">
											<td class="py-2">Detectors</td>
											<td class="py-2" id="alert_detectors">{selectedAlert?.detectors || 'N/A'}</td>
										</tr>
										<tr class="alert-info border-b">
											<td class="py-2">Time of Signal</td>
											<td class="py-2" id="alert_time_of_signal">
												{selectedAlert?.time_of_signal
													? new Date(selectedAlert.time_of_signal)
															.toISOString()
															.replace('T', ' ')
															.replace('Z', ' UTC')
													: 'N/A'}
											</td>
										</tr>
										<tr class="alert-info border-b">
											<td class="py-2">Time Sent</td>
											<td class="py-2" id="alert_timesent">
												{selectedAlert?.timesent
													? new Date(selectedAlert.timesent)
															.toISOString()
															.replace('T', ' ')
															.replace('Z', ' UTC')
													: 'N/A'}
											</td>
										</tr>
										<tr class="alert-info border-b">
											<td class="py-2">False Alarm Rate</td>
											<td class="py-2" id="alert_human_far">
												{#if selectedAlert?.human_far}
													once per {selectedAlert.human_far}
													{selectedAlert.human_far_unit || 'years'}
												{:else}
													N/A
												{/if}
											</td>
										</tr>
										<tr class="alert-info border-b">
											<td class="py-2">50% Area</td>
											<td class="py-2" id="alert_area_50"
												>{selectedAlert?.area_50 || 'N/A'} deg<sup>2</sup></td
											>
										</tr>
										<tr class="alert-info border-b">
											<td class="py-2">90% Area</td>
											<td class="py-2" id="alert_area_90"
												>{selectedAlert?.area_90 || 'N/A'} deg<sup>2</sup></td
											>
										</tr>
										{#if selectedAlert?.group !== 'Burst'}
											<tr class="alert-info border-b">
												<td class="py-2">Distance</td>
												<td class="py-2" id="alert_distance_plus_error">
													{#if selectedAlert?.distance && selectedAlert?.distance_error}
														{selectedAlert.distance} +/- {selectedAlert.distance_error} Mpc
													{:else}
														N/A
													{/if}
												</td>
											</tr>
										{:else}
											<tr class="alert-info border-b">
												<td class="py-2">Central Frequency</td>
												<td class="py-2" id="alert_centralfreq"
													>{selectedAlert?.centralfreq || 'N/A'} Hz</td
												>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">Duration</td>
												<td class="py-2" id="alert_duration"
													>{selectedAlert?.duration || 'N/A'} seconds</td
												>
											</tr>
										{/if}
									</tbody>
								</table>
							</div>

							<!-- Right Column: Classification (CBC Only) -->
							{#if selectedAlert?.group !== 'Burst'}
								<div class="col-sm-6 w-1/2 pl-4">
									<table class="table w-full border-collapse">
										<thead>
											<tr class="border-b">
												<th class="text-left py-2 font-semibold">Classification (CBC Only)</th>
												<th class="text-left py-2"></th>
											</tr>
										</thead>
										<tbody>
											<tr class="alert-info border-b">
												<td class="py-2">BNS</td>
												<td class="py-2" id="alert_prob_bns">{selectedAlert?.prob_bns || 'N/A'}</td>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">NSBH</td>
												<td class="py-2" id="alert_prob_nsbh"
													>{selectedAlert?.prob_nsbh || 'N/A'}</td
												>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">Mass Gap</td>
												<td class="py-2" id="alert_prob_gap">{selectedAlert?.prob_gap || 'N/A'}</td>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">BBH</td>
												<td class="py-2" id="alert_prob_bbh">{selectedAlert?.prob_bbh || 'N/A'}</td>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">Terrestrial</td>
												<td class="py-2" id="alert_prob_terrestrial"
													>{selectedAlert?.prob_terrestrial || 'N/A'}</td
												>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">Has NS</td>
												<td class="py-2" id="alert_prob_hasns"
													>{selectedAlert?.prob_hasns || 'N/A'}</td
												>
											</tr>
											<tr class="alert-info border-b">
												<td class="py-2">Has Remnant</td>
												<td class="py-2" id="alert_prob_hasremenant"
													>{selectedAlert?.prob_hasremenant || 'N/A'}</td
												>
											</tr>
										</tbody>
									</table>
								</div>
							{/if}
						</div>
					</div>
				</div>
			{:else if currentTab === 'coverage'}
				<!-- Coverage Calculator Tab (matching Flask exactly) -->
				<div class="tab-pane" id="calc-coverage-content">
					<div class="container-fluid">
						<center
							><h3 class="text-xl font-semibold" style="margin-top: 2rem;">
								Coverage Calculator
							</h3></center
						>

						<br />

						<i class="text-sm text-gray-700 block mb-4">
							Calculate the coverage of the GW localization over time, with choices to limit the
							coverage calculation to particular sets of instruments, wavelengths, or depth. All
							fields are optional, but cuts on depths must have an associated unit. If an empty form
							is submitted, the total reported coverage regardless of depth or band is computed.
							Once a HEALPIX pixel has been first covered, it is marked as done, to avoid double
							counting probability when the same field is covered multiple times. After clicking
							Calculate, be patient, it may take up to 2 minutes to fully compute the coverage
							profile.
						</i>
						<p class="text-red-600 text-sm mb-4">
							Disclaimer: The DECam Footprint currently breaks in the calculator. We are temporarily
							approximating its coverage as a circle with 1 deg radius.
						</p>

						<br />

						<!-- Coverage plot placeholder -->
						<div id="coveragediv" bind:this={plotlyContainer}></div>

						<!-- Coverage plot input parameters -->
						<div class="flex flex-wrap gap-4 mb-4">
							<div class="inline-block whitespace-nowrap">
								<b>Instrument</b>
								<select class="ml-2 px-2 py-1 border rounded" multiple id="inst_cov">
									<!-- Instrument options would be populated from API -->
									<option value="all">All Instruments</option>
								</select>
							</div>

							<div class="inline-block whitespace-nowrap">
								<b class="tooltip-container">
									Approximate
									<span class="tooltip-text">
										For footprints with multiple ccd's this will approximate the calculator's input
										by using a simplified instrument footprint without chip-gaps. It is
										substantially faster, but does introduce a level of uncertainty in the resulting
										area and probability.
									</span>
								</b>
								<select class="ml-2 px-2 py-1 border rounded" id="approx_cov">
									<option value="1" selected>Yes</option>
									<option value="0">No</option>
								</select>
							</div>

							<div class="inline-block whitespace-nowrap">
								<b>Depth</b>
								<input
									type="text"
									size="7"
									class="ml-2 px-2 py-1 border rounded"
									id="depth_cov"
									placeholder="Optional"
								/>
								<b class="ml-2">Depth Unit</b>
								<select class="ml-2 px-2 py-1 border rounded" id="depth_unit">
									<option value="">Select Unit</option>
									<option value="mag">Magnitude</option>
									<option value="flux">FLUX erg cm^-2 s^-1</option>
								</select>
							</div>

							<div class="inline-block whitespace-nowrap">
								<b>Band</b>
								<select class="ml-2 px-2 py-1 border rounded" multiple id="band_cov">
									<option value="">All Bands</option>
									<option value="g">g</option>
									<option value="r">r</option>
									<option value="i">i</option>
								</select>
							</div>

							<div class="inline-block whitespace-nowrap">
								<b class="tooltip-container">
									Spectral Range
									<span class="tooltip-text">
										Filter pointings based on their wavelength, energy, or frequency range
									</span>
								</b>
								<b class="ml-2">Type:</b>
								<select class="ml-1 px-2 py-1 border rounded" id="spectral_range_type">
									<option value="wavelength" selected>Wavelength</option>
									<option value="energy">Energy</option>
									<option value="frequency">Frequency</option>
								</select>
								<b class="ml-2">Range:</b>
								<input
									size="10"
									type="text"
									class="ml-1 px-1 py-1 border rounded"
									id="spectral_range_low"
									placeholder="Min"
								/>
								-
								<input
									size="10"
									type="text"
									class="ml-1 px-1 py-1 border rounded"
									id="spectral_range_high"
									placeholder="Max"
								/>
								<b class="ml-2">Unit</b>
								<select class="ml-1 px-2 py-1 border rounded" id="spectral_range_unit">
									<option value="nm">nm</option>
									<option value="angstrom">Angstrom</option>
								</select>
							</div>
						</div>

						<br /><br />
						<div class="flex justify-center">
							<button
								class="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
								on:click={calculateCoverage}
							>
								Calculate
							</button>
						</div>
					</div>
				</div>
			{:else if currentTab === 'renorm'}
				<!-- Renormalize Skymap Tab (matching Flask exactly) -->
				<div class="tab-pane" id="calc-renorm-skymap-content">
					<div class="container-fluid">
						<center
							><h3 class="text-xl font-semibold" style="margin-top: 2rem;">
								Renormalize Skymap
							</h3></center
						>

						<br />

						<i class="text-sm text-gray-700 block mb-4">
							Removes pointings from the GW skymap and renormalizes the remaining probability mass,
							with choices to select particular sets of instruments, and/or pointings that cover
							certain wavelengths or depth. All fields are optional, but cuts on depths must have an
							associated unit. If an empty form is submitted, all completed pointings regardless of
							depth or band are removed from the skymap. Once a HEALPIX pixel has been first
							covered, it is marked as done, to avoid double counting probability when the same
							field is covered multiple times. After clicking Download, be patient, it may take up
							to 3 minutes to fully compute the renormalized skymap and download the HEALPIX fits
							file. Click Visualize to replace the 50% and 90% localization contours in the figure
							above with ones calculated from the renormalized skymap.
						</i>
						<p class="text-red-600 text-sm mb-4">
							Disclaimer: The DECam Footprint currently breaks in the calculator. We are temporarily
							approximating its coverage as a circle with 1 deg radius.
						</p>

						<br />

						<!-- Renorm skymap input parameters -->
						<div class="flex flex-wrap gap-4 mb-4">
							<div class="inline-block whitespace-nowrap">
								<b class="tooltip-container">
									Instrument:
									<span class="tooltip-text">
										Completed and planned pointings to include from each instrument
									</span>
								</b>
								<b class="ml-2">Completed</b>
								<select class="ml-2 px-2 py-1 border rounded" multiple id="r_inst_cov">
									<option value="all">All Instruments</option>
								</select>
								<b class="ml-2">Planned</b>
								<select class="ml-2 px-2 py-1 border rounded" multiple id="r_inst_plan">
									<option value="all">All Instruments</option>
								</select>
							</div>

							<div class="inline-block whitespace-nowrap">
								<b class="tooltip-container">
									Approximate
									<span class="tooltip-text">
										For footprints with multiple ccd's this will approximate the calculator's input
										by using a simplified instrument footprint without chip-gaps. It is
										substantially faster, but does introduce a level of uncertainty in the resulting
										area and probability.
									</span>
								</b>
								<select class="ml-2 px-2 py-1 border rounded" id="r_approx_cov">
									<option value="1" selected>Yes</option>
									<option value="0">No</option>
								</select>
							</div>

							<div class="inline-block whitespace-nowrap">
								<b>Depth</b>
								<input
									type="text"
									size="7"
									class="ml-2 px-2 py-1 border rounded"
									id="r_depth_cov"
									placeholder="Optional"
								/>
								<b class="ml-2">Depth Unit</b>
								<select class="ml-2 px-2 py-1 border rounded" id="r_depth_unit">
									<option value="">Select Unit</option>
									<option value="mag">Magnitude</option>
									<option value="flux">FLUX erg cm^-2 s^-1</option>
								</select>
							</div>

							<div class="inline-block whitespace-nowrap">
								<b>Band</b>
								<select class="ml-2 px-2 py-1 border rounded" multiple id="r_band_cov">
									<option value="">All Bands</option>
									<option value="g">g</option>
									<option value="r">r</option>
									<option value="i">i</option>
								</select>
							</div>

							<div class="inline-block whitespace-nowrap">
								<b class="tooltip-container">
									Spectral Range
									<span class="tooltip-text">
										Filter pointings based on their wavelength, energy, or frequency range
									</span>
								</b>
								<b class="ml-2">Type:</b>
								<select class="ml-1 px-2 py-1 border rounded" id="r_spectral_range_type">
									<option value="wavelength" selected>Wavelength</option>
									<option value="energy">Energy</option>
									<option value="frequency">Frequency</option>
								</select>
								<b class="ml-2">Range:</b>
								<input
									size="10"
									type="text"
									class="ml-1 px-1 py-1 border rounded"
									id="r_spectral_range_low"
									placeholder="Min"
								/>
								-
								<input
									size="10"
									type="text"
									class="ml-1 px-1 py-1 border rounded"
									id="r_spectral_range_high"
									placeholder="Max"
								/>
								<b class="ml-2">Unit</b>
								<select class="ml-1 px-2 py-1 border rounded" id="r_spectral_range_unit">
									<option value="nm">nm</option>
									<option value="angstrom">Angstrom</option>
								</select>
							</div>
						</div>

						<br />

						<!-- renorm-skymap result placeholder -->
						<div id="renormdiv"></div>
						<div id="renorm-result" class="mt-4 text-sm"></div>

						<br />

						<div class="flex justify-center gap-4">
							<button
								class="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
								on:click={downloadRenormalizedSkymap}
							>
								Download
							</button>
							<button
								class="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
								on:click={visualizeRenormalizedSkymap}
							>
								Visualize
							</button>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	/* Tooltip styles (matching Flask implementation) */
	.tooltip-container {
		position: relative;
		cursor: help;
		border-bottom: 1px dotted #999;
	}

	.tooltip-container .tooltip-text {
		visibility: hidden;
		width: 300px;
		background-color: #555;
		color: white;
		text-align: left;
		border-radius: 6px;
		padding: 8px;
		font-size: 12px;
		font-weight: normal;
		position: absolute;
		z-index: 1000;
		bottom: 125%;
		left: 50%;
		margin-left: -150px;
		opacity: 0;
		transition: opacity 0.3s;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
	}

	.tooltip-container .tooltip-text::after {
		content: '';
		position: absolute;
		top: 100%;
		left: 50%;
		margin-left: -5px;
		border-width: 5px;
		border-style: solid;
		border-color: #555 transparent transparent transparent;
	}

	.tooltip-container:hover .tooltip-text {
		visibility: visible;
		opacity: 1;
	}

	/* Bootstrap-style form controls */
	.table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 1rem;
	}

	.table th,
	.table td {
		padding: 0.5rem;
		vertical-align: top;
		border-bottom: 1px solid #dee2e6;
	}

	.table th {
		font-weight: 600;
		border-bottom: 2px solid #dee2e6;
	}

	/* Nav tabs styling (matching Bootstrap) */
	.nav-tabs {
		display: flex;
		flex-wrap: wrap;
		border-bottom: 1px solid #dee2e6;
		background-color: #f8f9fa;
	}

	.nav-tabs .nav-item {
		margin-bottom: -1px;
	}

	.nav-tabs .nav-link {
		border: 1px solid transparent;
		border-top-left-radius: 0.25rem;
		border-top-right-radius: 0.25rem;
		transition: all 0.15s ease-in-out;
	}

	.nav-tabs .nav-link:hover {
		border-color: #e9ecef #e9ecef #dee2e6;
	}

	.nav-tabs .nav-link.active,
	.nav-tabs .nav-item.show .nav-link {
		color: #495057;
		background-color: #fff;
		border-color: #dee2e6 #dee2e6 #fff;
	}

	/* Container and row styles */
	.container-fluid {
		width: 100%;
		padding-right: 15px;
		padding-left: 15px;
		margin-right: auto;
		margin-left: auto;
	}

	.row {
		display: flex;
		flex-wrap: wrap;
		margin-right: -15px;
		margin-left: -15px;
	}

	.col-sm-6 {
		flex: 0 0 50%;
		max-width: 50%;
		padding-right: 15px;
		padding-left: 15px;
	}

	/* Form styling */
	select,
	input[type='text'] {
		font-size: 14px;
		line-height: 1.5;
	}

	.btn {
		display: inline-block;
		font-weight: 400;
		text-align: center;
		vertical-align: middle;
		user-select: none;
		border: 1px solid transparent;
		padding: 0.375rem 0.75rem;
		font-size: 1rem;
		line-height: 1.5;
		border-radius: 0.25rem;
		transition:
			color 0.15s ease-in-out,
			background-color 0.15s ease-in-out,
			border-color 0.15s ease-in-out,
			box-shadow 0.15s ease-in-out;
		cursor: pointer;
	}

	.btn-primary {
		color: #fff;
		background-color: #007bff;
		border-color: #007bff;
	}

	.btn-primary:hover {
		color: #fff;
		background-color: #0056b3;
		border-color: #004085;
	}
</style>
