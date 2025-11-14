<script lang="ts">
	/**
	 * @page Profile/Manage User
	 * @description User profile management page with DOI groups and admin functionality
	 * @category Pages
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 */

	import { onMount } from 'svelte';
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { API_ENDPOINTS } from '$lib/config/api';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import ErrorBoundary from '$lib/components/ui/ErrorBoundary.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';

	// Types
	interface User {
		id: number;
		username: string;
		email: string;
		firstname: string;
		lastname: string;
		verified: boolean;
		api_token?: string;
		datecreated?: string;
	}

	interface DoiAuthorGroup {
		id: number;
		name: string;
		userid: number;
	}

	// State
	let currentUser: User | null = null;
	let doiGroups: DoiAuthorGroup[] = [];
	let allUsers: User[] = [];
	let isAdmin = false;
	let loading = true;
	let error = '';
	let searchTerm = '';

	// Auth store subscription
	$: if ($auth.user) {
		currentUser = $auth.user;
	}

	// Filtered users for admin view
	$: filteredUsers = searchTerm
		? allUsers.filter(
				(user) =>
					user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
					user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
					`${user.lastname},${user.firstname}`.toLowerCase().includes(searchTerm.toLowerCase())
			)
		: allUsers;

	// Load profile data
	async function loadProfileData() {
		if (!$auth.isAuthenticated) {
			goto('/login');
			return;
		}

		try {
			loading = true;
			error = '';

			// Load DOI author groups
			try {
				const doiResponse = await api.client.get(API_ENDPOINTS.doiAuthorGroups);
				doiGroups = doiResponse.data || [];
			} catch (err) {
				console.warn('Failed to load DOI groups:', err);
				doiGroups = [];
			}

			// Check if user is admin and load all users if so
			try {
				const adminResponse = await api.client.get(API_ENDPOINTS.adminUsers);
				if (adminResponse.data) {
					allUsers = adminResponse.data;
					isAdmin = true;
				}
			} catch (err) {
				// Not admin or endpoint doesn't exist
				isAdmin = false;
			}
		} catch (err) {
			console.error('Failed to load profile data:', err);
			error = 'Failed to load profile data';
		} finally {
			loading = false;
		}
	}

	// Resend verification email
	async function resendVerificationEmail() {
		try {
			await api.client.post('/api/v1/auth/resend-verification');
			alert('Verification email sent!');
		} catch (err) {
			console.error('Failed to resend verification email:', err);
			alert('Failed to send verification email');
		}
	}

	// Format date for display
	function formatDate(dateString: string | undefined): string {
		if (!dateString) return 'N/A';
		return new Date(dateString).toLocaleDateString();
	}

	// Lifecycle
	onMount(() => {
		loadProfileData();
	});
</script>

<svelte:head>
	<title>Profile - GWTM</title>
</svelte:head>

<ErrorBoundary>
	<div class="profile-page">
		<PageHeader
			title="User Profile"
			description="Manage your account settings and DOI author groups"
		/>

		{#if loading}
			<div class="loading-container">
				<LoadingSpinner />
				<p>Loading profile data...</p>
			</div>
		{:else if error}
			<div class="error-container">
				<p class="error-message">{error}</p>
				<Button on:click={loadProfileData}>Retry</Button>
			</div>
		{:else if currentUser}
			<!-- User Information -->
			<Card className="user-info-card">
				<h2>User: {currentUser.username}</h2>
				<p><strong>Email:</strong> {currentUser.email}</p>
				<p><strong>Name:</strong> {currentUser.firstname} {currentUser.lastname}</p>

				{#if currentUser.api_token}
					<div class="api-token-section">
						<p><strong>Your API Token:</strong></p>
						<code class="api-token">{currentUser.api_token}</code>
						<p class="api-token-help">Use this token for API authentication. Keep it secure!</p>
					</div>
				{:else}
					<div class="verification-needed">
						<p class="error-text">Your account has not been verified</p>
						<Button on:click={resendVerificationEmail} variant="primary">
							Resend Verification Email
						</Button>
					</div>
				{/if}
			</Card>

			<!-- DOI Author Groups -->
			<Card className="doi-groups-card">
				<div class="section-header">
					<h3>DOI Author Groups</h3>
					<Button href="/doi/author-group" variant="primary">Create New DOI Author Group</Button>
				</div>

				{#if doiGroups.length > 0}
					<div class="doi-groups-table">
						<table class="table">
							<thead>
								<tr>
									<th>ID</th>
									<th>Name</th>
									<th>Actions</th>
								</tr>
							</thead>
							<tbody>
								{#each doiGroups as group (group.id)}
									<tr>
										<td>{group.id}</td>
										<td>{group.name}</td>
										<td>
											<a href="/doi/author-group?id={group.id}" class="link-button"> Edit </a>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No DOI author groups created yet.</p>
				{/if}
			</Card>

			<!-- Admin Section -->
			{#if isAdmin}
				<Card className="admin-section-card">
					<h3>Admin Functionality</h3>
					<h4>Users</h4>

					<!-- Search -->
					<div class="search-container">
						<input
							type="text"
							placeholder="Search users..."
							bind:value={searchTerm}
							class="search-input"
						/>
					</div>

					<!-- Users Table -->
					{#if allUsers.length > 0}
						<div class="users-table">
							<table class="table">
								<thead>
									<tr>
										<th>User ID</th>
										<th>Username</th>
										<th>Last, First</th>
										<th>Email</th>
										<th>Date Created</th>
										<th>Verified?</th>
										<th>Actions</th>
									</tr>
								</thead>
								<tbody>
									{#each filteredUsers as user (user.id)}
										<tr>
											<td>{user.id}</td>
											<td>{user.username}</td>
											<td>{user.lastname}, {user.firstname}</td>
											<td>{user.email}</td>
											<td>{formatDate(user.datecreated)}</td>
											<td>
												<span
													class="verification-badge {user.verified ? 'verified' : 'unverified'}"
												>
													{user.verified ? 'Yes' : 'No'}
												</span>
											</td>
											<td>
												{#if !user.verified}
													<button
														class="resend-button"
														on:click={() => {
															/* TODO: Implement resend for specific user */
														}}
													>
														Resend
													</button>
												{/if}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="empty-state">No users found.</p>
					{/if}
				</Card>
			{/if}
		{/if}
	</div>
</ErrorBoundary>

<style>
	.profile-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	.loading-container,
	.error-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 3rem;
		text-align: center;
	}

	.error-message {
		color: #dc2626;
		margin-bottom: 1rem;
	}

	/* User Info Card */
	.user-info-card h2 {
		color: #111827;
		margin: 0 0 1rem 0;
		font-size: 1.5rem;
	}

	.user-info-card p {
		margin: 0.5rem 0;
		color: #374151;
	}

	.api-token-section {
		margin-top: 1.5rem;
		padding: 1rem;
		background-color: #f3f4f6;
		border-radius: 0.5rem;
	}

	.api-token {
		display: block;
		background-color: #1f2937;
		color: #f9fafb;
		padding: 0.75rem;
		border-radius: 0.375rem;
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 0.875rem;
		margin: 0.5rem 0;
		word-break: break-all;
	}

	.api-token-help {
		font-size: 0.875rem;
		color: #6b7280;
		margin-top: 0.5rem;
	}

	.verification-needed {
		margin-top: 1.5rem;
		padding: 1rem;
		background-color: #fef2f2;
		border: 1px solid #fca5a5;
		border-radius: 0.5rem;
	}

	.error-text {
		color: #dc2626;
		margin-bottom: 1rem;
		font-weight: 500;
	}

	/* DOI Groups Card */
	.section-header {
		display: flex;
		justify-content: between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.section-header h3 {
		margin: 0;
		color: #111827;
		font-size: 1.25rem;
	}

	/* Tables */
	.table {
		width: 100%;
		border-collapse: collapse;
		margin-top: 1rem;
	}

	.table th,
	.table td {
		padding: 0.75rem;
		text-align: left;
		border-bottom: 1px solid #e5e7eb;
	}

	.table th {
		background-color: #f9fafb;
		font-weight: 600;
		color: #374151;
	}

	.table tbody tr:hover {
		background-color: #f9fafb;
	}

	.link-button {
		color: #3b82f6;
		text-decoration: none;
		font-weight: 500;
	}

	.link-button:hover {
		text-decoration: underline;
	}

	/* Search */
	.search-container {
		margin-bottom: 1rem;
	}

	.search-input {
		width: 100%;
		max-width: 300px;
		padding: 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 0.875rem;
	}

	.search-input:focus {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
	}

	/* Verification Badge */
	.verification-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.verification-badge.verified {
		background-color: #dcfce7;
		color: #166534;
	}

	.verification-badge.unverified {
		background-color: #fef2f2;
		color: #dc2626;
	}

	/* Buttons */
	.resend-button {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
		background-color: #3b82f6;
		color: white;
		border: none;
		border-radius: 0.25rem;
		cursor: pointer;
	}

	.resend-button:hover {
		background-color: #2563eb;
	}

	.empty-state {
		text-align: center;
		color: #6b7280;
		padding: 2rem;
		font-style: italic;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.profile-page {
			padding: 1rem;
		}

		.section-header {
			flex-direction: column;
			gap: 1rem;
			align-items: stretch;
		}

		.table {
			font-size: 0.875rem;
		}

		.table th,
		.table td {
			padding: 0.5rem;
		}
	}
</style>
