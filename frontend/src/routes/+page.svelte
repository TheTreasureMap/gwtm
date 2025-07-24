<script>
	import { auth } from '$lib/stores/auth';
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
</script>

<svelte:head>
	<title>Gravitational Wave Treasure Map</title>
</svelte:head>

<!-- Hero Section -->
<div class="bg-gradient-to-b from-blue-50 to-white">
	<PageContainer>
		<!-- API Notice -->
		<div class="bg-blue-100 border border-blue-200 rounded-lg p-4 mb-8">
			<p class="text-center text-blue-800">
				<span class="font-semibold">Now Available!</span> Our
				<code class="bg-blue-200 px-1 rounded">python</code>
				API wrapper:
				<a
					href="https://github.com/TheTreasureMap/gwtm_api"
					class="text-blue-600 hover:text-blue-800 underline">gwtm_api</a
				>.
			</p>
		</div>

		<div class="grid lg:grid-cols-3 gap-8 items-center">
			<!-- Main Content -->
			<div class="lg:col-span-2">
				<h1 class="text-5xl font-bold text-gray-900 mb-6">Treasure Map</h1>

				<div class="space-y-6 text-lg text-gray-700">
					<p class="leading-relaxed">
						Welcome! The Treasure Map is designed to help coordinate electromagnetic followup of
						gravitational-wave (GW) events. It allows observers to easily report their planned and
						executed observations in search of counterparts to GW events, and to query the reports
						of other observers, in a programmatic way. The goal is to enable coordination between
						observatories in order to minimize unnecessary overlap in these searches, and find the
						counterpart as quickly and as efficiently as possible.
					</p>

					<p class="leading-relaxed">
						Please <a
							href="/register"
							class="font-semibold text-blue-600 hover:text-blue-800 underline">register</a
						>
						for an account, so that you can programmatically query the Treasure Map. For more details
						on how to use the Treasure Map see our
						<a
							href="/documentation"
							class="font-semibold text-blue-600 hover:text-blue-800 underline">User Guide</a
						>.
					</p>

					<p class="text-base">
						Please direct any general inquiries to <a
							href="mailto:arcavi@tauex.tau.ac.il?cc=swyatt@arizona.edu&subject=GWTM%20Inquiry"
							class="text-blue-600 hover:text-blue-800 underline">Iair Arcavi</a
						>. If you use the Treasure Map in your research, please cite the
						<a
							href="https://ui.adsabs.harvard.edu/abs/2020ApJ...894..127W/abstract"
							class="text-blue-600 hover:text-blue-800 underline">Treasure Map paper</a
						>
						in addition to the circulars and/or papers of the teams whose pointing information you use.
					</p>
				</div>
			</div>

			<!-- Visualization Card -->
			<Card padding="none" hover={true}>
				<div class="bg-gray-200 h-48 flex items-center justify-center">
					<div class="text-center text-gray-500">
						<svg
							class="w-16 h-16 mx-auto mb-2"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
							/>
						</svg>
						<p class="text-sm">GW Visualization</p>
					</div>
				</div>
				<div class="p-6">
					<h3 class="text-xl font-semibold mb-3">Visualization</h3>
					<ul class="space-y-2 text-gray-600">
						<li>• Visualize GW alert contours</li>
						<li>• Submit your follow-up pointings</li>
						<li>• Collaborate with the counterpart search community</li>
						<li>• Analyze follow-up</li>
					</ul>
				</div>
				<div class="px-6 py-3 bg-gray-50">
					<small class="text-gray-500"
						>Images from <a
							href="/alerts?graceids=GW190814"
							class="text-blue-600 hover:text-blue-800">GW190814</a
						></small
					>
				</div>
			</Card>
		</div>

		<!-- Explore Button -->
		<div class="text-center mt-12">
			<p class="text-lg mb-4">Explore all GW alerts</p>
			<Button href="/alerts/select" size="lg">
				Browse Events
			</Button>
		</div>
	</PageContainer>
</div>

<!-- Action Cards -->
<PageContainer>
	<div class="grid md:grid-cols-3 gap-8">
		<!-- Register Card -->
		<Card padding="none" hover={true}>
			<div
				class="h-48 bg-gradient-to-br from-green-100 to-green-200 flex items-center justify-center"
			>
				<svg class="w-20 h-20 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
					/>
				</svg>
			</div>
			<div class="p-6">
				<h3 class="text-xl font-semibold mb-3">
					<a href="/register" class="text-blue-600 hover:text-blue-800">Register</a> a new account
				</h3>
				<p class="text-gray-600">
					Once registered and verified, you may begin interacting with the Treasure Map API and
					begin assisting the community's search for GW counterparts.
				</p>
			</div>
		</Card>

		<!-- Submit Instruments Card -->
		<Card padding="none" hover={true}>
			<div
				class="h-48 bg-gradient-to-br from-purple-100 to-purple-200 flex items-center justify-center"
			>
				<svg
					class="w-20 h-20 text-purple-600"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
					/>
				</svg>
			</div>
			<div class="p-6">
				<h3 class="text-xl font-semibold mb-3">
					<a href="/submit/instrument" class="text-blue-600 hover:text-blue-800">Submit</a> your follow-up
					instruments
				</h3>
				<p class="text-gray-600">
					If you are planning to follow-up gravitational wave alerts, we urge you to submit your
					instrument footprint to our database, so that you can let the community know about your GW
					follow-up efforts.
				</p>
			</div>
		</Card>

		<!-- API Integration Card -->
		<Card padding="none" hover={true}>
			<div
				class="h-48 bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center"
			>
				<svg class="w-20 h-20 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
					/>
				</svg>
			</div>
			<div class="p-6">
				<h3 class="text-xl font-semibold mb-3">
					<a href="/documentation" class="text-blue-600 hover:text-blue-800">Integrate</a> our API
				</h3>
				<p class="text-gray-600">
					Our API has endpoints for querying and posting telescope pointings for every GW event. The
					more users that <em>at least</em> submit their planned/completed observing strategies can lead
					to more and quicker discoveries!
				</p>
			</div>
		</Card>
	</div>
</PageContainer>
