<!--
@component TabNavigation
@description A reusable tab navigation component with consistent styling
@category UI Primitives
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<script>
  let activeTab = 'summary';
  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'details', label: 'Details' },
    { id: 'settings', label: 'Settings' }
  ];
</script>

<TabNavigation {tabs} bind:activeTab titleText="Event Explorer:" />
```

@prop {Array} tabs - Array of tab objects with id and label
@prop {string} activeTab - Currently active tab id
@prop {string} titleText - Optional title text to display before tabs
@prop {string} class - Additional CSS classes

@event tab-change - Fired when tab is changed
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{
		'tab-change': { tabId: string };
	}>();

	/**
	 * Array of tab objects with id and label
	 * @type {Array<{id: string, label: string, disabled?: boolean}>}
	 * @default []
	 */
	export let tabs: Array<{
		id: string;
		label: string;
		disabled?: boolean;
	}> = [];

	/**
	 * Currently active tab id
	 * @type {string}
	 * @default ''
	 */
	export let activeTab: string = '';

	/**
	 * Optional title text to display before tabs
	 * @type {string}
	 * @default ''
	 */
	export let titleText: string = '';

	/**
	 * Additional CSS classes
	 * @type {string}
	 * @default ''
	 */
	let className: string = '';
	export { className as class };

	function handleTabClick(tabId: string) {
		if (tabs.find((tab) => tab.id === tabId)?.disabled) return;

		activeTab = tabId;
		dispatch('tab-change', { tabId });
	}

	$: containerClass = ['bg-white border rounded-lg overflow-hidden', className]
		.filter(Boolean)
		.join(' ');
</script>

<div class={containerClass}>
	<ul class="nav nav-tabs flex border-b border-gray-200 bg-gray-50" role="tablist">
		{#if titleText}
			<li class="nav-item px-4 py-3">
				<span class="nav-link disabled text-sm font-medium text-gray-500 font-bold">
					{titleText}
				</span>
			</li>
		{/if}

		{#each tabs as tab}
			<li class="nav-item cursor-pointer" role="presentation">
				<button
					class="nav-link px-4 py-3 text-sm font-medium border-b-2 transition-colors
						{activeTab === tab.id
						? 'text-blue-600 border-blue-600 bg-white'
						: 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'}
						{tab.disabled ? 'opacity-50 cursor-not-allowed' : ''}"
					on:click={() => handleTabClick(tab.id)}
					disabled={tab.disabled}
					role="tab"
					aria-selected={activeTab === tab.id}
					aria-controls="tabpanel-{tab.id}"
					id="tab-{tab.id}"
				>
					{tab.label}
				</button>
			</li>
		{/each}
	</ul>

	<!-- Tab Content Slot -->
	<div class="tab-content">
		<slot {activeTab} />
	</div>
</div>

<style>
	/* Ensure tab buttons are styled consistently */
	.nav-link {
		background: none;
		border: none;
		outline: none;
		font-family: inherit;
	}

	.nav-link:focus {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
	}

	/* Remove default button spacing */
	.nav-tabs {
		gap: 0;
	}

	.nav-item:not(:last-child) .nav-link {
		border-right: 1px solid #e5e7eb;
	}
</style>
