<script lang="ts">
	/**
	 * @component AlertSearchService
	 * @description Service component for managing alert search functionality and autocomplete
	 * Handles search queries, suggestions, and search result processing
	 */
	import { createEventDispatcher } from 'svelte';
	import { api } from '$lib/api';

	const dispatch = createEventDispatcher();

	// Search state
	export let searchSuggestions = [];
	export let showSuggestions = false;
	export let searchTimeout: ReturnType<typeof setTimeout> | null = null;

	// Current filters (passed from FilterManagementService)
	export let filters = {};

	/**
	 * Search for graceids with autocomplete suggestions
	 */
	export async function searchGraceids(query: string) {
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
				per_page: 20 // Get more results to extract suggestions from
			};

			// Apply current filter selections to the search
			if (filters.alert_type) searchParams.alert_type = filters.alert_type;
			if (filters.role && filters.role !== 'all') searchParams.role = filters.role;
			if (filters.observing_run && filters.observing_run !== 'all')
				searchParams.observing_run = filters.observing_run;
			if (filters.far && filters.far !== 'all') searchParams.far = filters.far;
			if (filters.has_pointings) searchParams.has_pointings = filters.has_pointings;

			const response = await api.alerts.queryAlerts(currentParams);

			if (response && response.alerts) {
				// Extract unique graceids/alertnames from the results
				const suggestions = new Set();
				response.alerts.forEach((alert) => {
					if (alert.graceid) suggestions.add(alert.graceid);
					if (alert.alternateid) suggestions.add(alert.alternateid);
				});

				searchSuggestions = Array.from(suggestions)
					.filter((id) => id.toLowerCase().includes(query.toLowerCase()))
					.slice(0, 8); // Show max 8 suggestions

				showSuggestions = searchSuggestions.length > 0;
				dispatch('suggestions-updated', { suggestions: searchSuggestions, show: showSuggestions });
			}
		} catch (err) {
			console.warn('Error searching graceids:', err);
			searchSuggestions = [];
			showSuggestions = false;
			dispatch('search-error', { error: err });
		}
	}

	/**
	 * Handle search input with debouncing
	 */
	export function handleSearchInput(value: string) {
		// Clear existing timeout
		if (searchTimeout) {
			clearTimeout(searchTimeout);
		}

		// Set new timeout for search
		searchTimeout = setTimeout(() => {
			searchGraceids(value);
		}, 300); // Wait 300ms after user stops typing

		dispatch('search-input-changed', { value });
	}

	/**
	 * Select a suggestion from the autocomplete
	 */
	export function selectSuggestion(suggestion: string) {
		showSuggestions = false;
		searchSuggestions = [];
		dispatch('suggestion-selected', { suggestion });
	}

	/**
	 * Hide suggestions (with delay for click handling)
	 */
	export function hideSuggestions() {
		// Delay hiding to allow clicking on suggestions
		setTimeout(() => {
			showSuggestions = false;
		}, 200);
	}

	/**
	 * Show suggestions if search criteria met
	 */
	export function showSuggestionsIfReady(value: string) {
		if (value.length >= 3) {
			searchGraceids(value);
		}
	}
</script>

<!-- This is a service component with no visual output -->
