<!--
@component RenormalizeSkyMapTab
@description Renormalize Skymap tab component for Event Explorer
@category Visualization Components
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<RenormalizeSkyMapTab 
  on:download={handleDownload} 
  on:visualize={handleVisualize} 
/>
```

@event download - Fired when Download button is clicked
@event visualize - Fired when Visualize button is clicked
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { ControlGroup, Button, AlertBanner } from '$lib/components/ui';

	const dispatch = createEventDispatcher<{
		download: void;
		visualize: void;
	}>();

	// Form state
	let formData = {
		completedInstruments: ['all'],
		plannedInstruments: ['all'],
		approximate: '1',
		depth: '',
		depthUnit: '',
		bands: [''],
		spectralRangeType: 'wavelength',
		spectralRangeLow: '',
		spectralRangeHigh: '',
		spectralRangeUnit: 'nm'
	};

	// Options for form controls (same as Coverage tab)
	const instrumentOptions = [
		{ value: 'all', label: 'All Instruments' }
		// Additional instruments would be populated from API
	];

	const approximateOptions = [
		{ value: '1', label: 'Yes' },
		{ value: '0', label: 'No' }
	];

	const depthUnitOptions = [
		{ value: '', label: 'Select Unit' },
		{ value: 'mag', label: 'Magnitude' },
		{ value: 'flux', label: 'FLUX erg cm^-2 s^-1' }
	];

	const bandOptions = [
		{ value: '', label: 'All Bands' },
		{ value: 'g', label: 'g' },
		{ value: 'r', label: 'r' },
		{ value: 'i', label: 'i' }
	];

	const spectralRangeTypeOptions = [
		{ value: 'wavelength', label: 'Wavelength' },
		{ value: 'energy', label: 'Energy' },
		{ value: 'frequency', label: 'Frequency' }
	];

	const spectralRangeUnitOptions = [
		{ value: 'nm', label: 'nm' },
		{ value: 'angstrom', label: 'Angstrom' }
	];

	function handleDownload() {
		dispatch('download');
	}

	function handleVisualize() {
		dispatch('visualize');
	}
</script>

<div
	class="tab-pane p-6"
	id="calc-renorm-skymap-content"
	role="tabpanel"
	aria-labelledby="tab-renorm"
>
	<div class="container-fluid max-w-6xl mx-auto">
		<!-- Header -->
		<div class="text-center mb-8">
			<h3 class="text-2xl font-semibold text-gray-900 mb-4">Renormalize Skymap</h3>

			<p class="text-sm text-gray-700 mb-4 max-w-4xl mx-auto">
				Removes pointings from the GW skymap and renormalizes the remaining probability mass, with
				choices to select particular sets of instruments, and/or pointings that cover certain
				wavelengths or depth. All fields are optional, but cuts on depths must have an associated
				unit. If an empty form is submitted, all completed pointings regardless of depth or band are
				removed from the skymap. Once a HEALPIX pixel has been first covered, it is marked as done,
				to avoid double counting probability when the same field is covered multiple times. After
				clicking Download, be patient, it may take up to 3 minutes to fully compute the renormalized
				skymap and download the HEALPIX fits file. Click Visualize to replace the 50% and 90%
				localization contours in the figure above with ones calculated from the renormalized skymap.
			</p>

			<AlertBanner variant="warning" title="Notice">
				The DECam Footprint currently breaks in the calculator. We are temporarily approximating its
				coverage as a circle with 1 deg radius.
			</AlertBanner>
		</div>

		<!-- Renormalize Parameters Form -->
		<div class="bg-white p-6 rounded-lg shadow-sm border mb-8">
			<h4 class="text-lg font-medium text-gray-900 mb-6">Renormalization Parameters</h4>

			<div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
				<!-- Completed Instruments -->
				<ControlGroup label="Completed Instruments" inline>
					<select
						bind:value={formData.completedInstruments}
						multiple
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="r_inst_cov"
					>
						{#each instrumentOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
					<div slot="help" class="text-xs">Completed pointings to include from each instrument</div>
				</ControlGroup>

				<!-- Planned Instruments -->
				<ControlGroup label="Planned Instruments" inline>
					<select
						bind:value={formData.plannedInstruments}
						multiple
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="r_inst_plan"
					>
						{#each instrumentOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
					<div slot="help" class="text-xs">Planned pointings to include from each instrument</div>
				</ControlGroup>

				<!-- Approximate -->
				<ControlGroup label="Approximate" inline>
					<select
						bind:value={formData.approximate}
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="r_approx_cov"
					>
						{#each approximateOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
					<div slot="help" class="text-xs">
						For footprints with multiple CCDs this will approximate the calculator's input by using
						a simplified instrument footprint without chip-gaps. It is substantially faster, but
						does introduce a level of uncertainty.
					</div>
				</ControlGroup>

				<!-- Depth -->
				<ControlGroup label="Depth" inline>
					<input
						type="text"
						bind:value={formData.depth}
						placeholder="Optional"
						class="form-input px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="r_depth_cov"
					/>
				</ControlGroup>

				<!-- Depth Unit -->
				<ControlGroup label="Depth Unit" inline>
					<select
						bind:value={formData.depthUnit}
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="r_depth_unit"
					>
						{#each depthUnitOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</ControlGroup>

				<!-- Band -->
				<ControlGroup label="Band" inline>
					<select
						bind:value={formData.bands}
						multiple
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="r_band_cov"
					>
						{#each bandOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</ControlGroup>

				<!-- Spectral Range Type -->
				<ControlGroup label="Spectral Range Type" inline>
					<select
						bind:value={formData.spectralRangeType}
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="r_spectral_range_type"
					>
						{#each spectralRangeTypeOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
					<div slot="help" class="text-xs">
						Filter pointings based on their wavelength, energy, or frequency range
					</div>
				</ControlGroup>
			</div>

			<!-- Spectral Range Inputs -->
			<div class="mt-6">
				<ControlGroup label="Spectral Range" inline>
					<div class="flex items-center gap-2">
						<input
							type="text"
							bind:value={formData.spectralRangeLow}
							placeholder="Min"
							class="form-input px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-24"
							id="r_spectral_range_low"
						/>
						<span class="text-gray-500">-</span>
						<input
							type="text"
							bind:value={formData.spectralRangeHigh}
							placeholder="Max"
							class="form-input px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-24"
							id="r_spectral_range_high"
						/>
						<select
							bind:value={formData.spectralRangeUnit}
							class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							id="r_spectral_range_unit"
						>
							{#each spectralRangeUnitOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				</ControlGroup>
			</div>
		</div>

		<!-- Results Area -->
		<div class="mb-8">
			<div
				id="renormdiv"
				class="w-full h-64 border border-gray-200 rounded-lg bg-gray-50 mb-4"
			></div>
			<div id="renorm-result" class="text-sm text-gray-600"></div>
		</div>

		<!-- Action Buttons -->
		<div class="flex justify-center gap-4">
			<Button variant="primary" size="lg" on:click={handleDownload}>Download Skymap</Button>
			<Button variant="secondary" size="lg" on:click={handleVisualize}>Visualize</Button>
		</div>
	</div>
</div>
