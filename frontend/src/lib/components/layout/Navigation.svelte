<script>
	import { auth } from '$lib/stores/auth';

	function handleLogout() {
		auth.logout();
	}
</script>

<nav class="bg-white shadow-lg">
	<div class="max-w-7xl mx-auto px-4">
		<div class="flex justify-between h-16">
			<!-- Logo/Brand -->
			<div class="flex items-center">
				<a href="/" class="flex items-center text-xl font-bold text-blue-600">
					<img src="/gwtm_logo.png" width="32" height="32" class="mr-2" alt="GWTM Logo" />
					TM
				</a>
			</div>

			<!-- Main Navigation -->
			<div class="hidden md:flex items-center space-x-8">
				<a href="/" class="nav-link">Home</a>

				<!-- GW Events Dropdown -->
				<div class="relative group">
					<button class="nav-link flex items-center">
						GW Events
						<svg class="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
							<path
								d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
							/>
						</svg>
					</button>
					<div class="nav-dropdown">
						<a href="/alerts/select" class="nav-dropdown-item">Events</a>
						<a href="/alerts/reporting" class="nav-dropdown-item">Reporting Instruments</a>
					</div>
				</div>

				<!-- Query Pages Dropdown -->
				<div class="relative group">
					<button class="nav-link flex items-center">
						Query Pages
						<svg class="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
							<path
								d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
							/>
						</svg>
					</button>
					<div class="nav-dropdown">
						<a href="/search/pointings" class="nav-dropdown-item">Pointings</a>
						<a href="/search/instruments" class="nav-dropdown-item">Instruments</a>
					</div>
				</div>

				<!-- Submit Pages Dropdown -->
				<div class="relative group">
					<button class="nav-link flex items-center">
						Submit Pages
						<svg class="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
							<path
								d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
							/>
						</svg>
					</button>
					<div class="nav-dropdown">
						<a href="/submit/pointings" class="nav-dropdown-item">Pointings</a>
						<a href="/submit/instruments" class="nav-dropdown-item">Instruments</a>
					</div>
				</div>

				<!-- Documentation Dropdown -->
				<div class="relative group">
					<button class="nav-link flex items-center">
						Documentation
						<svg class="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
							<path
								d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
							/>
						</svg>
					</button>
					<div class="nav-dropdown">
						<a href="/documentation" class="nav-dropdown-item">API Documentation</a>
						<a href="/documentation/tutorial" class="nav-dropdown-item">Jupyter Tutorial</a>
						<a href="/documentation/blog" class="nav-dropdown-item">What's New</a>
					</div>
				</div>
			</div>

			<!-- Auth Menu -->
			<div class="flex items-center space-x-4">
				{#if $auth.isAuthenticated}
					<span class="text-gray-700">Welcome, {$auth.user?.username || $auth.user?.email}</span>
					<a href="/manage" class="nav-link">Profile</a>
					<button on:click={handleLogout} class="nav-link">Logout</button>
				{:else}
					<a href="/login" class="nav-link">Login</a>
					<a href="/register" class="btn-base btn-primary btn-md">Register</a>
				{/if}
			</div>
		</div>
	</div>
</nav>
