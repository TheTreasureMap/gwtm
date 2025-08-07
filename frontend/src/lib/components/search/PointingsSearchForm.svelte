<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { api } from '$lib/api';
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
			// Load ALL Grace IDs from alerts - fetch all pages like Flask does with .all()
			let allAlerts: any[] = [];
			let page = 1;
			let totalFetched = 0;

			// First request to get total count
			const firstResponse = await api.alerts.queryAlerts({ page: 1 });
			allAlerts = firstResponse.alerts || [];
			const totalCount = firstResponse.total || 0;
			totalFetched = allAlerts.length;

			console.log(`Initial fetch: ${totalFetched}/${totalCount} alerts`);

			// Fetch remaining pages if needed
			while (totalFetched < totalCount && firstResponse.has_next) {
				page++;
				const response = await api.alerts.queryAlerts({ page });
				const pageAlerts = response.alerts || [];
				allAlerts = [...allAlerts, ...pageAlerts];
				totalFetched += pageAlerts.length;

				console.log(`Fetched page ${page}: ${totalFetched}/${totalCount} alerts`);

				if (!response.has_next) break;
				if (page > 50) break; // Safety limit
			}

			const uniqueGraceIds = [...new Set(allAlerts.map((a: any) => a.graceid))]
				.filter(Boolean)
				.sort()
				.reverse();

			console.log(
				`Final result: ${uniqueGraceIds.length} unique Grace IDs from ${allAlerts.length} total alerts`
			);

			graceIdOptions = [
				{ value: '', label: '--Select--' },
				...uniqueGraceIds.map((gid: string) => ({ value: gid, label: gid }))
			];

			// Standard band options
			bandOptions = [
				{ value: 'all', label: 'All' },
				{ value: 'g', label: 'g' },
				{ value: 'r', label: 'r' },
				{ value: 'i', label: 'i' },
				{ value: 'z', label: 'z' },
				{ value: 'y', label: 'y' },
				{ value: 'J', label: 'J' },
				{ value: 'H', label: 'H' },
				{ value: 'K', label: 'K' }
			];

			// Standard status options
			statusOptions = [
				{ value: 'all', label: 'All' },
				{ value: 'planned', label: 'Planned' },
				{ value: 'completed', label: 'Completed' },
				{ value: 'cancelled', label: 'Cancelled' }
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
			<FormField
				name="graceid"
				label="Grace ID"
				type="select"
				bind:value={formData.graceid}
				options={graceIdOptions}
				required
				disabled={isLoadingOptions}
				helpText="*required"
			/>

			<!-- Bandpasses -->
			<div class="space-y-2">
				<label class="block text-sm font-medium text-gray-700">Bandpasses</label>
				<div class="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-md p-2">
					{#each bandOptions as option}
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
					{#each statusOptions as option}
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
