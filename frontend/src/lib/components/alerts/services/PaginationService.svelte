<script lang="ts">
	/**
	 * @component PaginationService
	 * @description Service component for managing pagination state and navigation
	 * Handles pagination controls, page navigation, and per-page settings
	 */
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Pagination state
	export let currentPage = 1;
	export let perPage = 25;
	export let totalItems = 0;
	export let totalPages = 0;
	export let hasNext = false;
	export let hasPrev = false;

	/**
	 * Update pagination state from API response
	 */
	export function updatePaginationState(paginationData: any) {
		currentPage = paginationData.currentPage || 1;
		totalItems = paginationData.total || 0;
		totalPages = paginationData.totalPages || 0;
		hasNext = paginationData.hasNext || false;
		hasPrev = paginationData.hasPrev || false;

		dispatch('pagination-updated', {
			currentPage,
			perPage,
			totalItems,
			totalPages,
			hasNext,
			hasPrev
		});
	}

	/**
	 * Navigate to a specific page
	 */
	export function goToPage(page: number) {
		if (page >= 1 && page <= totalPages && page !== currentPage) {
			currentPage = page;
			dispatch('page-changed', {
				page: currentPage,
				perPage,
				reset: false
			});
		}
	}

	/**
	 * Navigate to next page
	 */
	export function nextPage() {
		if (hasNext) {
			goToPage(currentPage + 1);
		}
	}

	/**
	 * Navigate to previous page
	 */
	export function prevPage() {
		if (hasPrev) {
			goToPage(currentPage - 1);
		}
	}

	/**
	 * Change items per page
	 */
	export function changePerPage(newPerPage: number) {
		if (newPerPage !== perPage) {
			perPage = newPerPage;
			currentPage = 1; // Reset to first page when changing per page
			dispatch('page-changed', {
				page: currentPage,
				perPage,
				reset: true
			});
		}
	}

	/**
	 * Reset pagination to first page
	 */
	export function resetToFirstPage() {
		if (currentPage !== 1) {
			currentPage = 1;
			dispatch('page-changed', {
				page: currentPage,
				perPage,
				reset: true
			});
		}
	}

	/**
	 * Get pagination info for display
	 */
	export function getPaginationInfo() {
		return {
			currentPage,
			perPage,
			totalItems,
			totalPages,
			hasNext,
			hasPrev,
			startItem: totalItems > 0 ? (currentPage - 1) * perPage + 1 : 0,
			endItem: Math.min(currentPage * perPage, totalItems)
		};
	}

	/**
	 * Generate page numbers for pagination display
	 */
	export function getDisplayPages() {
		const maxDisplayPages = 5;
		const startPage = Math.max(1, currentPage - Math.floor(maxDisplayPages / 2));
		const endPage = Math.min(totalPages, startPage + maxDisplayPages - 1);

		const pages = [];
		for (let i = startPage; i <= endPage; i++) {
			pages.push(i);
		}

		return {
			pages,
			showEllipsis: totalPages > maxDisplayPages && currentPage < totalPages - 2,
			startPage,
			endPage
		};
	}
</script>

<!-- This is a service component with no visual output -->
