<svelte:head>
  <title>GW Events - GWTM</title>
</svelte:head>

<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { gwtmApi } from '$lib/api';

  let alerts = [];
  let groupedAlerts = [];
  let loading = true;
  let error = null;
  let filters = {
    graceid: '',
    alert_type: '',
    role: 'observation',
    observing_run: 'O4',
    far: 'significant',
    has_pointings: false
  };
  
  // Dynamic search state
  let searchSuggestions = [];
  let showSuggestions = false;
  let searchTimeout;
  let searchInput;
  
  // Filter options loaded from API
  let filterOptions = {
    observing_runs: [],
    roles: [],
    alert_types: []
  };
  let filterOptionsLoading = true;
  
  // Function to apply URL parameters to filters
  function applyUrlParams() {
    const urlParams = $page.url.searchParams;
    
    if (urlParams.get('graceid')) {
      filters.graceid = urlParams.get('graceid');
    }
    if (urlParams.get('alert_type')) {
      filters.alert_type = urlParams.get('alert_type');
    }
    if (urlParams.get('role')) {
      filters.role = urlParams.get('role');
    }
    if (urlParams.get('observing_run')) {
      filters.observing_run = urlParams.get('observing_run');
    }
    if (urlParams.get('far')) {
      filters.far = urlParams.get('far');
    }
    if (urlParams.get('has_pointings')) {
      filters.has_pointings = urlParams.get('has_pointings') === 'true';
    }
  }
  
  // Pagination state
  let currentPage = 1;
  let perPage = 25;
  let totalItems = 0;
  let totalPages = 0;
  let hasNext = false;
  let hasPrev = false;

  async function loadAlerts() {
    try {
      loading = true;
      error = null;
      
      // Build query parameters
      const params = {
        page: currentPage,
        per_page: perPage
      };
      if (filters.graceid.trim()) params.graceid = filters.graceid.trim();
      if (filters.alert_type) params.alert_type = filters.alert_type;
      if (filters.role && filters.role !== 'all') params.role = filters.role;
      if (filters.observing_run && filters.observing_run !== 'all') params.observing_run = filters.observing_run;
      if (filters.far && filters.far !== 'all') params.far = filters.far;
      if (filters.has_pointings) params.has_pointings = filters.has_pointings;

      // Call FastAPI to fetch alerts
      const response = await gwtmApi.queryAlerts(params);
      if (response) {
        alerts = response.alerts || [];
        // Group alerts by graceid for display
        groupedAlerts = groupAlertsByGraceid(alerts);
        
        // Get pointing counts for the grouped alerts
        if (groupedAlerts.length > 0) {
          const graceids = groupedAlerts.map(g => g.alertname);
          await loadPointingCounts(graceids);
        }
        
        totalItems = response.total;
        totalPages = response.total_pages;
        hasNext = response.has_next;
        hasPrev = response.has_prev;
        currentPage = response.page;
      } else {
        alerts = [];
        groupedAlerts = [];
        totalItems = 0;
        totalPages = 0;
        hasNext = false;
        hasPrev = false;
      }
    } catch (err) {
      error = err.message || 'Failed to load alerts';
      console.error('Error loading alerts:', err);
    } finally {
      loading = false;
    }
  }

  function handleSearch() {
    currentPage = 1; // Reset to first page when searching
    loadAlerts();
  }

  function clearFilters() {
    filters = { 
      graceid: '', 
      alert_type: '', 
      role: filterOptions.roles.includes('observation') ? 'observation' : 'all',
      observing_run: filterOptions.observing_runs.length > 0 ? filterOptions.observing_runs[filterOptions.observing_runs.length - 1] : 'all',
      far: 'significant',
      has_pointings: false
    };
    currentPage = 1; // Reset to first page when clearing
    loadAlerts();
  }

  function goToPage(page) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
      loadAlerts();
    }
  }

  function nextPage() {
    if (hasNext) {
      goToPage(currentPage + 1);
    }
  }

  function prevPage() {
    if (hasPrev) {
      goToPage(currentPage - 1);
    }
  }

  function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  }

  function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    if (typeof num === 'number') {
      return num.toFixed(3);
    }
    return num;
  }

  function groupAlertsByGraceid(alertsList) {
    const grouped = {};
    
    // Group alerts by graceid (or alternateid if available)
    alertsList.forEach(alert => {
      const key = alert.alternateid || alert.graceid;
      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key].push(alert);
    });

    // Process each group to create the grouped alert format
    const result = [];
    for (const [graceid, alerts] of Object.entries(grouped)) {
      // Sort alerts by date created, most recent first
      alerts.sort((a, b) => new Date(b.datecreated) - new Date(a.datecreated));
      
      const mostRecentAlert = alerts[0];
      const alertTypes = alerts.map(a => a.alert_type).filter(Boolean);
      const hasRetraction = alertTypes.includes('Retraction');
      
      // Calculate classification (like Flask version)
      let classification = 'Unknown';
      if (hasRetraction) {
        classification = 'Retracted';
      } else {
        // Use most recent alert's classification logic
        classification = getAlertClassification(mostRecentAlert);
      }
      
      // Format distance
      let distanceStr = 'N/A';
      if (mostRecentAlert.distance && mostRecentAlert.distance > 0) {
        const dist = Math.round(mostRecentAlert.distance * 100) / 100;
        const distErr = mostRecentAlert.distance_error ? Math.round(mostRecentAlert.distance_error * 100) / 100 : null;
        distanceStr = distErr ? `${dist} +/- ${distErr}` : `${dist}`;
      }
      
      result.push({
        alertname: graceid,
        classification: classification,
        distance: distanceStr,
        pcounts: 0, // TODO: Get pointing counts from API
        alert_types: alertTypes,
        has_icecube: false, // TODO: Get icecube data
        mostRecentAlert: mostRecentAlert
      });
    }
    
    return result.sort((a, b) => a.alertname.localeCompare(b.alertname));
  }

  function getAlertClassification(alert) {
    // Classification logic matching Flask version
    if (!alert) return 'Unknown';
    
    // Handle Burst events
    if (alert.group === 'Burst') {
      return 'None (detected as burst)';
    }
    
    // Build probability list with classifications
    const probabilities = [];
    
    if (alert.prob_bns && alert.prob_bns > 0.01) {
      probabilities.push({ prob: alert.prob_bns, name: 'BNS' });
    }
    if (alert.prob_nsbh && alert.prob_nsbh > 0.01) {
      probabilities.push({ prob: alert.prob_nsbh, name: 'NSBH' });
    }
    if (alert.prob_bbh && alert.prob_bbh > 0.01) {
      probabilities.push({ prob: alert.prob_bbh, name: 'BBH' });
    }
    if (alert.prob_terrestrial && alert.prob_terrestrial > 0.01) {
      probabilities.push({ prob: alert.prob_terrestrial, name: 'Terrestrial' });
    }
    if (alert.prob_gap && alert.prob_gap > 0.01) {
      probabilities.push({ prob: alert.prob_gap, name: 'Mass Gap' });
    }
    
    // Sort by probability descending
    probabilities.sort((a, b) => b.prob - a.prob);
    
    // Format as "BBH: (85.2%) BNS: (12.3%) "
    if (probabilities.length === 0) {
      return 'Unknown';
    }
    
    return probabilities
      .map(p => `${p.name}: (${(p.prob * 100).toFixed(1)}%)`)
      .join(' ') + ' ';
  }

  function getAlertTypeBadges(alertTypes) {
    const badgeConfig = {
      'Preliminary': { color: 'bg-yellow-100 text-yellow-800', icon: 'P' },
      'Initial': { color: 'bg-blue-100 text-blue-800', icon: 'I' },
      'Update': { color: 'bg-green-100 text-green-800', icon: 'U' },
      'Retraction': { color: 'bg-red-100 text-red-800', icon: 'R' },
      'EarlyWarning': { color: 'bg-purple-100 text-purple-800', icon: 'EW' },
      'Early_Warning': { color: 'bg-purple-100 text-purple-800', icon: 'EW' },
      'Publication': { color: 'bg-gray-100 text-gray-800', icon: 'PU' }
    };
    
    return alertTypes.map(type => {
      const config = badgeConfig[type] || { color: 'bg-gray-100 text-gray-800', icon: type?.substring(0, 2) || '?' };
      return { type, ...config };
    });
  }

  async function loadPointingCounts(graceids) {
    try {
      // Get pointing counts for each graceid using the existing pointings API
      const pointingPromises = graceids.map(async (graceid) => {
        try {
          const pointings = await gwtmApi.getPointings({ graceid, status: 'completed' });
          return { graceid, count: pointings?.length || 0 };
        } catch (err) {
          console.warn(`Failed to get pointings for ${graceid}:`, err);
          return { graceid, count: 0 };
        }
      });
      
      const pointingCounts = await Promise.all(pointingPromises);
      
      // Update the grouped alerts with pointing counts
      groupedAlerts = groupedAlerts.map(alert => {
        const countData = pointingCounts.find(pc => pc.graceid === alert.alertname);
        return {
          ...alert,
          pcounts: countData ? countData.count : 0
        };
      });
    } catch (err) {
      console.error('Error loading pointing counts:', err);
      // Set all counts to 0 on error
      groupedAlerts = groupedAlerts.map(alert => ({
        ...alert,
        pcounts: 0
      }));
    }
  }

  async function loadFilterOptions() {
    try {
      filterOptionsLoading = true;
      const options = await gwtmApi.getAlertFilterOptions();
      filterOptions = options;
      
      // Set default values based on available options
      if (options.observing_runs.length > 0 && !options.observing_runs.includes(filters.observing_run)) {
        filters.observing_run = options.observing_runs[options.observing_runs.length - 1]; // Latest observing run
      }
      if (options.roles.length > 0 && !options.roles.includes(filters.role)) {
        filters.role = options.roles.includes('observation') ? 'observation' : options.roles[0];
      }
    } catch (err) {
      console.error('Error loading filter options:', err);
    } finally {
      filterOptionsLoading = false;
    }
  }

  async function searchGraceids(query) {
    if (!query || query.length < 3) {
      searchSuggestions = [];
      showSuggestions = false;
      return;
    }

    try {
      // Build search parameters using current filters
      const searchParams = {
        graceid: query,
        page: 1,
        per_page: 20, // Get more results to extract suggestions from
      };
      
      // Apply current filter selections to the search
      if (filters.alert_type) searchParams.alert_type = filters.alert_type;
      if (filters.role && filters.role !== 'all') searchParams.role = filters.role;
      if (filters.observing_run && filters.observing_run !== 'all') searchParams.observing_run = filters.observing_run;
      if (filters.far && filters.far !== 'all') searchParams.far = filters.far;
      if (filters.has_pointings) searchParams.has_pointings = filters.has_pointings;

      const response = await gwtmApi.queryAlerts(searchParams);

      if (response && response.alerts) {
        // Extract unique graceids/alertnames from the results
        const suggestions = new Set();
        response.alerts.forEach(alert => {
          if (alert.graceid) suggestions.add(alert.graceid);
          if (alert.alternateid) suggestions.add(alert.alternateid);
        });
        
        searchSuggestions = Array.from(suggestions)
          .filter(id => id.toLowerCase().includes(query.toLowerCase()))
          .slice(0, 8); // Show max 8 suggestions
        
        showSuggestions = searchSuggestions.length > 0;
      }
    } catch (err) {
      console.warn('Error searching graceids:', err);
      searchSuggestions = [];
      showSuggestions = false;
    }
  }

  function handleSearchInput(event) {
    const value = event.target.value;
    filters.graceid = value;
    
    // Clear existing timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    // Set new timeout for search
    searchTimeout = setTimeout(() => {
      searchGraceids(value);
    }, 300); // Wait 300ms after user stops typing
  }

  function selectSuggestion(suggestion) {
    filters.graceid = suggestion;
    showSuggestions = false;
    searchSuggestions = [];
    handleSearch();
  }

  function hideSuggestions() {
    // Delay hiding to allow clicking on suggestions
    setTimeout(() => {
      showSuggestions = false;
    }, 200);
  }

  onMount(async () => {
    // Apply URL parameters first
    applyUrlParams();
    
    // Load filter options
    await loadFilterOptions();
    
    // Load alerts with applied filters
    loadAlerts();
  });
</script>

<div class="max-w-7xl mx-auto px-4 py-8">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-4xl font-bold text-gray-900 mb-4">Gravitational Wave Events</h1>
  </div>

  <!-- Search Filters -->
  <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
    <h2 class="text-xl font-semibold mb-4">Search Filters</h2>
    
    <!-- First row of filters -->
    <div class="grid md:grid-cols-5 gap-4 mb-4">
      <div>
        <label for="observing_run" class="block text-sm font-medium text-gray-700 mb-2">
          <strong>Observing Run</strong>
        </label>
        <select
          id="observing_run"
          bind:value={filters.observing_run}
          disabled={filterOptionsLoading}
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <option value="all">All</option>
          {#each filterOptions.observing_runs as run}
            <option value={run}>{run}</option>
          {/each}
        </select>
      </div>
      
      <div>
        <label for="role" class="block text-sm font-medium text-gray-700 mb-2">
          <strong>Role</strong>
        </label>
        <select
          id="role"
          bind:value={filters.role}
          disabled={filterOptionsLoading}
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <option value="all">All</option>
          {#each filterOptions.roles as role}
            <option value={role}>{role.charAt(0).toUpperCase() + role.slice(1)}</option>
          {/each}
        </select>
      </div>
      
      <div>
        <label for="far" class="block text-sm font-medium text-gray-700 mb-2">
          <strong>FAR</strong>
        </label>
        <select
          id="far"
          bind:value={filters.far}
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All</option>
          <option value="significant">Significant</option>
          <option value="subthreshold">Subthreshold</option>
        </select>
      </div>
      
      <div>
        <label class="flex items-center mt-7">
          <input
            type="checkbox"
            bind:checked={filters.has_pointings}
            class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <span class="text-sm font-medium text-gray-700"><strong>Has Pointings</strong></span>
        </label>
      </div>
      
      <div class="flex items-end space-x-2">
        <button
          on:click={handleSearch}
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Search
        </button>
        <button
          on:click={clearFilters}
          class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          Clear
        </button>
      </div>
    </div>
    
    <!-- Test alert warning -->
    {#if filters.role === 'test' || filters.role === 'all'}
      <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-center text-red-700 font-medium">
          All ingested test alerts (MS...) are deleted within 48 hours
        </p>
      </div>
    {/if}
    
    <!-- Second row: Search box with autocomplete -->
    <div class="mb-4 relative">
      <p class="text-sm text-gray-600 mb-2">Type something in the input field to search for GW Event Names (autocomplete suggestions appear after 3+ characters):</p>
      <div class="relative">
        <input
          bind:this={searchInput}
          id="search"
          type="text"
          bind:value={filters.graceid}
          on:input={handleSearchInput}
          on:blur={hideSuggestions}
          on:focus={() => filters.graceid.length >= 3 && searchGraceids(filters.graceid)}
          placeholder="Search for graceid (e.g., S190425z, GW190521)..."
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          autocomplete="off"
        />
        
        <!-- Autocomplete suggestions dropdown -->
        {#if showSuggestions && searchSuggestions.length > 0}
          <div class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
            {#each searchSuggestions as suggestion}
              <button
                class="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                on:click={() => selectSuggestion(suggestion)}
              >
                <span class="text-sm text-gray-900">{suggestion}</span>
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <br><br>
      <p class="text-sm text-gray-600">Click on an alert name to see its visualization</p>
    </div>
  </div>

  <!-- Loading State -->
  {#if loading}
    <div class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-gray-600">Loading alerts...</p>
    </div>
  {/if}

  <!-- Error State -->
  {#if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div class="flex">
        <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Error loading alerts</h3>
          <p class="mt-1 text-sm text-red-700">{error}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Results -->
  {#if !loading && !error}
    <div class="bg-white rounded-lg shadow-lg overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 class="text-xl font-semibold">
          {totalItems} Alert{totalItems !== 1 ? 's' : ''} Found
          {#if totalItems > 0}
            <span class="text-sm font-normal text-gray-600">
              (showing {((currentPage - 1) * perPage) + 1}-{Math.min(currentPage * perPage, totalItems)} of {totalItems})
            </span>
          {/if}
        </h2>
        
        <!-- Per page selector -->
        <div class="flex items-center space-x-2">
          <label for="perPage" class="text-sm text-gray-600">Show:</label>
          <select
            id="perPage"
            bind:value={perPage}
            on:change={() => { currentPage = 1; loadAlerts(); }}
            class="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span class="text-sm text-gray-600">per page</span>
        </div>
      </div>

      {#if groupedAlerts.length === 0}
        <div class="text-center py-8">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">No alerts found</h3>
          <p class="mt-1 text-sm text-gray-500">Try adjusting your search filters.</p>
        </div>
      {:else}
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Alert
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Classification
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Distance (Mpc)
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  # Pointings
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              {#each groupedAlerts as groupedAlert}
                <tr class="hover:bg-gray-50">
                  <!-- Alert column with name and type badges -->
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center space-x-2">
                      <div class="text-sm font-medium text-blue-600">
                        <a href="/alerts?graceids={groupedAlert.alertname}" class="hover:text-blue-800">
                          {groupedAlert.alertname}
                        </a>
                      </div>
                      <div class="flex space-x-1">
                        {#each getAlertTypeBadges(groupedAlert.alert_types) as badge}
                          <span class="inline-flex px-1 py-0.5 text-xs font-semibold rounded-full {badge.color}">
                            {badge.icon}
                          </span>
                        {/each}
                        {#if groupedAlert.has_icecube}
                          <span class="inline-flex items-center">
                            <svg class="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M10 2L3 7v6c0 5.55 3.84 9.74 9 11 5.16-1.26 9-5.45 9-11V7l-7-5z"/>
                            </svg>
                          </span>
                        {/if}
                      </div>
                    </div>
                  </td>
                  
                  <!-- Classification column -->
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-sm text-gray-900">{groupedAlert.classification}</span>
                  </td>
                  
                  <!-- Distance column -->
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-sm text-gray-900">{groupedAlert.distance}</span>
                  </td>
                  
                  <!-- Pointings count column -->
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-sm text-gray-900">{groupedAlert.pcounts}</span>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
      
      <!-- Pagination Controls -->
      {#if totalPages > 1}
        <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <button
              on:click={prevPage}
              disabled={!hasPrev}
              class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <div class="flex items-center space-x-1">
              {#each Array.from({length: Math.min(5, totalPages)}, (_, i) => {
                const startPage = Math.max(1, currentPage - 2);
                const endPage = Math.min(totalPages, startPage + 4);
                return startPage + i <= endPage ? startPage + i : null;
              }).filter(p => p !== null) as page}
                <button
                  on:click={() => goToPage(page)}
                  class="px-3 py-2 border rounded-md text-sm font-medium
                    {page === currentPage 
                      ? 'bg-blue-600 text-white border-blue-600' 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
                >
                  {page}
                </button>
              {/each}
              
              {#if totalPages > 5 && currentPage < totalPages - 2}
                <span class="px-2 text-gray-500">...</span>
                <button
                  on:click={() => goToPage(totalPages)}
                  class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  {totalPages}
                </button>
              {/if}
            </div>
            
            <button
              on:click={nextPage}
              disabled={!hasNext}
              class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          
          <div class="text-sm text-gray-600">
            Page {currentPage} of {totalPages}
          </div>
        </div>
      {/if}
    </div>
  {/if}

</div>