<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import type { AxiosError } from 'axios';
	import { api } from '$lib/api';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import Form from '$lib/components/forms/Form.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import { validators } from '$lib/validation/validators';

	const token = $page.url.searchParams.get('token') ?? '';

	let formData: Record<string, unknown> = { password: '', confirmPassword: '' };

	async function handleSubmit(data: Record<string, unknown>) {
		try {
			await api.auth.resetPassword(token, data.password as string);
			goto(
				`/login?type=success&message=${encodeURIComponent('Your password has been reset. You can now sign in.')}`
			);
			return { success: true };
		} catch (err) {
			const body = (
				err as AxiosError<{
					message?: string;
					errors?: Array<{ message: string; params?: { field?: string } }>;
				}>
			).response?.data;
			// A validation error on anything but the password means a mangled token.
			const passwordError = body?.errors
				?.find((e) => e.params?.field === 'body.password')
				?.message.replace(/^Value error, /, '');
			const message =
				passwordError ??
				(body?.errors ? 'This reset link is invalid. Please request a new one.' : body?.message);
			return { success: false, error: message || 'Password reset failed. Please try again.' };
		}
	}
</script>

<svelte:head>
	<title>Reset Password - GWTM</title>
	<!-- The reset token is in the URL; keep it out of Referer headers. -->
	<meta name="referrer" content="no-referrer" />
</svelte:head>

<div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<PageHeader
			title="Choose a new password"
			description="Gravitational Wave Treasure Map"
			size="md"
		/>

		{#if !token}
			<ErrorMessage
				message="This reset link is incomplete. Please use the link from your email, or request a new one."
			/>
		{:else}
			<Form onSubmit={handleSubmit} submitText="Reset password" bind:data={formData}>
				<div class="space-y-4">
					<FormField
						name="password"
						label="New password"
						type="password"
						required
						placeholder="Enter a strong password"
						bind:value={formData.password}
						validators={[validators.password({})]}
						helpText="At least 8 characters with uppercase, lowercase, and numbers"
					/>

					<FormField
						name="confirmPassword"
						label="Confirm new password"
						type="password"
						required
						placeholder="Confirm your password"
						bind:value={formData.confirmPassword}
						validators={[validators.confirmPassword('password')]}
						validationContext={formData}
						helpText="Must match the password above"
					/>
				</div>
			</Form>
		{/if}

		<div class="text-center">
			<a href="/forgot-password" class="text-blue-600 hover:text-blue-500">Request a new link</a>
		</div>
	</div>
</div>
