<script lang="ts">
	export let maxWidth: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '4xl' | '7xl' = '7xl';
	export let padding: 'sm' | 'md' | 'lg' = 'md';

	const maxWidthClasses = {
		sm: 'max-w-sm',
		md: 'max-w-md',
		lg: 'max-w-lg',
		xl: 'max-w-xl',
		'2xl': 'max-w-2xl',
		'4xl': 'max-w-4xl',
		'7xl': 'max-w-7xl'
	};

	const paddingClasses = {
		sm: 'px-4 py-4',
		md: 'px-4 py-8',
		lg: 'px-6 py-12'
	};

	$: containerClass = `${maxWidthClasses[maxWidth]} mx-auto ${paddingClasses[padding]}`;
</script>

<div class={containerClass}>
	<slot />
</div>
