<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { api } from '$lib/api';
	import { getBandpassOptions, getPointingStatusOptions } from '$lib/services/pointingService';
	import Form from '$lib/components/forms/Form.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import Card from '$lib/components/ui/Card.svelte';

	const dispatch = createEventDispatcher<{
		search: {
			graceid: string;
			bands: string[];
			statuses: string[];
			my_points_only: boolean;
		};
	}>();

	// Form data
	let formData = {
		graceid: '',
		bands: [],
		statuses: [],
		my_points_only: false
	};

	// Form options
	let graceIdOptions: Array<{ value: string; label: string }> = [];
	let bandOptions: Array<{ value: string; label: string }> = [];
	let statusOptions: Array<{ value: string; label: string }> = [];

	let isLoadingOptions = true;

	onMount(async () => {
		await loadFormOptions();
	});

	async function loadFormOptions() {
		try {
			// Load grace IDs for datalist suggestions — fetch enough for autocomplete
			let allAlerts: any[] = [];
			let page = 1;

			const firstResponse = await api.alerts.queryAlerts({ page: 1 });
			allAlerts = firstResponse.alerts || [];

			while (firstResponse.has_next && page < 10) {
				page++;
				const response = await api.alerts.queryAlerts({ page });
				allAlerts = [...allAlerts, ...(response.alerts || [])];
				if (!response.has_next) break;
			}

			const uniqueGraceIds = [...new Set(allAlerts.map((a: any) => a.graceid))]
				.filter(Boolean)
				.sort()
				.reverse();

			graceIdOptions = uniqueGraceIds.map((gid: string) => ({ value: gid, label: gid }));

			// Load band options from API
			const bandpassData = await getBandpassOptions();
			bandOptions = [
				{ value: 'all', label: 'All' },
				...bandpassData.map((band) => ({
					value: band.value,
					label: band.name
				}))
			];

			// Load status options from API
			const statusData = await getPointingStatusOptions();
			statusOptions = [
				{ value: 'all', label: 'All' },
				...statusData.map((status) => ({
					value: status.value,
					label: status.name
				}))
			];
		} catch (err) {
			console.error('Failed to load form options:', err);
		} finally {
			isLoadingOptions = false;
		}
	}

	async function handleSubmit() {
		if (!formData.graceid) {
			throw new Error('Grace ID is required');
		}

		// Process bands - if "all" is selected, send empty array
		const processedBands = formData.bands.includes('all') ? [] : formData.bands;

		// Process statuses - if "all" is selected, send empty array
		const processedStatuses = formData.statuses.includes('all') ? [] : formData.statuses;

		dispatch('search', {
			graceid: formData.graceid,
			bands: processedBands,
			statuses: processedStatuses,
			my_points_only: formData.my_points_only
		});

		return { success: true };
	}
</script>

<Card title="Search Filters">
	<Form
		bind:data={formData}
		onSubmit={handleSubmit}
		submitText="Search"
		submitLoadingText="Searching..."
		let:isSubmitting
	>
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			<!-- Grace ID -->
			<div class="space-y-1">
				<label for="graceid" class="block text-sm font-medium text-gray-700">
					Grace ID <span class="text-red-500">*</span>
				</label>
				<input
					id="graceid"
					name="graceid"
					type="text"
					list="graceid-options"
					bind:value={formData.graceid}
					placeholder={isLoadingOptions ? 'Loading suggestions...' : 'e.g. S250206dm'}
					class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2"
					autocomplete="off"
				/>
				<datalist id="graceid-options">
					{#each graceIdOptions.filter(o => o.value) as option (option.value)}
						<option value={option.value} />
					{/each}
				</datalist>
				<p class="text-xs text-gray-500">Type to search, or select from suggestions</p>
			</div>

			<!-- Bandpasses -->
			<div class="space-y-2">
				<label class="block text-sm font-medium text-gray-700">Bandpasses</label>
				<div class="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-md p-2">
					{#each bandOptions as option (option.value)}
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:group={formData.bands}
								value={option.value}
								disabled={isLoadingOptions}
								class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
							/>
							<span class="ml-2 text-sm text-gray-700">{option.label}</span>
						</label>
					{/each}
				</div>
			</div>

			<!-- Status -->
			<div class="space-y-2">
				<label class="block text-sm font-medium text-gray-700">Status</label>
				<div class="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-md p-2">
					{#each statusOptions as option (option.value)}
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:group={formData.statuses}
								value={option.value}
								disabled={isLoadingOptions}
								class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
							/>
							<span class="ml-2 text-sm text-gray-700">{option.label}</span>
						</label>
					{/each}
				</div>
			</div>
		</div>

		<!-- My Points Only -->
		<div class="mt-6">
			<FormField
				name="my_points_only"
				label="Show Only My Pointings"
				type="checkbox"
				bind:value={formData.my_points_only}
				helpText="(required for DOI request)"
			/>
		</div>

		<!-- Loading state for options -->
		{#if isLoadingOptions}
			<div class="mt-4 text-sm text-gray-500 flex items-center">
				<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					></path>
				</svg>
				Loading form options...
			</div>
		{/if}
	</Form>
</Card>
