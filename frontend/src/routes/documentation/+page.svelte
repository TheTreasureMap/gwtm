<script>
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Card from '$lib/components/ui/Card.svelte';
</script>

<svelte:head>
	<title>Documentation - GWTM</title>
</svelte:head>

<PageContainer>
	<PageHeader
		title="Documentation"
		description="Communicating with the Treasure Map to either report or get information is best done programmatically through the API using POST and GET methods. However, you can also use the pages on this website to report and get information."
	/>

	<!-- API Notice -->
	<div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
		<div class="text-center">
			<p class="text-xl text-blue-800 mb-2">
				<strong
					>Newly released is our <code class="bg-blue-200 px-1 rounded">python</code> API wrapper:</strong
				>
				<a
					href="https://github.com/TheTreasureMap/gwtm_api"
					class="text-blue-600 hover:text-blue-800 underline font-semibold">gwtm_api</a
				>
			</p>
			<p class="text-blue-700">
				It fully encompasses the API endpoints, while also providing event tools to further aid in
				GW follow-up
			</p>
		</div>
	</div>

	<!-- API Versions -->
	<Card>
		<h2 class="text-2xl font-semibold mb-4">API Versions</h2>
		<p class="mb-4">
			We have two versions of the API. <strong>We recommend using <em>/api/v1</em></strong>
		</p>

		<div class="space-y-3">
			<div class="bg-yellow-50 border border-yellow-200 rounded p-4">
				<p class="text-yellow-800">
					<strong>Important:</strong> You must use <code>https://treasuremap.space</code> as your
					API base URL. Using <em>http</em> will result in an error.
				</p>
			</div>

			<div class="bg-blue-50 border border-blue-200 rounded p-4">
				<p class="text-blue-800">
					<strong>/api/v0:</strong> This version's GET responses <strong>does not</strong> return valid
					JSON. When iterating over results, you'd have to json.parse() each result in the result list.
				</p>
			</div>

			<div class="bg-blue-50 border border-blue-200 rounded p-4">
				<p class="text-blue-800">
					<strong>/api/v1:</strong> This version's GET responses returns valid JSON. You only have to
					perform json.parse(request.text) once then iterate over the JSON objects as expected.
				</p>
			</div>
		</div>
	</Card>

	<!-- Quick Links -->
	<div class="grid md:grid-cols-2 gap-6 mb-8">
		<Card>
			<h3 class="text-xl font-semibold mb-4 flex items-center">
				<svg
					class="w-6 h-6 mr-2 text-blue-600"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
					/>
				</svg>
				Interactive API Documentation
			</h3>
			<p class="text-gray-600 mb-4">
				Explore and test all API endpoints with our auto-generated documentation.
			</p>
			<a
				href="/docs"
				target="_blank"
				class="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
			>
				Open API Docs →
			</a>
		</Card>

		<Card>
			<h3 class="text-xl font-semibold mb-4 flex items-center">
				<svg
					class="w-6 h-6 mr-2 text-green-600"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
					/>
				</svg>
				Python API Wrapper
			</h3>
			<p class="text-gray-600 mb-4">
				Use our Python library for easier integration with the Treasure Map API.
			</p>
			<a
				href="https://github.com/TheTreasureMap/gwtm_api"
				target="_blank"
				class="inline-block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
			>
				View on GitHub →
			</a>
		</Card>
	</div>

	<!-- Use Cases -->
	<Card>
		<h2 class="text-2xl font-semibold mb-6">API Use Cases</h2>

		<div class="space-y-8">
			<!-- Use Case 1 -->
			<div>
				<h3 class="text-xl font-semibold text-blue-600 mb-3">
					1. I am an observer and I would like to report my observations
				</h3>
				<div class="pl-4 border-l-4 border-blue-200">
					<p class="mb-4">
						Great! Before you can start you must register an account through this website. Then you
						will be issued a token that you will use to post your reports.
					</p>
					<p class="mb-4">
						Once you have an account, also please check whether your imaging instrument is listed
						(either on the <a
							href="/search/instruments"
							class="text-blue-600 hover:text-blue-800 underline">website</a
						>
						or by using the instruments GET method), and make a note of its ID. If it isn't listed, please
						submit it.
					</p>

					<div class="bg-gray-50 rounded p-4 mb-4">
						<p class="font-semibold mb-2">Typical workflow:</p>
						<p class="text-sm mb-2">
							<strong>Note:</strong> You may test your <em>POST</em> scripts using test events
							listed
							<a
								href="/alerts/select?role=test&observing_run=O4"
								class="text-blue-600 hover:text-blue-800 underline">here</a
							>.
						</p>
						<ol class="list-decimal list-inside space-y-2 text-sm">
							<li>
								A GW alert comes in, and you decide on a list of pointings to observe with your
								telescope.
							</li>
							<li>
								You send this list of pointings using the pointings POST method, with a status of <strong
									>planned</strong
								>.
							</li>
							<li>
								As you observe your pointings, send them with a status of <strong>completed</strong
								>.
							</li>
							<li>For validation, you can request a DOI for your completed pointings.</li>
							<li>
								Cancel any planned pointings you won't complete so others know they're available.
							</li>
						</ol>
					</div>
				</div>
			</div>

			<!-- Use Case 2 -->
			<div>
				<h3 class="text-xl font-semibold text-blue-600 mb-3">
					2. I would like to see what others are observing to plan my observations accordingly
				</h3>
				<div class="pl-4 border-l-4 border-blue-200">
					<p>
						You are required to register. Use your API token along with the pointings GET method to
						retrieve reported planned or completed pointings for a specific GW alert, time window,
						instrument, and/or band.
					</p>
				</div>
			</div>
		</div>
	</Card>

	<!-- Getting Started -->
	<Card>
		<h2 class="text-2xl font-semibold mb-6">Getting Started</h2>

		<div class="grid md:grid-cols-3 gap-6">
			<div class="text-center">
				<div
					class="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3"
				>
					<span class="text-blue-600 font-bold text-lg">1</span>
				</div>
				<h3 class="font-semibold mb-2">Register</h3>
				<p class="text-sm text-gray-600">Create an account to get your API token</p>
				<a href="/register" class="text-blue-600 hover:text-blue-800 text-sm underline"
					>Register now →</a
				>
			</div>

			<div class="text-center">
				<div
					class="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3"
				>
					<span class="text-blue-600 font-bold text-lg">2</span>
				</div>
				<h3 class="font-semibold mb-2">Submit Instrument</h3>
				<p class="text-sm text-gray-600">Add your telescope to the database</p>
				<a href="/submit/instrument" class="text-blue-600 hover:text-blue-800 text-sm underline"
					>Submit instrument →</a
				>
			</div>

			<div class="text-center">
				<div
					class="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3"
				>
					<span class="text-blue-600 font-bold text-lg">3</span>
				</div>
				<h3 class="font-semibold mb-2">Start Observing</h3>
				<p class="text-sm text-gray-600">Report your planned and completed pointings</p>
				<a
					href="/docs"
					target="_blank"
					class="text-blue-600 hover:text-blue-800 text-sm underline">View API docs →</a
				>
			</div>
		</div>
	</Card>
</PageContainer>
