<!--
@component CoverageCalculatorTab
@description Coverage Calculator tab component for Event Explorer
@category Visualization Components
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<CoverageCalculatorTab {plotlyContainer} on:calculate={handleCalculateCoverage} />
```

@prop {HTMLDivElement | null} plotlyContainer - Container for the Plotly coverage plot

@event calculate - Fired when Calculate button is clicked
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { ControlGroup, Button, AlertBanner } from '$lib/components/ui';

	const dispatch = createEventDispatcher<{
		calculate: void;
	}>();

	/**
	 * Container for the Plotly coverage plot
	 * @type {HTMLDivElement | null}
	 * @default null
	 */
	export let plotlyContainer: HTMLDivElement | null = null;

	// Form state
	let formData = {
		instruments: ['all'],
		approximate: '1',
		depth: '',
		depthUnit: '',
		bands: [''],
		spectralRangeType: 'wavelength',
		spectralRangeLow: '',
		spectralRangeHigh: '',
		spectralRangeUnit: 'nm'
	};

	// Options for form controls
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

	function handleCalculate() {
		dispatch('calculate');
	}
</script>

<div class="tab-pane p-6" id="calc-coverage-content" role="tabpanel" aria-labelledby="tab-coverage">
	<div class="container-fluid max-w-6xl mx-auto">
		<!-- Header -->
		<div class="text-center mb-8">
			<h3 class="text-2xl font-semibold text-gray-900 mb-4">Coverage Calculator</h3>

			<p class="text-sm text-gray-700 mb-4 max-w-4xl mx-auto">
				Calculate the coverage of the GW localization over time, with choices to limit the coverage
				calculation to particular sets of instruments, wavelengths, or depth. All fields are
				optional, but cuts on depths must have an associated unit. If an empty form is submitted,
				the total reported coverage regardless of depth or band is computed. Once a HEALPIX pixel
				has been first covered, it is marked as done, to avoid double counting probability when the
				same field is covered multiple times. After clicking Calculate, be patient, it may take up
				to 2 minutes to fully compute the coverage profile.
			</p>

			<AlertBanner variant="warning" title="Notice">
				The DECam Footprint currently breaks in the calculator. We are temporarily approximating its
				coverage as a circle with 1 deg radius.
			</AlertBanner>
		</div>

		<!-- Coverage Plot Container -->
		<div class="mb-8">
			<div
				id="coveragediv"
				class="w-full h-96 border border-gray-200 rounded-lg bg-gray-50"
				bind:this={plotlyContainer}
			></div>
		</div>

		<!-- Coverage Parameters Form -->
		<div class="bg-white p-6 rounded-lg shadow-sm border">
			<h4 class="text-lg font-medium text-gray-900 mb-6">Coverage Parameters</h4>

			<div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
				<!-- Instrument Selection -->
				<ControlGroup label="Instrument" inline>
					<select
						bind:value={formData.instruments}
						multiple
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="inst_cov"
					>
						{#each instrumentOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</ControlGroup>

				<!-- Approximate -->
				<ControlGroup label="Approximate" inline>
					<select
						bind:value={formData.approximate}
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="approx_cov"
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
						id="depth_cov"
					/>
				</ControlGroup>

				<!-- Depth Unit -->
				<ControlGroup label="Depth Unit" inline>
					<select
						bind:value={formData.depthUnit}
						class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						id="depth_unit"
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
						id="band_cov"
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
						id="spectral_range_type"
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
							id="spectral_range_low"
						/>
						<span class="text-gray-500">-</span>
						<input
							type="text"
							bind:value={formData.spectralRangeHigh}
							placeholder="Max"
							class="form-input px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-24"
							id="spectral_range_high"
						/>
						<select
							bind:value={formData.spectralRangeUnit}
							class="form-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							id="spectral_range_unit"
						>
							{#each spectralRangeUnitOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				</ControlGroup>
			</div>

			<!-- Calculate Button -->
			<div class="mt-8 flex justify-center">
				<Button variant="primary" size="large" on:click={handleCalculate}>
					Calculate Coverage
				</Button>
			</div>
		</div>
	</div>
</div>
