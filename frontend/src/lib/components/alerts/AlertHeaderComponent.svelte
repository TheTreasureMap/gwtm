<!--
AlertHeaderComponent.svelte - Alert header display component
Extracted from alerts/+page.svelte to apply service-oriented architecture patterns.
Displays alert title, status badges, and special download links.
-->
<script lang="ts">
	import type { GWAlertSchema } from '$lib/api';
	import AlertStatusService from './services/AlertStatusService.svelte';

	// Required props
	export let graceid: string;
	export let alert: GWAlertSchema | null = null;

	// Service component reference
	let statusService: AlertStatusService;

	// Computed values using status service
	$: statusBadge = alert ? statusService?.getStatusBadge(alert, graceid) : null;
	$: specialDownloads = statusService?.getSpecialDownloads(graceid) || [];
	$: graceDbUrl = statusService?.getGraceDbUrl(graceid) || '';
</script>

<!-- Service component -->
<AlertStatusService bind:this={statusService} />

<!-- Alert Header -->
<div class="mb-3">
	<h1 class="text-xl font-bold text-gray-900 mb-1">
		Gravitational Wave Localization and Pointings: {graceid}
		<a
			href={graceDbUrl}
			target="_blank"
			rel="noopener noreferrer"
			class="text-blue-600 hover:text-blue-800 text-sm font-normal ml-2"
		>
			[GraceDB]
		</a>
	</h1>

	<!-- Status Badge -->
	{#if statusBadge}
		<div class="p-4 mb-4 {statusBadge.color} {statusBadge.borderClass}">
			{#if statusBadge.type === 'retracted'}
				<h2 class="text-xl font-bold">{statusBadge.title}</h2>
			{:else if statusBadge.type === 'test'}
				<h5 class="font-medium">{statusBadge.message}</h5>
			{/if}
		</div>
	{/if}

	<!-- Special Downloads -->
	{#if specialDownloads.length > 0}
		<div class="flex space-x-4 mb-4">
			{#each specialDownloads as download}
				<a
					href={download.url}
					download={download.filename}
					class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
				>
					{download.title}
				</a>
			{/each}
		</div>
	{/if}
</div>
