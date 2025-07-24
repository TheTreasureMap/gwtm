<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth, authActions } from '$lib/stores/auth';

	let email = '';
	let password = '';
	let username = '';
	let firstName = '';
	let lastName = '';
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
		if (!email || !password || !username) {
			error = 'Please fill in all required fields';
			return;
		}

		loading = true;
		error = '';

		const result = await authActions.register({
			email,
			password,
			username,
			first_name: firstName,
			last_name: lastName
		});

		if (result.success) {
			goto('/login?message=Registration successful! Please login.');
		} else {
			error = result.error;
			loading = false;
		}
	}

	function handleKeydown(event) {
		if (event.key === 'Enter') {
			handleRegister();
		}
	}
</script>

<svelte:head>
	<title>Register - GWTM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
	<div class="max-w-md w-full space-y-8">
		<div>
			<h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">Create Account</h2>
			<p class="mt-2 text-center text-sm text-gray-600">
				Join the Gravitational Wave Treasure Map community
			</p>
		</div>

		<form class="mt-8 space-y-6" on:submit|preventDefault={handleRegister}>
			<div class="space-y-4">
				<div>
					<label for="email" class="block text-sm font-medium text-gray-700">Email address *</label>
					<input
						id="email"
						type="email"
						required
						bind:value={email}
						on:keydown={handleKeydown}
						placeholder="your@email.com"
						class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>

				<div>
					<label for="username" class="block text-sm font-medium text-gray-700">Username *</label>
					<input
						id="username"
						type="text"
						required
						bind:value={username}
						on:keydown={handleKeydown}
						placeholder="username"
						class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>

				<div>
					<label for="password" class="block text-sm font-medium text-gray-700">Password *</label>
					<input
						id="password"
						type="password"
						required
						bind:value={password}
						on:keydown={handleKeydown}
						placeholder="Password"
						class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div>
						<label for="firstName" class="block text-sm font-medium text-gray-700">First Name</label
						>
						<input
							id="firstName"
							type="text"
							bind:value={firstName}
							on:keydown={handleKeydown}
							placeholder="First Name"
							class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
						/>
					</div>

					<div>
						<label for="lastName" class="block text-sm font-medium text-gray-700">Last Name</label>
						<input
							id="lastName"
							type="text"
							bind:value={lastName}
							on:keydown={handleKeydown}
							placeholder="Last Name"
							class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
						/>
					</div>
				</div>
			</div>

			{#if error}
				<div class="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
					{error}
				</div>
			{/if}

			<button
				type="submit"
				disabled={loading}
				class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md disabled:opacity-50 transition-colors"
			>
				{loading ? 'Creating Account...' : 'Create Account'}
			</button>

			<div class="text-center">
				<a href="/login" class="text-blue-600 hover:text-blue-500">
					Already have an account? Sign in
				</a>
			</div>
		</form>
	</div>
</div>
