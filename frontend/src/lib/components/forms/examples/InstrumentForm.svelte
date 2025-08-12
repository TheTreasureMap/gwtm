<script lang="ts">
	/**
	 * @component InstrumentForm
	 * @description Example form for creating/editing telescope instruments with comprehensive validation
	 * @category Forms
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 *
	 * @example
	 * ```svelte
	 * <InstrumentForm
	 *   mode="create"
	 *   onSubmit={handleCreateInstrument}
	 *   on:success={handleSuccess}
	 *   on:cancel={handleCancel}
	 * />
	 * ```
	 */

	import { createEventDispatcher } from 'svelte';
	import FormField from '../FormField.svelte';
	import Form from '../Form.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import { validationSchemas, validators } from '$lib/validation/validators';
	import type { InstrumentSchema } from '$lib/api';

	/**
	 * @event {CustomEvent<{instrument: InstrumentSchema}>} success - Fired when form submission succeeds
	 * @event {CustomEvent<{error: string}>} error - Fired when form submission fails
	 * @event {CustomEvent} cancel - Fired when form is cancelled
	 */
	const dispatch = createEventDispatcher<{
		success: { instrument: InstrumentSchema };
		error: { error: string };
		cancel: Record<string, never>;
	}>();

	/**
	 * Form mode - create or edit
	 * @type {'create' | 'edit'}
	 * @default 'create'
	 */
	export let mode: 'create' | 'edit' = 'create';

	/**
	 * Initial instrument data (for edit mode)
	 * @type {Partial<InstrumentSchema>}
	 * @optional
	 */
	export let initialData: Partial<InstrumentSchema> = {};

	/**
	 * Submit handler function
	 * @type {(data: any) => Promise<{success: boolean, error?: string, result?: any}>}
	 */
	export let onSubmit: (data: any) => Promise<{ success: boolean; error?: string; result?: any }>;

	/**
	 * Whether to show cancel button
	 * @type {boolean}
	 * @default true
	 */
	export let showCancel: boolean = true;

	// Form data
	let formData = {
		instrument_name: '',
		nickname: '',
		instrument_type: '',
		description: '',
		location: '',
		aperture: '',
		field_of_view: '',
		limiting_magnitude: '',
		wavelength_coverage: '',
		...initialData
	};

	// Instrument type options
	const instrumentTypes = [
		{ value: '1', label: 'Optical Telescope' },
		{ value: '2', label: 'Radio Telescope' },
		{ value: '3', label: 'X-ray Observatory' },
		{ value: '4', label: 'Gamma-ray Detector' },
		{ value: '5', label: 'Gravitational Wave Detector' },
		{ value: '6', label: 'Neutrino Detector' },
		{ value: '7', label: 'Other' }
	];

	// Enhanced validation schema with custom validators
	const instrumentValidationSchema = {
		...validationSchemas.instrument.create,
		description: {
			validators: [
				validators.maxLength(1000, 'Description must be less than 1000 characters'),
				validators.safe()
			]
		},
		location: {
			validators: [
				validators.maxLength(200, 'Location must be less than 200 characters'),
				validators.safe()
			]
		},
		aperture: {
			validators: [
				validators.custom((value) => {
					if (!value) return true; // Optional field
					const num = parseFloat(value);
					if (isNaN(num)) return 'Aperture must be a valid number';
					if (num <= 0) return 'Aperture must be positive';
					if (num > 1000) return 'Aperture seems unrealistically large (>1000m)';
					return true;
				})
			]
		},
		field_of_view: {
			validators: [
				validators.custom((value) => {
					if (!value) return true; // Optional field
					const num = parseFloat(value);
					if (isNaN(num)) return 'Field of view must be a valid number';
					if (num <= 0) return 'Field of view must be positive';
					if (num > 360) return 'Field of view cannot exceed 360 degrees';
					return true;
				})
			]
		},
		limiting_magnitude: {
			validators: [
				validators.custom((value) => {
					if (!value) return true; // Optional field
					const num = parseFloat(value);
					if (isNaN(num)) return 'Limiting magnitude must be a valid number';
					if (num < -30 || num > 50) return 'Limiting magnitude seems unrealistic';
					return true;
				})
			]
		}
	};

	async function handleFormSubmit(data: typeof formData) {
		const result = await onSubmit(data);

		if (result.success) {
			dispatch('success', { instrument: result.result });
		} else {
			dispatch('error', { error: result.error || 'Submission failed' });
		}

		return result;
	}

	function handleCancel() {
		dispatch('cancel');
	}
</script>

<Card>
	<div class="mb-6">
		<h2 class="text-xl font-semibold text-gray-900">
			{mode === 'create' ? 'Register New Instrument' : 'Edit Instrument'}
		</h2>
		<p class="mt-1 text-sm text-gray-600">
			{mode === 'create'
				? 'Add your telescope or instrument to the GWTM network'
				: 'Update instrument information'}
		</p>
	</div>

	<Form
		schema={instrumentValidationSchema}
		bind:data={formData}
		onSubmit={handleFormSubmit}
		submitText={mode === 'create' ? 'Register Instrument' : 'Update Instrument'}
		submitLoadingText={mode === 'create' ? 'Registering...' : 'Updating...'}
		showSubmitButton={false}
		let:isValid
		let:isSubmitting
	>
		<!-- Basic Information Section -->
		<div class="space-y-6">
			<div>
				<h3 class="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
				<div class="grid md:grid-cols-2 gap-6">
					<FormField
						name="instrument_name"
						label="Instrument Name"
						type="text"
						required
						bind:value={formData.instrument_name}
						placeholder="e.g., Hubble Space Telescope"
						helpText="Official name of the instrument"
					/>

					<FormField
						name="nickname"
						label="Nickname"
						type="text"
						bind:value={formData.nickname}
						placeholder="e.g., HST"
						helpText="Common abbreviation or nickname"
					/>
				</div>

				<div class="mt-6">
					<FormField
						name="instrument_type"
						label="Instrument Type"
						type="select"
						required
						bind:value={formData.instrument_type}
						options={instrumentTypes}
						placeholder="Select instrument type"
					/>
				</div>

				<div class="mt-6">
					<FormField
						name="description"
						label="Description"
						type="textarea"
						bind:value={formData.description}
						rows={4}
						placeholder="Detailed description of the instrument capabilities, specifications, and scientific goals..."
						helpText="Optional detailed description (max 1000 characters)"
					/>
				</div>
			</div>

			<!-- Technical Specifications Section -->
			<div>
				<h3 class="text-lg font-medium text-gray-900 mb-4">Technical Specifications</h3>
				<div class="grid md:grid-cols-2 gap-6">
					<FormField
						name="location"
						label="Location"
						type="text"
						bind:value={formData.location}
						placeholder="e.g., Mauna Kea, Hawaii"
						helpText="Geographic location or 'Space' for space-based instruments"
					/>

					<FormField
						name="aperture"
						label="Aperture (meters)"
						type="number"
						bind:value={formData.aperture}
						placeholder="2.4"
						helpText="Primary mirror/aperture diameter in meters"
					/>

					<FormField
						name="field_of_view"
						label="Field of View (degrees)"
						type="number"
						bind:value={formData.field_of_view}
						placeholder="0.1"
						helpText="Field of view in degrees"
					/>

					<FormField
						name="limiting_magnitude"
						label="Limiting Magnitude"
						type="number"
						bind:value={formData.limiting_magnitude}
						placeholder="28.0"
						helpText="Faintest detectable magnitude"
					/>
				</div>

				<div class="mt-6">
					<FormField
						name="wavelength_coverage"
						label="Wavelength Coverage"
						type="text"
						bind:value={formData.wavelength_coverage}
						placeholder="e.g., 300-1000 nm, Radio 1-100 GHz"
						helpText="Spectral range or wavelength coverage"
					/>
				</div>
			</div>
		</div>

		<!-- Form Actions -->
		<div class="flex justify-end space-x-3 pt-6 border-t">
			{#if showCancel}
				<Button variant="secondary" on:click={handleCancel} disabled={isSubmitting}>Cancel</Button>
			{/if}

			<Button
				type="submit"
				variant="primary"
				loading={isSubmitting}
				disabled={!isValid || isSubmitting}
			>
				{#if isSubmitting}
					{mode === 'create' ? 'Registering...' : 'Updating...'}
				{:else}
					{mode === 'create' ? 'Register Instrument' : 'Update Instrument'}
				{/if}
			</Button>
		</div>
	</Form>
</Card>

<style>
	/* Custom styling for form sections */
	h3 {
		position: relative;
	}

	h3::after {
		content: '';
		position: absolute;
		bottom: -0.5rem;
		left: 0;
		width: 3rem;
		height: 2px;
		background-color: #3b82f6;
	}
</style>
