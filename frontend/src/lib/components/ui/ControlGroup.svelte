<script lang="ts">
	export let label: string = '';
	export let required: boolean = false;
	export let inline: boolean = false;
	export let helpText: string = '';
	export let error: string = '';

	let className: string = '';
	export { className as class };

	import { onMount } from 'svelte';

	export let id: string = '';
	let controlId: string = '';
	onMount(() => {
		if (!id) {
			controlId = `control_${Math.random().toString(36).substring(2, 11)}`;
		}
	});
	$: controlId = id || controlId;

	$: containerClass = [inline ? 'inline-flex items-center gap-2' : 'space-y-1', className]
		.filter(Boolean)
		.join(' ');

	$: labelClass = [
		inline ? 'whitespace-nowrap' : 'block',
		'text-sm font-medium text-gray-700',
		required ? "after:content-['*'] after:ml-0.5 after:text-red-500" : ''
	]
		.filter(Boolean)
		.join(' ');
</script>

<div class={containerClass}>
	{#if label}
		<label for={controlId} class={labelClass}>
			{label}
		</label>
	{/if}

	<div class={inline ? 'flex items-center gap-1' : 'relative'}>
		{#if $$slots.prefix}
			<div class="text-sm text-gray-600">
				<slot name="prefix" />
			</div>
		{/if}

		<div class="flex-1">
			<slot {controlId} />
		</div>

		{#if $$slots.suffix}
			<div class="text-sm text-gray-600">
				<slot name="suffix" />
			</div>
		{/if}
	</div>

	{#if error}
		<p class="text-sm text-red-600" role="alert">
			{error}
		</p>
	{:else if helpText || $$slots.help}
		<div class="text-sm text-gray-500">
			<slot name="help">
				{helpText}
			</slot>
		</div>
	{/if}
</div>
