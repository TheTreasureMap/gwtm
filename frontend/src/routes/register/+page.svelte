<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Form from '$lib/components/forms/Form.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import { validators } from '$lib/validation/validators';

	let formData: Record<string, unknown> = {
		email: '',
		username: '',
		password: '',
		confirmPassword: '',
		firstName: '',
		lastName: ''
	};

	// Redirect if already authenticated
	onMount(() => {
		const unsubscribe = auth.subscribe((state) => {
			if (state.isAuthenticated) {
				goto('/');
			}
		});

		return unsubscribe;
	});

	async function handleRegister(data: Record<string, unknown>) {
		const result = await auth.register({
			email: data.email as string,
			password: data.password as string,
			username: data.username as string,
			first_name: data.firstName as string,
			last_name: data.lastName as string
		});

		if (result.success) {
			goto('/login?message=Registration successful! You can now log in with your credentials.');
			return { success: true };
		} else {
			return { success: false, error: result.error || 'Registration failed' };
		}
	}
</script>

<svelte:head>
	<title>Register - GWTM</title>
</svelte:head>

<div
	class="min-h-screen bg-gray-50 flex items-center justify-center py-8 px-4 sm:py-12 sm:px-6 lg:px-8"
>
	<div class="max-w-md w-full space-y-8">
		<PageHeader
			title="Create Account"
			description="Join the Gravitational Wave Treasure Map community to coordinate astronomical observations"
			size="md"
		/>

		<Form onSubmit={handleRegister} submitText="Create Account" bind:data={formData}>
			<div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
				<div class="flex">
					<div class="flex-shrink-0">
						<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
							<path
								fill-rule="evenodd"
								d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<div class="ml-3">
						<p class="text-sm text-blue-700">
							After registration, we'll send a verification email to confirm your address. You'll
							need to verify before you can log in.
						</p>
					</div>
				</div>
			</div>

			<div class="space-y-4">
				<FormField
					name="email"
					label="Email address"
					type="email"
					required
					placeholder="your@email.com"
					bind:value={formData.email}
					validators={[validators.email()]}
					helpText="We'll send a verification link to this address"
				/>

				<FormField
					name="username"
					label="Username"
					type="text"
					required
					placeholder="Choose a unique username"
					bind:value={formData.username}
					validators={[
						validators.minLength(3, 'Username must be at least 3 characters'),
						validators.maxLength(50, 'Username must be less than 50 characters'),
						validators.pattern(
							/^[a-zA-Z0-9_-]+$/,
							'Username can only contain letters, numbers, underscores, and dashes'
						),
						validators.safe()
					]}
					helpText="3-50 characters, letters, numbers, underscores, and dashes only"
				/>

				<FormField
					name="password"
					label="Password"
					type="password"
					required
					placeholder="Enter a strong password"
					bind:value={formData.password}
					validators={[validators.password({})]}
					helpText="At least 8 characters with uppercase, lowercase, and numbers"
				/>

				<FormField
					name="confirmPassword"
					label="Confirm Password"
					type="password"
					required
					placeholder="Confirm your password"
					bind:value={formData.confirmPassword}
					validators={[validators.confirmPassword('password')]}
					validationContext={formData}
					helpText="Must match the password above"
				/>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<FormField
						name="firstName"
						label="First Name"
						type="text"
						placeholder="Optional"
						bind:value={formData.firstName}
						validators={[
							validators.maxLength(100, 'First name must be less than 100 characters'),
							validators.safe()
						]}
					/>

					<FormField
						name="lastName"
						label="Last Name"
						type="text"
						placeholder="Optional"
						bind:value={formData.lastName}
						validators={[
							validators.maxLength(100, 'Last name must be less than 100 characters'),
							validators.safe()
						]}
					/>
				</div>
			</div>
		</Form>

		<div class="text-center space-y-4">
			<div class="text-xs text-gray-500">
				By creating an account, you agree to participate in the GWTM collaborative observation
				network. Your contact information will be used solely for coordination purposes.
			</div>

			<div>
				<a href="/login" class="text-blue-600 hover:text-blue-500 font-medium">
					Already have an account? Sign in
				</a>
			</div>
		</div>
	</div>
</div>
