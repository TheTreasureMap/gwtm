<!--
@component StatusBadge
@description A reusable status badge component for displaying status information with consistent styling
@category UI Primitives
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<StatusBadge variant="success" label="Active" />
<StatusBadge variant="warning" label="Pending" size="large" />
<StatusBadge variant="error" label="Failed" icon="alert-circle" />
<StatusBadge variant="info" label="Processing" pulse={true} />
```

@prop {'success' | 'warning' | 'error' | 'info' | 'neutral'} variant - Badge variant for styling
@prop {string} label - Text to display in the badge
@prop {'small' | 'medium' | 'large'} size - Size of the badge
@prop {boolean} pulse - Whether to show a pulsing animation
@prop {string} icon - Optional icon name to display
@prop {string} class - Additional CSS classes

@slot default - Custom content instead of label
@slot icon - Custom icon content
-->
<script lang="ts">
	/**
	 * Badge variant for styling
	 * @type {'success' | 'warning' | 'error' | 'info' | 'neutral'}
	 * @default 'neutral'
	 */
	export let variant: 'success' | 'warning' | 'error' | 'info' | 'neutral' = 'neutral';

	/**
	 * Text to display in the badge
	 * @type {string}
	 * @default ''
	 */
	export let label: string = '';

	/**
	 * Size of the badge
	 * @type {'small' | 'medium' | 'large'}
	 * @default 'medium'
	 */
	export let size: 'small' | 'medium' | 'large' = 'medium';

	/**
	 * Whether to show a pulsing animation
	 * @type {boolean}
	 * @default false
	 */
	export let pulse: boolean = false;

	/**
	 * Optional icon name to display
	 * @type {string}
	 * @default ''
	 */
	export let icon: string = '';

	/**
	 * Additional CSS classes
	 * @type {string}
	 * @default ''
	 */
	let className: string = '';
	export { className as class };

	// Variant styles
	$: variantClasses = {
		success: 'bg-green-100 text-green-800 border-green-200',
		warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
		error: 'bg-red-100 text-red-800 border-red-200',
		info: 'bg-blue-100 text-blue-800 border-blue-200',
		neutral: 'bg-gray-100 text-gray-800 border-gray-200'
	}[variant];

	// Size styles
	$: sizeClasses = {
		small: 'px-2 py-0.5 text-xs',
		medium: 'px-2.5 py-1 text-sm',
		large: 'px-3 py-1.5 text-base'
	}[size];

	// Icon sizes
	$: iconSize = {
		small: 'w-3 h-3',
		medium: 'w-4 h-4',
		large: 'w-5 h-5'
	}[size];

	$: badgeClass = [
		'inline-flex items-center gap-1.5 font-medium rounded-full border',
		variantClasses,
		sizeClasses,
		pulse ? 'animate-pulse' : '',
		className
	]
		.filter(Boolean)
		.join(' ');

	// Simple icon mappings (could be extended with a proper icon system)
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

<style>
	/* Pulse animation */
	.animate-pulse {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}
</style>
