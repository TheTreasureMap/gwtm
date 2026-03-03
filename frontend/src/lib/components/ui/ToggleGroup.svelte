<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { slide } from 'svelte/transition';
	import Button from './Button.svelte';

	const dispatch = createEventDispatcher<{
		toggle: { expanded: boolean };
	}>();

	export let label: string = '';
	export let expanded: boolean = false;
	export let variant: 'primary' | 'secondary' | 'outline' = 'primary';
	export let size: 'sm' | 'md' | 'lg' = 'sm';
	export let disabled: boolean = false;

	let className: string = '';
	export { className as class };

	function handleToggle() {
		if (disabled) return;
		expanded = !expanded;
		dispatch('toggle', { expanded });
	}
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

		<svg
			class="w-4 h-4 transition-transform duration-200"
			class:rotate-180={expanded}
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
			class="border border-t-0 border-gray-200 rounded-b-md bg-white"
			transition:slide={{ duration: 200 }}
		>
			<slot />
		</div>
	{/if}
</div>
