<script lang="ts">
	/**
	 * @component ExistingInstrumentsTable
	 * @description Displays a table of existing instruments for reference
	 */

	import Card from '$lib/components/ui/Card.svelte';
	import type { InstrumentOption } from '$lib/services/instrumentService';

	export let instruments: InstrumentOption[] = [];
	export let isLoading: boolean = false;

	// Format date for display
	function formatDate(dateString?: string): string {
		if (!dateString) return 'Unknown';
		return new Date(dateString).toLocaleDateString();
	}

	// Get instrument info URL (assuming it exists like in Flask)
	function getInstrumentInfoUrl(id: number): string {
		return `/instrument/${id}`;
	}
</script>

<Card class="existing-instruments-card">
	<div slot="header" class="card-header">
		<h3>Existing Instruments</h3>
		<p class="subtitle">Check existing instruments before submitting a new one</p>
	</div>

	{#if isLoading}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>Loading instruments...</p>
		</div>
	{:else if instruments.length === 0}
		<div class="empty-state">
			<p>No instruments found.</p>
		</div>
	{:else}
		<div class="table-container">
			<table class="instruments-table">
				<thead>
					<tr>
						<th>ID</th>
						<th>Name</th>
						<th>Short Name</th>
						<th>Type</th>
						<th>Date Created</th>
					</tr>
				</thead>
				<tbody>
					{#each instruments as instrument (instrument.id)}
						<tr>
							<td class="id-cell">{instrument.id}</td>
							<td class="name-cell">
								<a href={getInstrumentInfoUrl(instrument.id)} class="instrument-link">
									{instrument.instrument_name}
								</a>
							</td>
							<td class="nickname-cell">{instrument.nickname || '-'}</td>
							<td class="type-cell">{instrument.instrument_type}</td>
							<td class="date-cell">{formatDate(instrument.datecreated)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<div class="table-footer">
			<p class="result-count">
				Showing {instruments.length} instrument{instruments.length !== 1 ? 's' : ''}
			</p>
		</div>
	{/if}
</Card>

<style>
	:global(.existing-instruments-card) {
		height: fit-content;
		max-height: 600px;
		overflow: hidden;
	}

	.card-header h3 {
		margin: 0 0 0.25rem 0;
		color: #111827;
		font-size: 1.25rem;
		font-weight: 600;
	}

	.subtitle {
		margin: 0;
		color: #6b7280;
		font-size: 0.875rem;
	}

	.loading-state,
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 2rem;
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

	.table-container {
		max-height: 400px;
		overflow-y: auto;
		border: 1px solid #e5e7eb;
		border-radius: 0.375rem;
	}

	.instruments-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.instruments-table th {
		background-color: #f9fafb;
		padding: 0.75rem;
		text-align: left;
		font-weight: 600;
		color: #374151;
		border-bottom: 1px solid #e5e7eb;
		position: sticky;
		top: 0;
		z-index: 1;
	}

	.instruments-table td {
		padding: 0.75rem;
		border-bottom: 1px solid #f3f4f6;
		color: #374151;
	}

	.instruments-table tbody tr:hover {
		background-color: #f9fafb;
	}

	.id-cell {
		width: 60px;
		text-align: center;
		font-weight: 500;
	}

	.instrument-link {
		color: #3b82f6;
		text-decoration: none;
		font-weight: 500;
	}

	.instrument-link:hover {
		text-decoration: underline;
		color: #1d4ed8;
	}

	.nickname-cell {
		color: #6b7280;
		font-style: italic;
	}

	.type-cell {
		text-transform: capitalize;
		font-weight: 500;
	}

	.date-cell {
		color: #6b7280;
		font-size: 0.8125rem;
	}

	.table-footer {
		padding: 1rem;
		border-top: 1px solid #e5e7eb;
		background-color: #f9fafb;
	}

	.result-count {
		margin: 0;
		font-size: 0.875rem;
		color: #6b7280;
		text-align: center;
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.instruments-table {
			font-size: 0.8125rem;
		}

		.instruments-table th,
		.instruments-table td {
			padding: 0.5rem;
		}

		/* Hide less important columns on mobile */
		.nickname-cell,
		.date-cell {
			display: none;
		}
	}
</style>
