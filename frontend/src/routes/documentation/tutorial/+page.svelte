<svelte:head>
	<title>API Tutorial - GWTM</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
	<div class="mb-8">
		<h1 class="text-4xl font-bold text-gray-900 mb-4">API Jupyter Tutorial</h1>
		<p class="text-lg text-gray-600">
			Learn how to use the Treasure Map API with practical examples and code samples.
		</p>
	</div>

	<!-- Coming Soon Notice -->
	<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
		<div class="flex items-center">
			<svg
				class="w-6 h-6 text-yellow-600 mr-3"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
				/>
			</svg>
			<div>
				<h3 class="text-lg font-semibold text-yellow-800">Tutorial Under Development</h3>
				<p class="text-yellow-700">
					The interactive Jupyter tutorial is currently being updated for the new API. In the
					meantime, please use the resources below.
				</p>
			</div>
		</div>
	</div>

	<!-- Alternative Resources -->
	<div class="grid md:grid-cols-2 gap-6 mb-8">
		<div class="bg-white rounded-lg shadow-lg p-6">
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
				The easiest way to get started is with our official Python library that provides high-level
				functions and examples.
			</p>
			<a
				href="https://github.com/TheTreasureMap/gwtm_api"
				target="_blank"
				class="inline-block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
			>
				View on GitHub →
			</a>
		</div>

		<div class="bg-white rounded-lg shadow-lg p-6">
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
				Interactive API Docs
			</h3>
			<p class="text-gray-600 mb-4">
				Explore all available endpoints with live examples and the ability to test API calls
				directly from your browser.
			</p>
			<a
				href="/docs"
				target="_blank"
				class="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
			>
				Open API Docs →
			</a>
		</div>
	</div>

	<!-- Quick Examples -->
	<div class="bg-white rounded-lg shadow-lg p-6">
		<h2 class="text-2xl font-semibold mb-6">Quick Examples</h2>

		<div class="space-y-6">
			<!-- Example 1 -->
			<div>
				<h3 class="text-lg font-semibold mb-3">1. Getting Started with Authentication</h3>
				<div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
					<pre class="text-green-400 text-sm"><code
							># First, register for an account and get your API token
import requests

# Set your API token (get this from your profile page)
API_TOKEN = "your_api_token_here"
BASE_URL = "https://treasuremap.space/api/v1"

headers = {'{'}"Authorization": f"Bearer {'{'}{API_TOKEN}}",
    "Content-Type": "application/json"
}</code
						></pre>
				</div>
			</div>

			<!-- Example 2 -->
			<div>
				<h3 class="text-lg font-semibold mb-3">2. Querying Pointings</h3>
				<div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
					<pre class="text-green-400 text-sm"><code
							># Get pointings for a specific GW event
response = requests.get(
    f"{'{'}{BASE_URL}}/pointings",
    params={'{'}"graceid": "S190425z"},
    headers=headers
)

pointings = response.json()
print(f"Found {'{'}{len(pointings)}} pointings for S190425z")</code
						></pre>
				</div>
			</div>

			<!-- Example 3 -->
			<div>
				<h3 class="text-lg font-semibold mb-3">3. Submitting Planned Pointings</h3>
				<div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
					<pre class="text-green-400 text-sm"><code
							># Submit a planned pointing
pointing_data = {'{'}"graceid": "S190425z",
    "instrumentid": 1,  # Your instrument ID
    "ra": 123.456,
    "dec": -12.345,
    "pos_angle": 0.0,
    "status": "planned",
    "depth": 20.5,
    "depth_unit": "ab_mag",
    "band": "r"
}

response = requests.post(
    f"{'{'}{BASE_URL}}/pointings",
    json=pointing_data,
    headers=headers
)

print(response.json())</code
						></pre>
				</div>
			</div>
		</div>
	</div>

	<!-- Navigation -->
	<div class="mt-8 flex justify-between">
		<a href="/documentation" class="inline-flex items-center text-blue-600 hover:text-blue-800">
			<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
			</svg>
			Back to Documentation
		</a>

		<a
			href="/documentation/blog"
			class="inline-flex items-center text-blue-600 hover:text-blue-800"
		>
			What's New
			<svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
			</svg>
		</a>
	</div>
</div>
