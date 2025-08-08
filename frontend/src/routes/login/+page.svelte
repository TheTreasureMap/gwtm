<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	let username = '';
	let password = '';
	let rememberMe = false;
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

	async function handleLogin() {
		if (!username || !password) {
			error = 'Please fill in all fields';
			return;
		}

		loading = true;
		error = '';

		const result = await auth.login(username, password, rememberMe);

		if (result.success) {
			goto('/');
		} else {
			error = result.error || 'Login failed';
			loading = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleLogin();
		}
	}
</script>

<svelte:head>
	<title>Login - GWTM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<PageHeader title="Sign in to GWTM" description="Gravitational Wave Treasure Map" size="md" />

		<form class="mt-8 space-y-6" on:submit|preventDefault={handleLogin}>
			<div class="rounded-md shadow-sm -space-y-px">
				<div>
					<label for="username" class="sr-only">Username or Email</label>
					<input
						id="username"
						name="username"
						type="text"
						required
						bind:value={username}
						on:keydown={handleKeydown}
						class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none
  focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
						placeholder="Username or Email"
					/>
				</div>
				<div>
					<label for="password" class="sr-only">Password</label>
					<input
						id="password"
						name="password"
						type="password"
						required
						bind:value={password}
						on:keydown={handleKeydown}
						class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none
  focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
						placeholder="Password"
					/>
				</div>
			</div>

			<div class="flex items-center justify-between">
				<div class="flex items-center">
					<input
						id="remember-me"
						name="remember-me"
						type="checkbox"
						bind:checked={rememberMe}
						class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
					/>
					<label for="remember-me" class="ml-2 block text-sm text-gray-900">
						Remember me
					</label>
				</div>
			</div>

			{#if error}
				<ErrorMessage message={error} />
			{/if}

			<div>
				<Button type="submit" disabled={loading} {loading} fullWidth={true}>
					{loading ? 'Signing in...' : 'Sign in'}
				</Button>
			</div>

			<div class="text-center">
				<a href="/register" class="text-blue-600 hover:text-blue-500">
					Don't have an account? Register here
				</a>
			</div>
		</form>
	</div>
</div>
