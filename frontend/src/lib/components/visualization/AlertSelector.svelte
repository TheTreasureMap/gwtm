<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { gwtmApi, type GWAlertSchema } from '$lib/api.js';

	export let currentGraceid: string = '';

	let alerts: GWAlertSchema[] = [];
	let loading = false;
	let searchTerm = '';
	let showDropdown = false;

	// Filtered alerts based on search term
	$: filteredAlerts = alerts.filter(
		(alert) =>
			alert.graceid.toLowerCase().includes(searchTerm.toLowerCase()) ||
			(alert.alternateid && alert.alternateid.toLowerCase().includes(searchTerm.toLowerCase()))
	);

	onMount(async () => {
		await loadAlerts();
	});

	async function loadAlerts() {
		loading = true;
		try {
			const response = await gwtmApi.queryAlerts({
				per_page: 100,
				sort_by: 'time_of_signal',
				sort_order: 'desc'
			});
			alerts = response.alerts || [];
		} catch (err) {
			console.error('Failed to load alerts:', err);
		} finally {
			loading = false;
		}
	}

	function selectAlert(graceid: string) {
		showDropdown = false;
		searchTerm = '';
		goto(`/alerts?graceids=${graceid}`);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			showDropdown = false;
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="relative mb-6">
	<label for="alert-selector" class="block text-sm font-medium text-gray-700 mb-2">
		Select Gravitational Wave Event
	</label>

	<div class="relative">
		<button
			type="button"
			class="relative w-full bg-white border border-gray-300 rounded-md shadow-sm pl-3 pr-10 py-2 text-left cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
			on:click={() => (showDropdown = !showDropdown)}
		>
			<span class="block truncate">
				{currentGraceid || 'Choose an event...'}
			</span>
			<span class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
				<svg
					class="h-5 w-5 text-gray-400"
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3zm-3.707 9.293a1 1 0 011.414 0L10 14.586l2.293-2.293a1 1 0 011.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
						clip-rule="evenodd"
					/>
				</svg>
			</span>
		</button>

		{#if showDropdown}
			<div
				class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm"
			>
				<!-- Search input -->
				<div class="sticky top-0 bg-white px-3 py-2 border-b">
					<input
						type="text"
						placeholder="Search events..."
						bind:value={searchTerm}
						class="w-full px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
						on:click|stopPropagation
					/>
				</div>

				{#if loading}
					<div class="px-3 py-2 text-center text-gray-500">Loading events...</div>
				{:else if filteredAlerts.length === 0}
					<div class="px-3 py-2 text-center text-gray-500">No events found</div>
				{:else}
					{#each filteredAlerts as alert (alert.graceid)}
						<button
							type="button"
							class="w-full text-left px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
							class:bg-blue-50={alert.graceid === currentGraceid}
							on:click={() => selectAlert(alert.graceid)}
						>
							<div class="flex justify-between items-center">
								<div>
									<div class="font-medium text-gray-900">{alert.graceid}</div>
									{#if alert.alternateid && alert.alternateid !== alert.graceid}
										<div class="text-xs text-gray-500">{alert.alternateid}</div>
									{/if}
								</div>
								<div class="text-xs text-gray-500">
									{#if alert.time_of_signal}
										{new Date(alert.time_of_signal).toLocaleDateString()}
									{/if}
								</div>
							</div>
							<div class="text-xs text-gray-600 mt-1">
								{alert.alert_type} • {alert.role}
								{#if alert.detectors}
									• {alert.detectors}
								{/if}
							</div>
						</button>
					{/each}
				{/if}
			</div>
		{/if}
	</div>
</div>

<!-- Click outside to close dropdown -->
{#if showDropdown}
	<div
		class="fixed inset-0 z-0"
		on:click={() => (showDropdown = false)}
		on:keydown={(e) => e.key === 'Escape' && (showDropdown = false)}
		role="button"
		tabindex="-1"
		aria-label="Close dropdown"
	></div>
{/if}
