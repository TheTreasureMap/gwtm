<!--
@component ToggleGroup
@description A reusable toggle group component for show/hide functionality with consistent styling
@category UI Primitives
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<ToggleGroup label="Instrument Footprints" bind:expanded={showFootprints}>
  <InstrumentList />
</ToggleGroup>

<ToggleGroup label="Advanced Options" variant="outline" size="small">
  <div class="p-4">
    <p>Advanced configuration options...</p>
  </div>
</ToggleGroup>
```

@prop {string} label - Label text for the toggle button
@prop {boolean} expanded - Whether the content is expanded
@prop {'primary' | 'secondary' | 'outline'} variant - Button styling variant
@prop {'small' | 'medium' | 'large'} size - Button size
@prop {boolean} disabled - Whether the toggle is disabled
@prop {string} class - Additional CSS classes

@slot default - Content to show/hide
@slot label - Custom label content
@slot icon - Custom icon content

@event toggle - Fired when toggle state changes
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { slide } from 'svelte/transition';
	import Button from './Button.svelte';

	const dispatch = createEventDispatcher<{
		toggle: { expanded: boolean };
	}>();

	/**
	 * Label text for the toggle button
	 * @type {string}
	 * @default ''
	 */
	export let label: string = '';

	/**
	 * Whether the content is expanded
	 * @type {boolean}
	 * @default false
	 */
	export let expanded: boolean = false;

	/**
	 * Button styling variant
	 * @type {'primary' | 'secondary' | 'outline'}
	 * @default 'primary'
	 */
	export let variant: 'primary' | 'secondary' | 'outline' = 'primary';

	/**
	 * Button size
	 * @type {'small' | 'medium' | 'large'}
	 * @default 'small'
	 */
	export let size: 'sm' | 'md' | 'lg' = 'sm';

	/**
	 * Whether the toggle is disabled
	 * @type {boolean}
	 * @default false
	 */
	export let disabled: boolean = false;

	/**
	 * Additional CSS classes
	 * @type {string}
	 * @default ''
	 */
	let className: string = '';
	export { className as class };

	function handleToggle() {
		if (disabled) return;

		expanded = !expanded;
		dispatch('toggle', { expanded });
	}

	$: chevronTransform = expanded ? 'rotate-180' : 'rotate-0';
</script>

<div class="space-y-0">
	<Button {variant} {size} {disabled} on:click={handleToggle}>
		<div class="flex items-center gap-2">
			{#if $$slots.icon}
				<slot name="icon" />
			{/if}

			<slot name="label">
				{label}
			</slot>
		</div>

		<!-- Chevron icon -->
		<svg
			class="w-4 h-4 transition-transform duration-200 {chevronTransform}"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			aria-hidden="true"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</Button>

	{#if expanded}
		<div
			id="toggle-content"
			class="border border-t-0 border-gray-200 rounded-b-md bg-white"
			transition:slide={{ duration: 200 }}
		>
			<slot />
		</div>
	{/if}
</div>
