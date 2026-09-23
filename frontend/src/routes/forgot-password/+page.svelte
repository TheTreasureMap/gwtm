<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { AxiosError } from 'axios';
	import { auth } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import Form from '$lib/components/forms/Form.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import Turnstile from '$lib/components/forms/Turnstile.svelte';
	import { validators } from '$lib/validation/validators';

	let turnstileSiteKey = '';
	let turnstile: Turnstile;
	let turnstileToken = '';
	let sentMessage = '';

	let formData: Record<string, unknown> = { email: '' };

	onMount(() => {
		api.auth
			.getCaptchaConfig()
			.then((response) => (turnstileSiteKey = response.data.turnstile_site_key))
			.catch((err) => console.error('Failed to load captcha config:', err));

		return auth.subscribe((state) => {
			if (state.isAuthenticated) {
				goto('/');
			}
		});
	});

	async function handleSubmit(data: Record<string, unknown>) {
		if (turnstileSiteKey && !turnstileToken) {
			return { success: false, error: 'Please complete the captcha challenge.' };
		}

		try {
			const response = await api.auth.forgotPassword(
				data.email as string,
				turnstileToken || undefined
			);
			sentMessage = response.data.message;
			return { success: true };
		} catch (err) {
			turnstile?.reset();
			const message = (err as AxiosError<{ message?: string }>).response?.data?.message;
			return { success: false, error: message || 'Something went wrong. Please try again.' };
		}
	}
</script>

<svelte:head>
	<title>Forgot Password - GWTM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<PageHeader
			title="Forgot your password?"
			description="Enter your account's email address and we'll send you a link to reset it."
			size="md"
		/>

		{#if sentMessage}
			<ErrorMessage message={sentMessage} type="info" title="Check your email" />
		{:else}
			<Form onSubmit={handleSubmit} submitText="Send reset link" bind:data={formData}>
				<div class="space-y-4">
					<FormField
						name="email"
						label="Email address"
						type="email"
						required
						placeholder="your@email.com"
						bind:value={formData.email}
						validators={[validators.email()]}
					/>

					{#if turnstileSiteKey}
						<Turnstile
							bind:this={turnstile}
							bind:token={turnstileToken}
							siteKey={turnstileSiteKey}
						/>
					{/if}
				</div>
			</Form>
		{/if}

		<div class="text-center">
			<a href="/login" class="text-blue-600 hover:text-blue-500">Back to sign in</a>
		</div>
	</div>
</div>
