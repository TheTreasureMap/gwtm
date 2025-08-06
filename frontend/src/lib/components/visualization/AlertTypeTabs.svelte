<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { GWAlertSchema } from '$lib/api';

	export let availableAlertTypes: any[] = [];
	export let selectedAlertType: string = '';
	export let loading: boolean = false;

	const dispatch = createEventDispatcher();

	function handleAlertTypeSwitch(alertType: string) {
		dispatch('alertTypeChange', { alertType });
	}
</script>

<!-- Alert Type Tabs (matching Flask) - positioned at top above visualization -->
{#if availableAlertTypes.length > 0}
	<div class="mb-4">
		<ul class="nav nav-tabs flex flex-wrap border-b border-gray-200">
			{#each availableAlertTypes as alertTypeOption}
				<li class="nav-item mr-2">
					<button
						class="px-3 py-2 text-sm font-medium border-b-2 transition-all cursor-pointer
							{selectedAlertType === alertTypeOption.alert_type
							? 'text-blue-600 border-blue-600 bg-blue-50'
							: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}"
						on:click={() => handleAlertTypeSwitch(alertTypeOption.alert_type)}
						disabled={loading}
					>
						<div class="text-center leading-tight">
							<div class="font-medium">{alertTypeOption.alert_type}</div>
							{#if alertTypeOption.timesent}
								<div class="text-xs opacity-75">
									{new Date(alertTypeOption.timesent).toLocaleString()}
								</div>
							{/if}
						</div>
					</button>
				</li>
			{/each}
		</ul>
	</div>
{/if}

<style>
	.nav-tabs {
		display: flex;
		flex-wrap: wrap;
		border-bottom: 1px solid #dee2e6;
	}

	.nav-tabs .nav-item {
		margin-bottom: -1px;
	}

	.nav-tabs button {
		border: 1px solid transparent;
		border-top-left-radius: 0.25rem;
		border-top-right-radius: 0.25rem;
		transition: all 0.15s ease-in-out;
	}

	.nav-tabs button:hover:not(:disabled) {
		border-color: #e9ecef #e9ecef #dee2e6;
	}

	.nav-tabs button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>
