<script lang="ts">
	export let variant: 'success' | 'warning' | 'error' | 'info' | 'neutral' = 'neutral';
	export let label: string = '';
	export let size: 'small' | 'medium' | 'large' = 'medium';
	export let pulse: boolean = false;

	export let icon: string = '';

	let className: string = '';
	export { className as class };

	const variantClasses: Record<string, string> = {
		success: 'badge badge-success',
		warning: 'badge badge-warning',
		error: 'badge badge-error',
		info: 'badge badge-info',
		neutral: 'badge badge-neutral'
	};

	const sizeClasses: Record<string, string> = {
		small: 'badge-sm',
		medium: '',
		large: 'badge-lg'
	};

	const iconSizeClasses: Record<string, string> = {
		small: 'w-3 h-3',
		medium: 'w-4 h-4',
		large: 'w-5 h-5'
	};

	$: badgeClass = [
		variantClasses[variant],
		sizeClasses[size],
		pulse ? 'animate-pulse' : '',
		className
	]
		.filter(Boolean)
		.join(' ');

	$: iconSize = iconSizeClasses[size];

	$: iconSymbol =
		{
			check: '✓',
			warning: '⚠',
			error: '✗',
			info: 'ℹ',
			clock: '⏰',
			loading: '◐'
		}[icon] || '';
</script>

<span class={badgeClass} role="status">
	{#if icon || $$slots.icon}
		<span class={iconSize} aria-hidden="true">
			<slot name="icon">
				{iconSymbol}
			</slot>
		</span>
	{/if}

	<slot>
		{label}
	</slot>
</span>
