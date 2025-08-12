<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import { useFormValidation } from '$lib/hooks/useFormValidation';
	import { validationSchemas, validators } from '$lib/validation/validators';

	// Form data
	interface RegistrationFormData {
		email: string;
		username: string;
		password: string;
		confirmPassword: string;
		firstName: string;
		lastName: string;
	}

	// Initialize form validation
	const formValidation = useFormValidation<RegistrationFormData>({
		schema: {
			email: {
				required: true,
				validators: [validators.email()]
			},
			username: {
				required: true,
				validators: [
					validators.minLength(3, 'Username must be at least 3 characters'),
					validators.maxLength(50, 'Username must be less than 50 characters'),
					validators.pattern(
						/^[a-zA-Z0-9_-]+$/,
						'Username can only contain letters, numbers, underscores, and dashes'
					),
					validators.safe()
				]
			},
			password: {
				required: true,
				validators: [validators.password({})]
			},
			confirmPassword: {
				required: true,
				validators: [validators.confirmPassword('password')],
				dependsOn: ['password']
			},
			firstName: {
				validators: [
					validators.maxLength(100, 'First name must be less than 100 characters'),
					validators.safe()
				]
			},
			lastName: {
				validators: [
					validators.maxLength(100, 'Last name must be less than 100 characters'),
					validators.safe()
				]
			}
		},
		initialValues: {
			email: '',
			username: '',
			password: '',
			confirmPassword: '',
			firstName: '',
			lastName: ''
		}
	});

	// Destructure stores for easier access
	const { values, errors, isValid, isValidating } = formValidation;

	let error = '';
	let loading = false;

	// Redirect if already authenticated
	onMount(() => {
		const unsubscribe = auth.subscribe((state) => {
			if (state.isAuthenticated) {
				goto('/');
			}
		});

		return unsubscribe;
	});

	async function handleRegister() {
		// Validate all fields before submission
		if (!formValidation.validateAll()) {
			error = 'Please fix the errors above before submitting.';
			return;
		}

		loading = true;
		error = '';

		const result = await auth.register({
			email: $values.email,
			password: $values.password,
			username: $values.username,
			first_name: $values.firstName,
			last_name: $values.lastName
		});

		if (result.success) {
			goto(
				'/login?message=Registration successful! Please check your email to verify your account.'
			);
		} else {
			error = result.error || 'Registration failed';
			loading = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleRegister();
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

		<form class="mt-8 space-y-6" on:submit|preventDefault={handleRegister} novalidate>
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
					value={$values.email}
					externalErrors={$errors.email || []}
					validationContext={$values}
					helpText="We'll send a verification link to this address"
					on:change={({ detail }) => formValidation.setFieldValue('email', detail.value)}
					on:keydown={handleKeydown}
				/>

				<FormField
					name="username"
					label="Username"
					type="text"
					required
					placeholder="Choose a unique username"
					value={$values.username}
					externalErrors={$errors.username || []}
					helpText="3-50 characters, letters, numbers, underscores, and dashes only"
					on:change={({ detail }) => formValidation.setFieldValue('username', detail.value)}
					on:keydown={handleKeydown}
				/>

				<FormField
					name="password"
					label="Password"
					type="password"
					required
					placeholder="Enter a strong password"
					value={$values.password}
					externalErrors={$errors.password || []}
					helpText="At least 8 characters with uppercase, lowercase, and numbers"
					on:change={({ detail }) => formValidation.setFieldValue('password', detail.value)}
					on:keydown={handleKeydown}
				/>

				<FormField
					name="confirmPassword"
					label="Confirm Password"
					type="password"
					required
					placeholder="Confirm your password"
					value={$values.confirmPassword}
					externalErrors={$errors.confirmPassword || []}
					validationContext={$values}
					helpText="Must match the password above"
					on:change={({ detail }) => formValidation.setFieldValue('confirmPassword', detail.value)}
					on:keydown={handleKeydown}
				/>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<FormField
						name="firstName"
						label="First Name"
						type="text"
						placeholder="Optional"
						value={$values.firstName}
						externalErrors={$errors.firstName || []}
						on:change={({ detail }) => formValidation.setFieldValue('firstName', detail.value)}
						on:keydown={handleKeydown}
					/>

					<FormField
						name="lastName"
						label="Last Name"
						type="text"
						placeholder="Optional"
						value={$values.lastName}
						externalErrors={$errors.lastName || []}
						on:change={({ detail }) => formValidation.setFieldValue('lastName', detail.value)}
						on:keydown={handleKeydown}
					/>
				</div>
			</div>

			{#if error}
				<ErrorMessage message={error} />
			{/if}

			<Button
				type="submit"
				disabled={loading || $isValidating || !$isValid}
				{loading}
				fullWidth={true}
			>
				{loading ? 'Creating Account...' : 'Create Account'}
			</Button>

			{#if !$isValid && Object.keys($errors).length > 0}
				<div class="text-center text-sm text-gray-600">
					Please complete all required fields to continue
				</div>
			{/if}

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
		</form>
	</div>
</div>
