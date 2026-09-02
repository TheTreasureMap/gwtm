<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { doiService } from '$lib/api/services/doi.service';
	import type { DOIAuthorInput } from '$lib/api/types/doi.types';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	// Derived from ?id= query param
	let groupId: number | null = null;
	let isEdit = false;

	let groupName = '';
	let authors: DOIAuthorInput[] = [];
	let loading = true;
	let saving = false;
	let error = '';

	function emptyAuthor(): DOIAuthorInput {
		return { name: '', affiliation: '', orcid: '', gnd: '' };
	}

	function addRow() {
		authors = [...authors, emptyAuthor()];
	}

	function removeRow(index: number) {
		authors = authors.filter((_, i) => i !== index);
	}

	function validate(): string {
		if (!groupName.trim()) return 'Group name is required.';
		for (const [i, a] of authors.entries()) {
			if (!a.name.trim()) return `Row ${i + 1}: author name is required.`;
			if (!a.affiliation.trim()) return `Row ${i + 1}: affiliation is required.`;
		}
		return '';
	}

	async function handleSave() {
		error = validate();
		if (error) return;

		saving = true;
		try {
			const payload = {
				name: groupName.trim(),
				authors: authors.map((a) => ({
					...(a.id != null ? { id: a.id } : {}),
					name: a.name.trim(),
					affiliation: a.affiliation.trim(),
					orcid: a.orcid?.trim() || undefined,
					gnd: a.gnd?.trim() || undefined
				}))
			};

			if (isEdit && groupId !== null) {
				await doiService.updateDOIAuthorGroup(groupId, payload);
			} else {
				await doiService.createDOIAuthorGroup(payload);
			}
			goto('/manage');
		} catch (err: unknown) {
			const e = err as { response?: { data?: { detail?: string } } };
			error = e?.response?.data?.detail || 'Failed to save. Please try again.';
		} finally {
			saving = false;
		}
	}

	onMount(async () => {
		if (!$auth.isAuthenticated) {
			goto('/login');
			return;
		}

		const idParam = $page.url.searchParams.get('id');
		if (idParam) {
			groupId = parseInt(idParam, 10);
			isEdit = true;
			try {
				const [groups, authorList] = await Promise.all([
					doiService.getDOIAuthorGroups(),
					doiService.getDOIAuthors(groupId)
				]);
				const group = groups.find((g) => g.id === groupId);
				if (!group) {
					error = 'Author group not found.';
					loading = false;
					return;
				}
				groupName = group.name;
				authors = authorList.map((a) => ({
					id: a.id,
					name: a.name,
					affiliation: a.affiliation,
					orcid: a.orcid ?? '',
					gnd: a.gnd ?? ''
				}));
			} catch {
				error = 'Failed to load author group.';
			}
		} else {
			authors = [emptyAuthor()];
		}
		loading = false;
	});
</script>

<svelte:head>
	<title>{isEdit ? 'Edit' : 'Create'} DOI Author Group - GWTM</title>
</svelte:head>

<div class="page">
	<PageHeader
		title="{isEdit ? 'Edit' : 'Create'} DOI Author Group"
		description="Define a reusable list of authors for DOI submissions"
		size="md"
	/>

	{#if loading}
		<div class="center"><LoadingSpinner /></div>
	{:else}
		{#if error}
			<ErrorMessage message={error} />
		{/if}

		<div class="card">
			<div class="field">
				<label for="group-name">Group Name <span class="required">*</span></label>
				<input
					id="group-name"
					type="text"
					bind:value={groupName}
					placeholder="e.g. My Collaboration Team"
					class="input"
				/>
			</div>

			<table class="author-table">
				<thead>
					<tr>
						<th>Name <span class="required">*</span></th>
						<th>Affiliation <span class="required">*</span></th>
						<th>ORCID</th>
						<th>GND</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					{#each authors as author, i (i)}
						<tr>
							<td
								><input
									type="text"
									bind:value={author.name}
									placeholder="Full name"
									class="input"
								/></td
							>
							<td
								><input
									type="text"
									bind:value={author.affiliation}
									placeholder="Institution"
									class="input"
								/></td
							>
							<td
								><input
									type="text"
									bind:value={author.orcid}
									placeholder="0000-0000-0000-0000"
									class="input"
								/></td
							>
							<td
								><input
									type="text"
									bind:value={author.gnd}
									placeholder="GND ID"
									class="input"
								/></td
							>
							<td>
								<button
									type="button"
									class="remove-btn"
									on:click={() => removeRow(i)}
									aria-label="Remove row"
								>
									✕
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>

			<p class="hint">* required fields</p>

			<div class="row-actions">
				<Button variant="secondary" on:click={addRow}>+ Add Author</Button>
			</div>

			<div class="form-actions">
				<Button variant="secondary" href="/manage">Cancel</Button>
				<Button variant="primary" on:click={handleSave} disabled={saving}>
					{saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Group'}
				</Button>
			</div>
		</div>
	{/if}
</div>

<style>
	.page {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
	}

	.center {
		display: flex;
		justify-content: center;
		padding: 3rem;
	}

	.card {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		padding: 1.5rem;
		margin-top: 1.5rem;
	}

	.field {
		margin-bottom: 1.5rem;
	}

	.field label {
		display: block;
		font-weight: 600;
		color: #374151;
		margin-bottom: 0.375rem;
	}

	.input {
		width: 100%;
		padding: 0.5rem 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		box-sizing: border-box;
	}

	.input:focus {
		outline: 2px solid #3b82f6;
		outline-offset: 1px;
	}

	.author-table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 0.5rem;
	}

	.author-table th {
		text-align: left;
		padding: 0.5rem 0.5rem 0.5rem 0;
		font-size: 0.8rem;
		font-weight: 600;
		color: #6b7280;
		border-bottom: 1px solid #e5e7eb;
	}

	.author-table td {
		padding: 0.375rem 0.5rem 0.375rem 0;
		vertical-align: middle;
	}

	.author-table td:last-child {
		width: 2rem;
	}

	.remove-btn {
		background: none;
		border: none;
		color: #ef4444;
		cursor: pointer;
		font-size: 1rem;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
	}

	.remove-btn:hover {
		background-color: #fef2f2;
	}

	.hint {
		font-size: 0.75rem;
		color: #9ca3af;
		margin: 0.25rem 0 1rem;
	}

	.required {
		color: #ef4444;
	}

	.row-actions {
		margin-bottom: 1.5rem;
	}

	.form-actions {
		display: flex;
		gap: 0.75rem;
		justify-content: flex-end;
		padding-top: 1rem;
		border-top: 1px solid #e5e7eb;
	}
</style>
