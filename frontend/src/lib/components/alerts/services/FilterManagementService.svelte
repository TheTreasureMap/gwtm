<script lang="ts">
	/**
	 * @component FilterManagementService
	 * @description Service component for managing alert filters, URL parameters, and filter options
	 * Handles filter state management, URL synchronization, and filter options loading
	 */
	import { createEventDispatcher } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';

	const dispatch = createEventDispatcher();

	// Filter state
	export let filters = {
		graceid: '',
		alert_type: '',
		role: 'observation',
		observing_run: 'O4',
		far: 'significant',
		has_pointings: false
	};

	// Filter options loaded from API
	export let filterOptions = {
		observing_runs: [],
		roles: [],
		alert_types: []
	};

	export let filterOptionsLoading = true;

	/**
	 * Apply URL parameters to filters
	 */
	export function applyUrlParams() {
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

		dispatch('filters-updated', { filters });
	}

	/**
	 * Load filter options from API
	 */
	export async function loadFilterOptions() {
		try {
			filterOptionsLoading = true;
			const fetchedOptions = await api.alerts.getAlertFilterOptions();
			filterOptions = fetchedOptions;

			// Set default values based on available options
			if (
				fetchedOptions.observing_runs.length > 0 &&
				!fetchedOptions.observing_runs.includes(filters.observing_run)
			) {
				filters.observing_run =
					fetchedOptions.observing_runs[fetchedOptions.observing_runs.length - 1]; // Latest observing run
			}
			if (fetchedOptions.roles.length > 0 && !fetchedOptions.roles.includes(filters.role)) {
				filters.role = fetchedOptions.roles.includes('observation')
					? 'observation'
					: fetchedOptions.roles[0];
			}

			dispatch('filter-options-loaded', { filterOptions });
			dispatch('filters-updated', { filters });
		} catch (err) {
			console.error('Error loading filter options:', err);
			dispatch('filter-options-error', { error: err });
		} finally {
			filterOptionsLoading = false;
		}
	}

	/**
	 * Clear all filters to defaults
	 */
	export function clearFilters() {
		filters = {
			graceid: '',
			alert_type: '',
			role: filterOptions.roles.includes('observation') ? 'observation' : 'all',
			observing_run:
				filterOptions.observing_runs.length > 0
					? filterOptions.observing_runs[filterOptions.observing_runs.length - 1]
					: 'all',
			far: 'significant',
			has_pointings: false
		};

		dispatch('filters-cleared', { filters });
	}

	/**
	 * Update a specific filter
	 */
	export function updateFilter(key: string, value: unknown) {
		filters = { ...filters, [key]: value };
		dispatch('filter-changed', { key, value, filters });
	}

	/**
	 * Build query parameters from current filters
	 */
	export function buildQueryParams(additionalParams = {}) {
		const params = { ...additionalParams };

		if (filters.graceid.trim()) params.graceid = filters.graceid.trim();
		if (filters.alert_type) params.alert_type = filters.alert_type;
		if (filters.role && filters.role !== 'all') params.role = filters.role;
		if (filters.observing_run && filters.observing_run !== 'all')
			params.observing_run = filters.observing_run;
		if (filters.far && filters.far !== 'all') params.far = filters.far;
		if (filters.has_pointings) params.has_pointings = filters.has_pointings;

		return params;
	}
</script>

<!-- This is a service component with no visual output -->
