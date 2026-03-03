<script lang="ts">
	export let message: string = 'Loading...';
	export let size: 'small' | 'medium' | 'large' = 'medium';
	export let showSpinner: boolean = true;
	export let inline: boolean = false;

	let className: string = '';
	export { className as class };

	export let spinnerClass: string = '';

	$: containerClass = [
		inline ? 'inline-flex' : 'flex',
		'items-center justify-center gap-3',
		inline ? '' : 'flex-col',
		className
	]
		.filter(Boolean)
		.join(' ');

	$: spinnerSize = { small: 'h-4 w-4', medium: 'h-8 w-8', large: 'h-12 w-12' }[size];
	$: textSize = { small: 'text-sm', medium: 'text-base', large: 'text-lg' }[size];
</script>

<div class={containerClass} role="status" aria-live="polite" aria-label={message}>
	{#if showSpinner}
		<div
			class="animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 {spinnerSize} {spinnerClass}"
			aria-hidden="true"
		></div>
	{/if}

	<div class="text-gray-600 {textSize}">
		<slot>
			{message}
		</slot>
	</div>
</div>
