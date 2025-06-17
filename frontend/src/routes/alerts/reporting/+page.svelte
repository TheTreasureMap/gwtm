<svelte:head>
  <title>Reporting Instruments - GWTM</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-4xl font-bold text-gray-900 mb-4">Reporting Instruments</h1>
    <p class="text-lg text-gray-600">
      View instruments that are actively reporting observations for gravitational wave follow-up.
    </p>
  </div>

  <!-- Coming Soon Notice -->
  <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
    <div class="flex items-center">
      <svg class="w-6 h-6 text-yellow-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
      </svg>
      <div>
        <h3 class="text-lg font-semibold text-yellow-800">Page Under Development</h3>
        <p class="text-yellow-700">
          The reporting instruments page is currently being implemented. 
          In the meantime, you can use the search pages to explore instrument data.
        </p>
      </div>
    </div>
  </div>

  <!-- Navigation Links -->
  <div class="grid md:grid-cols-2 gap-6">
    <div class="bg-white rounded-lg shadow-lg p-6">
      <h3 class="text-xl font-semibold mb-4 flex items-center">
        <svg class="w-6 h-6 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        Search Instruments
      </h3>
      <p class="text-gray-600 mb-4">
        Browse and search all registered instruments in the database.
      </p>
      <a 
        href="/search/instruments" 
        class="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
      >
        View Instruments →
      </a>
    </div>

    <div class="bg-white rounded-lg shadow-lg p-6">
      <h3 class="text-xl font-semibold mb-4 flex items-center">
        <svg class="w-6 h-6 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        Submit New Instrument
      </h3>
      <p class="text-gray-600 mb-4">
        Register your telescope or instrument for GW follow-up coordination.
      </p>
      <a 
        href="/submit/instrument" 
        class="inline-block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
      >
        Submit Instrument →
      </a>
    </div>
  </div>

  <!-- Back Navigation -->
  <div class="mt-8">
    <a 
      href="/alerts/select" 
      class="inline-flex items-center text-blue-600 hover:text-blue-800"
    >
      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
      Back to GW Events
    </a>
  </div>
</div>