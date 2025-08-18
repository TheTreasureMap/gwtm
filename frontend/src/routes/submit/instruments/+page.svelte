<script lang="ts">
	/**
	 * @page SubmitInstruments
	 * @description Submit new telescope instruments with footprint configurations
	 * @category Pages
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2025-01-10
	 */

	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { createFormStore } from '$lib/stores/formStore';

	// Form components
	import FormField from '$lib/components/forms/FormField.svelte';
	import FootprintTypeSelector from '$lib/components/forms/FootprintTypeSelector.svelte';

	// UI components
	import Card from '$lib/components/ui/Card.svelte';
	import ErrorBoundary from '$lib/components/ui/ErrorBoundary.svelte';
	import ExistingInstrumentsTable from '$lib/components/instruments/ExistingInstrumentsTable.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	// Services
	import {
		submitInstrument,
		loadFormOptions,
		validateInstrumentData,
		previewFootprint,
		type InstrumentData,
		type EnumOption,
		type InstrumentOption
	} from '$lib/services/instrumentService';

	// Types and interfaces
	interface InstrumentFormData {
		instrument_name: string;
		nickname: string;
		instrument_type: string;
		footprint_type: string;
		unit: string;
		height: number | null;
		width: number | null;
		radius: number | null;
		polygon: string;
	}

	interface SelectOption {
		value: string;
		label: string;
		disabled?: boolean;
	}

	// Form store
	const formStore = createFormStore<InstrumentFormData>({
		initialValues: {
			instrument_name: '',
			nickname: '',
			instrument_type: '',
			footprint_type: '',
			unit: '',
			height: null,
			width: null,
			radius: null,
			polygon: ''
		},
		validateOnChange: true,
		validateOnBlur: true,
		submitHandler: async (data) => {
			console.log('Submit handler called with:', data);
			console.log('Existing instruments for validation:', existingInstruments.length);
			try {
				// Client-side validation (including duplicate check)
				const validation = validateInstrumentData(data, existingInstruments);
				console.log('Validation result:', validation);
				if (!validation.isValid) {
					return {
						success: false,
						error: validation.errors.join('; ')
					};
				}

				// Prepare instrument data (remove empty optional fields)
				const instrumentData: InstrumentData = {
					instrument_name: data.instrument_name,
					instrument_type: data.instrument_type,
					footprint_type: data.footprint_type,
					unit: data.unit,
					...(data.nickname && { nickname: data.nickname }),
					...(data.height !== null && { height: data.height }),
					...(data.width !== null && { width: data.width }),
					...(data.radius !== null && { radius: data.radius }),
					...(data.polygon && { polygon: data.polygon })
				};

				console.log('Submitting to API:', instrumentData);
				const result = await submitInstrument(instrumentData);
				console.log('API result:', result);

				if (result.success) {
					// Add the new instrument to the existing list immediately
					// to prevent duplicate submissions
					if (result.instrument) {
						existingInstruments = [
							...existingInstruments,
							{
								id: result.instrument.id,
								instrument_name: result.instrument.instrument_name,
								nickname: result.instrument.nickname,
								instrument_type: result.instrument.instrument_type,
								datecreated: new Date().toISOString(),
								submitterid: result.instrument.submitterid
							}
						];

						// Redirect immediately upon success
						console.log('Success! Redirecting to instrument:', result.instrument.id);
						setTimeout(() => {
							goto(`/instrument/${result.instrument.id}`);
						}, 1000); // Brief delay to show success message
					}
					return { success: true, result };
				} else {
					return {
						success: false,
						error: result.message || 'Submission failed',
						details: result.errors
					};
				}
			} catch (error) {
				return {
					success: false,
					error: error instanceof Error ? error.message : 'Submission failed'
				};
			}
		}
	});

	// Reactive form state
	$: formData = $formStore.data;
	$: isSubmitting = $formStore.isSubmitting;
	$: globalError = $formStore.globalError;
	$: submitResult = $formStore.submitResult;

	// Debug submitResult changes
	$: if (submitResult) {
		console.log('submitResult changed:', submitResult);
	}

	// Form options
	let instrumentTypeOptions: SelectOption[] = [];
	let footprintTypeOptions: EnumOption[] = [];
	let footprintUnitOptions: SelectOption[] = [];
	let existingInstruments: InstrumentOption[] = [];

	// Loading states
	let loadingOptions = true;
	let previewLoading = false;
	let previewData: any = null;
	let previewError: string = '';

	// Real-time validation states
	let nameValidationError: string = '';

	// Load dropdown options
	async function loadDropdownOptions() {
		try {
			loadingOptions = true;

			const options = await loadFormOptions();

			// Instrument types
			instrumentTypeOptions = [
				{ value: '', label: 'Choose Type' },
				...options.instrumentTypes.map((type) => ({
					value: type.value, // Already string from API
					label: type.name
				}))
			];

			// Footprint types (used by FootprintTypeSelector)
			footprintTypeOptions = options.footprintTypes;

			// Footprint units
			footprintUnitOptions = [
				{ value: '', label: 'Choose Unit' },
				...options.footprintUnits.map((unit) => ({
					value: unit.value,
					label: unit.name
				}))
			];

			// Existing instruments
			existingInstruments = options.existingInstruments.sort(
				(a, b) => new Date(b.datecreated || '').getTime() - new Date(a.datecreated || '').getTime()
			);
		} catch (error) {
			console.error('Failed to load form options:', error);
		} finally {
			loadingOptions = false;
		}
	}

	// Preview footprint
	async function handlePreviewFootprint() {
		if (!formData.footprint_type || !formData.unit) {
			previewError = 'Please select footprint type and unit before previewing';
			return;
		}

		try {
			previewLoading = true;
			previewError = '';

			const validation = validateInstrumentData(formData, existingInstruments);
			if (!validation.isValid) {
				previewError = validation.errors.join('; ');
				return;
			}

			previewData = await previewFootprint(formData);
		} catch (error) {
			previewError = error instanceof Error ? error.message : 'Preview failed';
			console.error('Preview error:', error);
		} finally {
			previewLoading = false;
		}
	}

	// Handle plot rendering when preview data changes
	$: if (previewData && typeof window !== 'undefined' && window.Plotly) {
		// Use setTimeout to ensure DOM is updated
		setTimeout(renderPreviewPlot, 50);
	}

	// Render preview plot
	function renderPreviewPlot() {
		const plotDiv = document.getElementById('preview-plot');
		if (plotDiv && previewData && window.Plotly) {
			try {
				window.Plotly.newPlot('preview-plot', previewData.data, previewData.layout);
			} catch (error) {
				console.error('Failed to render plot:', error);
			}
		}
	}

	// Handle successful submission
	$: {
		console.log('Checking submitResult:', submitResult);
		if (submitResult?.success && submitResult.result?.instrument?.id) {
			console.log('Success detected, redirecting...', submitResult);
			// Refresh the instruments list first
			loadDropdownOptions().then(() => {
				// Redirect to the newly created instrument's page
				const instrumentId = submitResult.result.instrument.id;
				goto(`/instrument/${instrumentId}`);
			});
		} else if (submitResult?.success) {
			console.log('Success but no instrument ID:', submitResult);
		} else if (submitResult) {
			console.log('Submit result received:', submitResult);
		}
	}

	// Real-time instrument name validation
	function validateInstrumentName() {
		if (!formData.instrument_name?.trim()) {
			nameValidationError = '';
			return;
		}

		const trimmedName = formData.instrument_name.trim();
		console.log(
			'Checking name:',
			trimmedName,
			'against',
			existingInstruments.length,
			'instruments'
		);
		const isDuplicate = existingInstruments.some((instrument) => {
			const match = instrument.instrument_name.toLowerCase() === trimmedName.toLowerCase();
			if (match) console.log('Found duplicate:', instrument.instrument_name);
			return match;
		});

		nameValidationError = isDuplicate
			? 'An instrument with this name already exists. Please choose a different name.'
			: '';
		console.log('Name validation result:', nameValidationError);
	}

	// Reactive validation when instrument name or existing instruments change
	$: if (formData.instrument_name !== undefined || existingInstruments.length > 0) {
		validateInstrumentName();
	}

	// Initialize
	onMount(() => {
		loadDropdownOptions();
	});
</script>

<svelte:head>
	<title>Submit Instrument - GWTM</title>
	<meta
		name="description"
		content="Submit a new telescope instrument to the Gravitational Wave Treasure Map"
	/>
	<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</svelte:head>

<ErrorBoundary>
	<div class="submit-instruments-page">
		<div class="page-header">
			<h1>Submit Instrument</h1>
			<p class="page-description">
				Please check the existing instruments table to see if your instrument already exists before
				submitting a new instrument. Contact an administrator if there are any issues.
			</p>
		</div>

		<div class="page-content">
			<!-- Left Column: Form -->
			<div class="form-column">
				<Card class="form-card">
					<div slot="header" class="form-header">
						<h2>Instrument Information</h2>
					</div>

					{#if loadingOptions}
						<div class="loading-state">
							<div class="spinner"></div>
							<p>Loading form options...</p>
						</div>
					{:else}
						<form on:submit|preventDefault={formStore.handleSubmit} class="instrument-form">
							<!-- Basic Information -->
							<div class="form-section">
								<h3>Basic Information</h3>

								<FormField
									name="instrument_name"
									label="Name"
									type="text"
									bind:value={formData.instrument_name}
									required
									disabled={isSubmitting}
									helpText="Full name of the instrument"
									error={nameValidationError}
								/>

								<FormField
									name="nickname"
									label="Short Name"
									type="text"
									bind:value={formData.nickname}
									disabled={isSubmitting}
									helpText="Optional short name or abbreviation"
								/>

								<FormField
									name="instrument_type"
									label="Instrument Type"
									type="select"
									bind:value={formData.instrument_type}
									options={instrumentTypeOptions}
									required
									disabled={isSubmitting}
									helpText="Type of instrument"
								/>
							</div>

							<!-- Footprint Configuration -->
							<div class="form-section">
								<h3>Footprint Configuration</h3>

								<FormField
									name="unit"
									label="Unit"
									type="select"
									bind:value={formData.unit}
									options={footprintUnitOptions}
									required
									disabled={isSubmitting}
									helpText="Unit for footprint dimensions"
								/>

								<FootprintTypeSelector
									bind:footprintType={formData.footprint_type}
									bind:height={formData.height}
									bind:width={formData.width}
									bind:radius={formData.radius}
									bind:polygon={formData.polygon}
									footprintTypes={footprintTypeOptions}
								/>
							</div>

							<!-- Form Actions -->
							<div class="form-actions">
								<Button
									type="button"
									variant="secondary"
									on:click={handlePreviewFootprint}
									disabled={previewLoading || isSubmitting}
								>
									{previewLoading ? 'Previewing...' : 'Preview Footprint'}
								</Button>

								<Button
									type="submit"
									variant="primary"
									disabled={isSubmitting || loadingOptions || !!nameValidationError}
								>
									{isSubmitting ? 'Submitting...' : 'Submit Instrument'}
								</Button>
							</div>

							<!-- Error Display -->
							{#if globalError}
								<div class="error-message">
									<strong>Error:</strong>
									{globalError}
									{#if submitResult?.details}
										<ul class="error-details">
											{#each submitResult.details as detail}
												<li>{detail}</li>
											{/each}
										</ul>
									{/if}
								</div>
							{/if}

							<!-- Success Display -->
							{#if submitResult?.success}
								<div class="success-message">
									<strong>Success!</strong>
									{submitResult.result?.message || 'Instrument submitted successfully'}
									{#if submitResult.result?.instrument}
										<p>
											Your instrument ID is: <strong>{submitResult.result.instrument.id}</strong>
										</p>
										<p>Redirecting to instrument page...</p>
									{/if}
								</div>
							{/if}
						</form>
					{/if}
				</Card>
			</div>

			<!-- Right Column: Existing Instruments & Preview -->
			<div class="table-column">
				<ExistingInstrumentsTable instruments={existingInstruments} isLoading={loadingOptions} />

				<!-- Preview Section -->
				{#if previewData || previewError}
					<Card class="preview-card">
						<div slot="header">
							<h3>Footprint Preview</h3>
						</div>

						{#if previewError}
							<div class="preview-error">
								<strong>Preview Error:</strong>
								{previewError}
							</div>
						{:else if previewData}
							<div id="preview-plot" class="preview-plot"></div>
						{/if}
					</Card>
				{/if}
			</div>
		</div>
	</div>
</ErrorBoundary>

<style>
	.submit-instruments-page {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
	}

	.page-header {
		margin-bottom: 1.5rem;
		text-align: center;
	}

	.page-header h1 {
		margin: 0 0 1rem 0;
		color: #111827;
		font-size: 2.5rem;
		font-weight: 700;
	}

	.page-description {
		margin: 0;
		color: #6b7280;
		font-size: 1.125rem;
		max-width: 800px;
		margin-left: auto;
		margin-right: auto;
		line-height: 1.6;
	}

	.page-content {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		align-items: start;
	}

	.form-column {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.table-column {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	:global(.form-card) {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
	}

	.form-header h2 {
		margin: 0;
		color: #111827;
		font-size: 1.5rem;
		font-weight: 600;
	}

	.instrument-form {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.form-section {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.form-section h3 {
		margin: 0 0 0.5rem 0;
		color: #374151;
		font-size: 1.25rem;
		font-weight: 600;
		padding-bottom: 0.5rem;
		border-bottom: 2px solid #e5e7eb;
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #e5e7eb;
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 3rem;
		color: #6b7280;
	}

	.spinner {
		width: 2rem;
		height: 2rem;
		border: 3px solid #e5e7eb;
		border-top: 3px solid #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 1rem;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	.error-message {
		background-color: #fef2f2;
		border: 1px solid #fca5a5;
		border-radius: 0.375rem;
		padding: 1rem;
		color: #dc2626;
	}

	.error-details {
		margin: 0.5rem 0 0 0;
		padding-left: 1.25rem;
	}

	.success-message {
		background-color: #f0fdf4;
		border: 1px solid #86efac;
		border-radius: 0.375rem;
		padding: 1rem;
		color: #15803d;
	}

	.preview-card {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
	}

	.preview-plot {
		width: 100%;
		height: 400px;
	}

	.preview-error {
		padding: 1rem;
		background-color: #fef2f2;
		border: 1px solid #fca5a5;
		border-radius: 0.375rem;
		color: #dc2626;
	}

	/* Mobile responsiveness */
	@media (max-width: 1024px) {
		.page-content {
			grid-template-columns: 1fr;
		}

		.page-header h1 {
			font-size: 2rem;
		}

		.submit-instruments-page {
			padding: 1rem;
		}
	}

	@media (max-width: 768px) {
		.form-actions {
			flex-direction: column;
		}

		.page-description {
			font-size: 1rem;
		}
	}
</style>
