<script lang="ts">
	export let size: 'sm' | 'md' | 'lg' | 'xl' = 'md';
	export let message: string = '';
	export let centered: boolean = true;

	const sizeClasses: Record<string, string> = {
		sm: 'h-4 w-4',
		md: 'h-8 w-8',
		lg: 'h-16 w-16',
		xl: 'h-32 w-32'
	};

	let spinnerClass: string = '';
	let containerClass: string = '';

	$: spinnerClass = `animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses[size]}`;
	$: containerClass = centered ? 'flex justify-center items-center py-12' : '';
</script>

<div class={containerClass}>
	<div class="text-center" role="status" aria-live="polite">
		<div
			class={spinnerClass}
			aria-label={message || 'Loading'}
			aria-hidden={!message && $$slots.default ? 'true' : 'false'}
		></div>
		{#if message}
			<p class="mt-2 text-gray-600">{message}</p>
		{/if}
		<slot {message} {size} {centered} />
	</div>
</div>
