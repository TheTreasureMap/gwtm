<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	let loading = true;
	let error = '';
	let success = false;
	let message = '';

	onMount(async () => {
		const token = $page.url.searchParams.get('token');

		if (!token) {
			error = 'Invalid verification link. Please check your email for the correct link.';
			loading = false;
			return;
		}

		try {
			const response = await fetch('/api/v1/auth/verify-email', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					verification_token: token
				})
			});

			const data = await response.json();

			if (response.ok && data.verified) {
				success = true;
				message = data.message || 'Email verified successfully! You can now log in.';

				// Redirect to login after a short delay
				setTimeout(() => {
					goto('/login?message=' + encodeURIComponent('Account verified! You can now log in.'));
				}, 3000);
			} else {
				error = data.detail || data.message || 'Email verification failed. Please try again.';
			}
		} catch (err) {
			console.error('Verification error:', err);
			error = 'Network error. Please check your connection and try again.';
		} finally {
			loading = false;
		}
	});

	function handleResendVerification() {
		// You could implement resend logic here if needed
		goto(
			'/login?message=' +
				encodeURIComponent(
					'Please try logging in or contact support if you continue to have issues.'
				)
		);
	}
</script>

<svelte:head>
	<title>Email Verification - GWTM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<PageHeader
			title="Email Verification"
			description="Gravitational Wave Treasure Map"
			size="md"
		/>

		<div class="mt-8">
			{#if loading}
				<div class="text-center">
					<div class="inline-flex items-center px-4 py-2 text-sm leading-6 text-gray-500">
						<svg
							class="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							></path>
						</svg>
						Verifying your email address...
					</div>
				</div>
			{:else if success}
				<div class="text-center space-y-4">
					<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
						<svg
							class="h-6 w-6 text-green-600"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M5 13l4 4L19 7"
							></path>
						</svg>
					</div>
					<div>
						<h3 class="text-lg font-medium text-gray-900">Email Verified Successfully!</h3>
						<p class="mt-2 text-sm text-gray-600">{message}</p>
						<p class="mt-2 text-sm text-gray-500">
							You will be redirected to the login page shortly...
						</p>
					</div>
					<Button href="/login" variant="primary">Continue to Login</Button>
				</div>
			{:else if error}
				<div class="space-y-4">
					<ErrorMessage message={error} />
					<div class="space-y-2">
						<Button on:click={handleResendVerification} variant="secondary" fullWidth>
							Go to Login
						</Button>
						<div class="text-center">
							<a href="/register" class="text-sm text-blue-600 hover:text-blue-500">
								Need to register? Create account
							</a>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
