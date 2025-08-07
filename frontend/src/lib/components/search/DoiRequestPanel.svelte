<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { api } from '$lib/api';
	import Button from '$lib/components/ui/Button.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import Card from '$lib/components/ui/Card.svelte';

	const dispatch = createEventDispatcher<{
		'doi-request': {
			pointing_ids: number[];
			graceid: string;
			doi_group_id: string;
			doi_url?: string;
		};
	}>();

	export let selectedPointings: Set<number>;
	export let graceid: string;
	export let visible: boolean = false;

	// Form state
	let doiCreatorGroup = '';
	let doiUrl = '';
	let availableCreatorGroups: Array<{ value: string; label: string }> = [];
	let isLoadingGroups = true;
	let isRequestingDoi = false;

	onMount(async () => {
		await loadCreatorGroups();
	});

	async function loadCreatorGroups() {
		try {
			const groups = await api.doi.getDOIAuthorGroups();
			availableCreatorGroups = [
				{ value: '', label: 'None' },
				...groups.map((g: any) => ({ value: g.id, label: g.name }))
			];
		} catch (err) {
			console.warn('Could not load DOI creator groups:', err);
			availableCreatorGroups = [{ value: '', label: 'None' }];
		} finally {
			isLoadingGroups = false;
		}
	}

	async function handleDoiRequest() {
		if (selectedPointings.size === 0) {
			throw new Error('Please select pointings to request DOI for');
		}

		if (!doiCreatorGroup) {
			throw new Error('Please select a DOI Author Group');
		}

		isRequestingDoi = true;

		try {
			const requestPayload = {
				pointing_ids: Array.from(selectedPointings),
				graceid,
				doi_group_id: doiCreatorGroup,
				...(doiUrl && { doi_url: doiUrl })
			};

			dispatch('doi-request', requestPayload);
		} finally {
			isRequestingDoi = false;
		}
	}

	// Reset form when visibility changes
	$: if (!visible) {
		doiCreatorGroup = '';
		doiUrl = '';
	}
</script>

{#if visible}
	<Card title="Request DOI" variant="info">
		<div class="space-y-6">
			<!-- DOI Request Button -->
			<div class="text-center">
				<Button
					variant="primary"
					size="large"
					fullWidth
					loading={isRequestingDoi}
					disabled={selectedPointings.size === 0 || isLoadingGroups}
					on:click={handleDoiRequest}
				>
					{#if isRequestingDoi}
						Processing DOI Request...
					{:else}
						Request DOI for Selected ({selectedPointings.size})
					{/if}
				</Button>
			</div>

			<!-- Form Fields -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
				<!-- DOI Creator Group -->
				<FormField
					name="doiCreatorGroup"
					label="DOI Author Groups"
					type="select"
					bind:value={doiCreatorGroup}
					options={availableCreatorGroups}
					disabled={isLoadingGroups}
					required
				/>

				<!-- DOI URL -->
				<FormField
					name="doiUrl"
					label="DOI URL"
					type="url"
					bind:value={doiUrl}
					placeholder="https://doi.org/..."
					helpText="Associate an already existing DOI URL"
				/>
			</div>

			<!-- Help Text -->
			<div class="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
				<p class="mb-2">
					<strong>Note:</strong> DOI requests can only be made for:
				</p>
				<ul class="list-disc list-inside space-y-1 text-xs">
					<li>Pointings with status "completed"</li>
					<li>Pointings that you submitted (when "Show Only My Pointings" is checked)</li>
					<li>Pointings that don't already have a DOI</li>
				</ul>
				<p class="mt-3 text-xs">
					Don't have a DOI Author group? You can create one
					<a href="/manage_user" class="text-indigo-600 hover:text-indigo-800 underline">here</a>
				</p>
			</div>

			<!-- Loading state -->
			{#if isLoadingGroups}
				<div class="text-center text-sm text-gray-500 flex items-center justify-center">
					<svg
						class="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-400"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					Loading DOI author groups...
				</div>
			{/if}
		</div>
	</Card>
{/if}
