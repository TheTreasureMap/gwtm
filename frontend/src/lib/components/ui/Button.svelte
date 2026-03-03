<script lang="ts">
	export let variant: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' = 'primary';
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let disabled: boolean = false;
	export let loading: boolean = false;
	export let fullWidth: boolean = false;
	export let type: 'button' | 'submit' | 'reset' = 'button';
	export let href: string | undefined = undefined;

	const variantClasses: Record<string, string> = {
		primary: 'btn-primary',
		secondary: 'btn-secondary',
		ghost: 'btn-ghost',
		outline: 'btn-outline',
		danger: 'btn-error'
	};

	const sizeClasses: Record<string, string> = {
		sm: 'btn-sm',
		md: '',
		lg: 'btn-lg'
	};

	$: buttonClass = [
		'btn',
		variantClasses[variant],
		sizeClasses[size],
		fullWidth ? 'w-full' : '',
		disabled || loading ? 'opacity-50 cursor-not-allowed' : '',
		loading ? 'pointer-events-none' : ''
	]
		.filter(Boolean)
		.join(' ');
</script>

{#if href && !disabled}
	<a {href} class={buttonClass} on:click role="button" aria-disabled={disabled} aria-busy={loading}>
		{#if loading}
			<span
				class="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-current border-t-transparent rounded-full"
				aria-hidden="true"
			></span>
		{/if}
		<slot {loading} {disabled} {variant} {size} />
	</a>
{:else}
	<button {type} {disabled} class={buttonClass} on:click aria-busy={loading}>
		{#if loading}
			<span
				class="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-current border-t-transparent rounded-full"
				aria-hidden="true"
			></span>
		{/if}
		<slot {loading} {disabled} {variant} {size} />
	</button>
{/if}
