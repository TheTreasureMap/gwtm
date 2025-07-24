<script lang="ts">
	export let padding: 'none' | 'sm' | 'md' | 'lg' = 'md';
	export let shadow: 'none' | 'sm' | 'md' | 'lg' = 'lg';
	export let hover: boolean = false;
	export let clickable: boolean = false;

	const paddingClasses = {
		none: '',
		sm: 'p-4',
		md: 'p-6',
		lg: 'p-8'
	};

	const shadowClasses = {
		none: '',
		sm: 'shadow-sm',
		md: 'shadow-md',
		lg: 'shadow-lg'
	};

	$: cardClass = [
		'bg-white rounded-lg',
		shadowClasses[shadow],
		paddingClasses[padding],
		hover ? 'hover:shadow-xl transition-shadow duration-200' : '',
		clickable ? 'cursor-pointer' : ''
	]
		.filter(Boolean)
		.join(' ');
</script>

<div class={cardClass} on:click on:keydown>
	<slot />
</div>