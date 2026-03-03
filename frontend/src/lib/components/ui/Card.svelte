<script lang="ts">
	export let padding: 'none' | 'sm' | 'md' | 'lg' = 'md';
	export let shadow: 'none' | 'sm' | 'md' | 'lg' = 'lg';
	export let hover: boolean = false;
	export let clickable: boolean = false;
	export let title: string = '';
	export let variant: 'default' | 'info' | 'success' | 'warning' | 'error' = 'default';

	let className: string = '';
	export { className as class };

	const paddingClasses: Record<string, string> = {
		none: '',
		sm: 'p-4',
		md: 'p-6',
		lg: 'p-8'
	};

	const shadowClasses: Record<string, string> = {
		none: 'shadow-none',
		sm: 'shadow-sm',
		md: 'shadow-md',
		lg: 'shadow-lg'
	};

	const variantClasses: Record<string, string> = {
		default: '',
		info: 'border-l-4 border-l-blue-500',
		success: 'border-l-4 border-l-green-500',
		warning: 'border-l-4 border-l-yellow-500',
		error: 'border-l-4 border-l-red-500'
	};

	$: cardClass = [
		'card bg-base-100',
		paddingClasses[padding],
		shadowClasses[shadow],
		hover ? 'hover:shadow-xl transition-shadow duration-200' : '',
		variantClasses[variant],
		clickable ? 'cursor-pointer' : '',
		className
	]
		.filter(Boolean)
		.join(' ');
</script>

{#if clickable}
	<div class={cardClass} on:click on:keydown role="button" tabindex="0" aria-pressed="false">
		{#if $$slots.header}
			<div class="mb-3">
				<slot name="header" />
			</div>
		{:else if title}
			<h3 class="card-title mb-3">{title}</h3>
		{/if}
		<slot {padding} {shadow} {hover} {clickable} />
	</div>
{:else}
	<div class={cardClass}>
		{#if $$slots.header}
			<div class="mb-3">
				<slot name="header" />
			</div>
		{:else if title}
			<h3 class="card-title mb-3">{title}</h3>
		{/if}
		<slot {padding} {shadow} {hover} {clickable} />
	</div>
{/if}
