<script lang="ts">
	/**
	 * @page SubmitPointings
	 * @description Submit new telescope pointing observations
	 * @category Pages
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 */

	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { createFormStore } from '$lib/stores/formStore';
	import { validators } from '$lib/validation/validators';

	// Form components
	import FormField from '$lib/components/forms/FormField.svelte';
	import CoordinateFields from '$lib/components/forms/CoordinateFields.svelte';
	import TimeField from '$lib/components/forms/TimeField.svelte';
	import LoadPointingField from '$lib/components/forms/LoadPointingField.svelte';
	import ConditionalSection from '$lib/components/forms/ConditionalSection.svelte';

	// UI components
	import ErrorBoundary from '$lib/components/ui/ErrorBoundary.svelte';

	// Services
	import {
		submitPointing,
		loadFormOptions,
		formatDateTimeForApi,
		parseInstrumentId,
		type PointingData
	} from '$lib/services/pointingService';

	// Types and interfaces
	interface PointingFormData extends Record<string, unknown> {
		loadid: number | null;
		graceid: string;
		obs_status: string;
		ra: number | null;
		dec: number | null;
		instrumentid: string;
		obs_bandpass: string;
		depth: number | null;
		depth_err: number | null;
		depth_unit: string;
		planned_obs_time: string | null;
		completed_obs_time: string | null;
		pos_angle: number | null;
		request_doi: boolean;
		doi_creator_groups: string;
		doi_url: string;
	}

	interface SelectOption {
		value: string;
		label: string;
		disabled?: boolean;
	}

	// Form store
	const formStore = createFormStore<PointingFormData>({
		initialValues: {
			loadid: null,
			graceid: '',
			obs_status: '',
			ra: null,
			dec: null,
			instrumentid: '',
			obs_bandpass: '',
			depth: null,
			depth_err: null,
			depth_unit: '',
			planned_obs_time: null,
			completed_obs_time: null,
			pos_angle: null,
			request_doi: false,
			doi_creator_groups: 'None',
			doi_url: ''
		},
		validateOnChange: true,
		validateOnBlur: true,
		submitHandler: async (data) => {
			try {
				// Parse instrument ID
				const instrumentInfo = parseInstrumentId(data.instrumentid);
				if (!instrumentInfo) {
					throw new Error('Invalid instrument selection');
				}

				// Prepare pointing data
				const pointingData: PointingData = {
					graceid: data.graceid,
					instrumentid: instrumentInfo.id.toString(),
					obs_status: data.obs_status,
					ra: data.ra!,
					dec: data.dec!,
					obs_bandpass: data.obs_bandpass,
					depth: data.depth || undefined,
					depth_err: data.depth_err || undefined,
					depth_unit: data.depth_unit,
					planned_obs_time: formatDateTimeForApi(data.planned_obs_time),
					completed_obs_time: formatDateTimeForApi(data.completed_obs_time),
					pos_angle: data.pos_angle || undefined,
					request_doi: data.request_doi,
					doi_creator_groups:
						data.doi_creator_groups !== 'None' ? data.doi_creator_groups : undefined,
					doi_url: data.doi_url || undefined
				};

				const result = await submitPointing(pointingData);
				return { success: true, result };
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

	// Dropdown options (will be populated from API)
	let graceIdOptions: SelectOption[] = [];
	let instrumentOptions: SelectOption[] = [];
	let bandpassOptions: SelectOption[] = [];
	let depthUnitOptions: SelectOption[] = [];
	let statusOptions: SelectOption[] = [];
	let doiGroupOptions: SelectOption[] = [{ value: 'None', label: 'None' }];

	// Loading states
	let loadingOptions = true;

	// Computed states
	$: showPlannedSection = formData.obs_status === 'planned';
	$: showCompletedSection = formData.obs_status === 'completed';
	$: isFormValid = $formStore.isValid;

	// Load dropdown options
	async function loadDropdownOptions() {
		try {
			loadingOptions = true;

			const options = await loadFormOptions();

			// Grace IDs
			graceIdOptions = [
				{ value: '', label: 'Select Grace ID' },
				...options.graceIds.map((grace) => ({
					value: grace.graceid,
					label: grace.graceid
				}))
			];

			// Instruments
			instrumentOptions = [
				{ value: '', label: 'Select Instrument' },
				...options.instruments.map((inst) => ({
					value: `${inst.id}_${inst.instrument_type}`,
					label: inst.instrument_name
				}))
			];

			// Bandpass options
			bandpassOptions = [
				{ value: '', label: 'Select Bandpass' },
				...options.bandpassOptions.map((band) => ({
					value: band.value,
					label: band.name
				}))
			];

			// Depth units
			depthUnitOptions = [
				{ value: '', label: 'Select Unit' },
				...options.depthUnitOptions.map((unit) => ({
					value: unit.value,
					label: unit.name
				}))
			];

			// Status options
			statusOptions = [
				{ value: '', label: 'Select Status' },
				...options.statusOptions.map((status) => ({
					value: status.value,
					label: status.name
				}))
			];

			// DOI author groups
			doiGroupOptions = [
				{ value: 'None', label: 'None' },
				...options.doiAuthorGroups.map((group) => ({
					value: group.id.toString(),
					label: group.name
				}))
			];
		} catch (error) {
			console.error('Failed to load form options:', error);
		} finally {
			loadingOptions = false;
		}
	}

	// Handle loading existing pointing data
	function handleLoadPointingData(event: CustomEvent) {
		const { data } = event.detail;

		// Update form with loaded data using the format from ajax_pointingfromid
		formStore.setFieldValue('ra', parseFloat(data.ra));
		formStore.setFieldValue('dec', parseFloat(data.dec));
		formStore.setFieldValue('obs_status', 'completed');
		formStore.setFieldValue('instrumentid', data.instrument); // Already in format "id_type"
		formStore.setFieldValue('graceid', data.graceid);
		formStore.setFieldValue('obs_bandpass', data.band);
		formStore.setFieldValue('depth', data.depth);
		formStore.setFieldValue('depth_err', data.depth_err);
	}

	// Form submission
	async function handleSubmit() {
		const result = await formStore.submit();

		if (result.success) {
			// Redirect to success page or show success message
			alert('Pointing submitted successfully!');
			goto('/search/pointings');
		}
	}

	// Lifecycle
	onMount(() => {
		loadDropdownOptions();
	});
</script>

<ErrorBoundary>
	<div class="submit-pointings-page">
		<div class="page-header">
			<h1>Submit Pointing</h1>
			<p class="page-description">
				Submit telescope pointing observations for gravitational wave events.
			</p>
		</div>

		<div class="form-container">
			<form on:submit|preventDefault={handleSubmit}>
				<!-- Load existing pointing -->
				<LoadPointingField
					name="loadid"
					label="Planned ID"
					bind:value={formData.loadid}
					on:load={handleLoadPointingData}
					helpText="Pre-loads existing information for your planned pointings"
				/>

				<!-- Basic information -->
				<div class="form-section">
					<div class="form-row">
						<FormField
							name="graceid"
							label="Grace ID"
							type="select"
							bind:value={formData.graceid}
							options={graceIdOptions}
							required
							disabled={loadingOptions}
							validators={[validators.required('Please select a Grace ID')]}
						/>

						<FormField
							name="obs_status"
							label="Observation Status"
							type="select"
							bind:value={formData.obs_status}
							options={statusOptions}
							required
							validators={[validators.required('Please select observation status')]}
						/>
					</div>

					<!-- Coordinates -->
					<CoordinateFields bind:ra={formData.ra} bind:dec={formData.dec} required />

					<div class="form-row">
						<FormField
							name="instrumentid"
							label="Instrument"
							type="select"
							bind:value={formData.instrumentid}
							options={instrumentOptions}
							required
							disabled={loadingOptions}
							validators={[validators.required('Please select an instrument')]}
						/>

						<FormField
							name="obs_bandpass"
							label="Bandpass"
							type="select"
							bind:value={formData.obs_bandpass}
							options={bandpassOptions}
							required
							validators={[validators.required('Please select a bandpass')]}
						/>
					</div>

					<!-- Depth information -->
					<div class="form-row">
						<FormField
							name="depth"
							label="Depth"
							type="number"
							bind:value={formData.depth}
							validators={[validators.number(), validators.min(0)]}
						/>

						<FormField
							name="depth_err"
							label="Depth Error"
							type="number"
							bind:value={formData.depth_err}
							validators={[validators.number(), validators.min(0)]}
						/>

						<FormField
							name="depth_unit"
							label="Depth Unit"
							type="select"
							bind:value={formData.depth_unit}
							options={depthUnitOptions}
							required
							validators={[validators.required('Please select depth unit')]}
						/>
					</div>
				</div>

				<!-- Conditional sections based on observation status -->
				<ConditionalSection
					show={showPlannedSection}
					className="planned"
					title="Planned Observation"
				>
					<TimeField
						name="planned_obs_time"
						label="Planned Observation Time"
						bind:value={formData.planned_obs_time}
						helpText="YYYY-mm-ddTHH:MM:SS.ss e.g: 2001-01-01T12:30:15.50"
					/>
				</ConditionalSection>

				<ConditionalSection
					show={showCompletedSection}
					className="completed"
					title="Completed Observation"
				>
					<div class="form-section">
						<TimeField
							name="completed_obs_time"
							label="Completed Observation Time"
							bind:value={formData.completed_obs_time}
							helpText="YYYY-mm-ddTHH:MM:SS.ss e.g: 2001-01-01T12:30:15.50"
						/>

						<FormField
							name="pos_angle"
							label="Position Angle"
							type="number"
							bind:value={formData.pos_angle}
							validators={[validators.number(), validators.min(0), validators.max(360)]}
							helpText="Position angle in degrees (0-360)"
						/>

						<!-- DOI Options -->
						<div class="doi-section">
							<FormField
								name="request_doi"
								label="Request DOI"
								type="checkbox"
								bind:value={formData.request_doi}
								helpText="Will request a DOI from Zenodo"
							/>

							{#if formData.request_doi}
								<FormField
									name="doi_creator_groups"
									label="DOI Author Groups"
									type="select"
									bind:value={formData.doi_creator_groups}
									options={doiGroupOptions}
								/>
							{/if}

							<FormField
								name="doi_url"
								label="DOI URL"
								type="url"
								bind:value={formData.doi_url}
								helpText="Existing DOI will be associated to this URL (e.g., published paper link)"
								validators={[validators.url('Please enter a valid URL')]}
							/>
						</div>
					</div>
				</ConditionalSection>

				<!-- Form actions -->
				<div class="form-actions">
					{#if globalError}
						<div class="error-message" role="alert">
							{globalError}
						</div>
					{/if}

					<button
						type="submit"
						class="btn-primary"
						disabled={!isFormValid || isSubmitting || loadingOptions}
					>
						{#if isSubmitting}
							<span class="spinner"></span>
							Submitting...
						{:else}
							Submit Pointing
						{/if}
					</button>

					<button type="button" class="btn-secondary" on:click={() => goto('/search/pointings')}>
						Cancel
					</button>
				</div>
			</form>
		</div>
	</div>
</ErrorBoundary>

<style>
	.submit-pointings-page {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem;
	}

	.page-header {
		margin-bottom: 1.5rem;
	}

	.page-header h1 {
		font-size: 2rem;
		font-weight: 700;
		color: #111827;
		margin: 0 0 0.5rem 0;
	}

	.page-description {
		color: #6b7280;
		margin: 0;
	}

	.form-container {
		background: white;
		border-radius: 0.5rem;
		border: 1px solid #e5e7eb;
		padding: 2rem;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
	}

	.form-section {
		margin-bottom: 1.5rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid #f3f4f6;
	}

	.form-section:last-child {
		border-bottom: none;
		margin-bottom: 0;
		padding-bottom: 0;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	/* Removed unused :has() selector - not needed in current implementation */

	.doi-section {
		background: #f9fafb;
		padding: 1rem;
		border-radius: 0.375rem;
		border: 1px solid #e5e7eb;
		margin-top: 1rem;
	}

	.form-actions {
		display: flex;
		gap: 1rem;
		align-items: center;
		justify-content: flex-end;
		margin-top: 1.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e5e7eb;
	}

	.btn-primary,
	.btn-secondary {
		padding: 0.75rem 1.5rem;
		border-radius: 0.375rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.15s ease-in-out;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.btn-primary {
		background-color: #3b82f6;
		color: white;
		border: 1px solid #3b82f6;
	}

	.btn-primary:hover:not(:disabled) {
		background-color: #2563eb;
		border-color: #2563eb;
	}

	.btn-primary:disabled {
		background-color: #9ca3af;
		border-color: #9ca3af;
		cursor: not-allowed;
	}

	.btn-secondary {
		background-color: #f9fafb;
		color: #374151;
		border: 1px solid #d1d5db;
	}

	.btn-secondary:hover {
		background-color: #f3f4f6;
		border-color: #9ca3af;
	}

	.error-message {
		color: #dc2626;
		background-color: #fef2f2;
		border: 1px solid #fca5a5;
		padding: 0.75rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		flex: 1;
	}

	.spinner {
		width: 1rem;
		height: 1rem;
		border: 2px solid transparent;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.submit-pointings-page {
			padding: 1rem;
		}

		.form-container {
			padding: 1rem;
		}

		.form-row {
			grid-template-columns: 1fr;
		}

		.form-actions {
			flex-direction: column-reverse;
		}

		.btn-primary,
		.btn-secondary {
			width: 100%;
			justify-content: center;
		}
	}
</style>
