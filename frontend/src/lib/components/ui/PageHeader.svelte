<script lang="ts">
	export let title: string;
	export let description: string = '';
	export let size: 'sm' | 'md' | 'lg' = 'md';

	const titleClasses = {
		sm: 'text-2xl font-bold text-gray-900 mb-2',
		md: 'text-3xl font-bold text-gray-900 mb-4',
		lg: 'text-4xl font-bold text-gray-900 mb-4'
	};

	const descriptionClasses = {
		sm: 'text-base text-gray-600',
		md: 'text-lg text-gray-600',
		lg: 'text-lg text-gray-600'
	};

	$: titleClass = titleClasses[size];
	$: descriptionClass = descriptionClasses[size];
</script>

<div class="mb-8">
	<h1 class={titleClass}>{title}</h1>
	{#if description}
		<p class={descriptionClass}>{description}</p>
	{/if}
	<slot />
</div>