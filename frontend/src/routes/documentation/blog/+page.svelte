<svelte:head>
  <title>What's New - GWTM</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 py-8">
  <div class="mb-8">
    <h1 class="text-4xl font-bold text-gray-900 mb-4">What's New</h1>
    <p class="text-lg text-gray-600">
      Latest updates, improvements, and announcements for the Treasure Map.
    </p>
  </div>

  <!-- Blog Posts -->
  <div class="space-y-8">
    
    <!-- Latest Post -->
    <article class="bg-white rounded-lg shadow-lg p-6">
      <div class="flex items-center text-sm text-gray-500 mb-3">
        <time datetime="2025-06-13">June 13, 2025</time>
        <span class="mx-2">•</span>
        <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">New Feature</span>
      </div>
      <h2 class="text-2xl font-semibold text-gray-900 mb-3">
        Modern Frontend with Svelte
      </h2>
      <p class="text-gray-600 mb-4">
        We're excited to announce the launch of our new modern frontend built with SvelteKit! 
        This update brings improved performance, better user experience, and a responsive design 
        that works seamlessly across all devices.
      </p>
      <div class="flex flex-wrap gap-2">
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">Frontend</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">SvelteKit</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">UI/UX</span>
      </div>
    </article>

    <!-- Previous Posts -->
    <article class="bg-white rounded-lg shadow-lg p-6">
      <div class="flex items-center text-sm text-gray-500 mb-3">
        <time datetime="2025-05-15">May 15, 2025</time>
        <span class="mx-2">•</span>
        <span class="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">API</span>
      </div>
      <h2 class="text-2xl font-semibold text-gray-900 mb-3">
        FastAPI Backend Launch
      </h2>
      <p class="text-gray-600 mb-4">
        Our new FastAPI backend is now live, providing faster response times, automatic API documentation, 
        and improved error handling. The new backend maintains full compatibility with existing API endpoints 
        while adding new features for better developer experience.
      </p>
      <div class="flex flex-wrap gap-2">
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">FastAPI</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">Performance</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">Documentation</span>
      </div>
    </article>

    <article class="bg-white rounded-lg shadow-lg p-6">
      <div class="flex items-center text-sm text-gray-500 mb-3">
        <time datetime="2025-04-20">April 20, 2025</time>
        <span class="mx-2">•</span>
        <span class="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs">Tool Release</span>
      </div>
      <h2 class="text-2xl font-semibold text-gray-900 mb-3">
        Python API Wrapper Available
      </h2>
      <p class="text-gray-600 mb-4">
        We've released the official Python API wrapper: 
        <a href="https://github.com/TheTreasureMap/gwtm_api" class="text-blue-600 hover:text-blue-800 underline">gwtm_api</a>. 
        This library provides a convenient Python interface to all Treasure Map endpoints, 
        along with helpful utilities for GW follow-up planning and coordination.
      </p>
      <div class="flex flex-wrap gap-2">
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">Python</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">API Wrapper</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">Tools</span>
      </div>
    </article>

    <article class="bg-white rounded-lg shadow-lg p-6">
      <div class="flex items-center text-sm text-gray-500 mb-3">
        <time datetime="2025-03-10">March 10, 2025</time>
        <span class="mx-2">•</span>
        <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs">Enhancement</span>
      </div>
      <h2 class="text-2xl font-semibold text-gray-900 mb-3">
        Enhanced DOI Request System
      </h2>
      <p class="text-gray-600 mb-4">
        We've improved the DOI request system to make it easier for observers to get credit for their contributions. 
        The new system supports bulk DOI requests and better integration with author group management.
      </p>
      <div class="flex flex-wrap gap-2">
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">DOI</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">Citations</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">Collaboration</span>
      </div>
    </article>

    <article class="bg-white rounded-lg shadow-lg p-6">
      <div class="flex items-center text-sm text-gray-500 mb-3">
        <time datetime="2025-02-01">February 1, 2025</time>
        <span class="mx-2">•</span>
        <span class="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs">Important</span>
      </div>
      <h2 class="text-2xl font-semibold text-gray-900 mb-3">
        LIGO-Virgo-KAGRA O4 Observing Run
      </h2>
      <p class="text-gray-600 mb-4">
        The fourth observing run (O4) of the LIGO-Virgo-KAGRA gravitational wave detector network is now active. 
        We expect increased GW alert frequency and encourage all observers to register their instruments 
        and participate in follow-up coordination.
      </p>
      <div class="flex flex-wrap gap-2">
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">O4</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">LIGO</span>
        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">Observing Run</span>
      </div>
    </article>

  </div>

  <!-- Archive Notice -->
  <div class="mt-12 text-center">
    <div class="bg-gray-50 rounded-lg p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">Looking for older updates?</h3>
      <p class="text-gray-600 mb-4">
        Previous announcements and development history can be found in our GitHub repository.
      </p>
      <a 
        href="https://github.com/TheTreasureMap" 
        target="_blank"
        class="inline-flex items-center text-blue-600 hover:text-blue-800"
      >
        View on GitHub
        <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
        </svg>
      </a>
    </div>
  </div>

  <!-- Navigation -->
  <div class="mt-8">
    <a 
      href="/documentation" 
      class="inline-flex items-center text-blue-600 hover:text-blue-800"
    >
      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
      Back to Documentation
    </a>
  </div>
</div>