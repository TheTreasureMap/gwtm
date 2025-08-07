<script lang="ts">
	/**
	 * @component RegisterFormExample
	 * @description Example registration form using the new validation system
	 * @category Forms
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 *
	 * @example
	 * ```svelte
	 * <RegisterFormExample
	 *   onSubmit={handleRegister}
	 *   on:success={handleRegisterSuccess}
	 * />
	 * ```
	 */

	import { createEventDispatcher } from 'svelte';
	import FormField from '../FormField.svelte';
	import Form from '../Form.svelte';
	import { validationSchemas } from '$lib/validation/validators';

	const dispatch = createEventDispatcher<{
		success: { result: any };
		error: { error: string };
	}>();

	/**
	 * Submit handler function
	 */
	export let onSubmit: (data: any) => Promise<{ success: boolean; error?: string; result?: any }>;

	let formData = {
		email: '',
		username: '',
		password: '',
		confirmPassword: '',
		firstName: '',
		lastName: ''
	};

	async function handleFormSubmit(data: typeof formData) {
		// Remove confirmPassword from submission data
		const { confirmPassword: _, ...submitData } = data;

		const result = await onSubmit({
			email: submitData.email,
			password: submitData.password,
			username: submitData.username,
			first_name: submitData.firstName,
			last_name: submitData.lastName
		});

		if (result.success) {
			dispatch('success', { result: result.result });
		} else {
			dispatch('error', { error: result.error || 'Registration failed' });
		}

		return result;
	}
</script>

<Form
	schema={validationSchemas.auth.register}
	bind:data={formData}
	onSubmit={handleFormSubmit}
	submitText="Create Account"
	submitLoadingText="Creating Account..."
>
	<div class="space-y-4">
		<FormField
			name="email"
			label="Email address"
			type="email"
			required
			bind:value={formData.email}
			placeholder="your@email.com"
			helpText="We'll use this email for account verification"
		/>

		<FormField
			name="username"
			label="Username"
			type="text"
			required
			bind:value={formData.username}
			placeholder="username"
			helpText="Letters, numbers, underscores, and dashes only"
		/>

		<FormField
			name="password"
			label="Password"
			type="password"
			required
			bind:value={formData.password}
			placeholder="Password"
			helpText="Must be at least 8 characters with uppercase, lowercase, and numbers"
			validationContext={formData}
		/>

		<FormField
			name="confirmPassword"
			label="Confirm Password"
			type="password"
			required
			bind:value={formData.confirmPassword}
			placeholder="Confirm your password"
			validationContext={formData}
		/>

		<div class="grid grid-cols-2 gap-4">
			<FormField
				name="firstName"
				label="First Name"
				type="text"
				bind:value={formData.firstName}
				placeholder="First Name"
			/>

			<FormField
				name="lastName"
				label="Last Name"
				type="text"
				bind:value={formData.lastName}
				placeholder="Last Name"
			/>
		</div>
	</div>
</Form>
