<script lang="ts">
	/**
	 * @component LoginFormExample
	 * @description Example login form using the new validation system
	 * @category Forms
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 *
	 * @example
	 * ```svelte
	 * <LoginFormExample
	 *   onSubmit={handleLogin}
	 *   on:success={handleLoginSuccess}
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
	 * @type {(data: {email: string, password: string}) => Promise<{success: boolean, error?: string, result?: any}>}
	 */
	export let onSubmit: (data: {
		email: string;
		password: string;
	}) => Promise<{ success: boolean; error?: string; result?: any }>;

	let formData = {
		email: '',
		password: ''
	};

	async function handleFormSubmit(data: typeof formData) {
		const result = await onSubmit(data);

		if (result.success) {
			dispatch('success', { result: result.result });
		} else {
			dispatch('error', { error: result.error || 'Login failed' });
		}

		return result;
	}
</script>

<Form
	schema={validationSchemas.auth.login}
	bind:data={formData}
	onSubmit={handleFormSubmit}
	submitText="Sign in"
	submitLoadingText="Signing in..."
>
	<div class="space-y-4">
		<FormField
			name="email"
			label="Email address"
			type="email"
			required
			bind:value={formData.email}
			placeholder="Enter your email"
		/>

		<FormField
			name="password"
			label="Password"
			type="password"
			required
			bind:value={formData.password}
			placeholder="Enter your password"
		/>
	</div>
</Form>
