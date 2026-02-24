<script lang="ts">
	/**
	 * @component Card
	 * @description A flexible container component for grouping content with consistent styling
	 * @category UI
	 * @version 1.1.0
	 * @author GWTM Team
	 * @since 2024-01-15
	 *
	 * @accessibility
	 * - Semantic container with proper focus management when clickable
	 * - Keyboard navigation support for interactive cards
	 * - Screen reader compatible with appropriate roles
	 *
	 * @performance
	 * - Minimal DOM overhead with computed CSS classes
	 * - Efficient hover and click state management
	 * - Optimized for both static and interactive use cases
	 *
	 * @example
	 * ```svelte
	 * <!-- Basic content card -->
	 * <Card>
	 *   <h3>Card Title</h3>
	 *   <p>Card content goes here</p>
	 * </Card>
	 *
	 * <!-- Interactive clickable card -->
	 * <Card clickable hover on:click={handleCardClick}>
	 *   <div>Click me!</div>
	 * </Card>
	 *
	 * <!-- Minimal card with no padding -->
	 * <Card padding="none" shadow="sm">
	 *   <img src="image.jpg" alt="Full width image" />
	 * </Card>
	 *
	 * <!-- Large card for hero sections -->
	 * <Card padding="lg" shadow="lg">
	 *   <h1>Hero Title</h1>
	 *   <p>Large hero content</p>
	 * </Card>
	 * ```
	 *
	 * @see Button - For actionable elements
	 * @see Modal - For overlay content containers
	 */

	/**
	 * Internal padding size of the card
	 * @type {'none' | 'sm' | 'md' | 'lg'}
	 * @default 'md'
	 */
	export let padding: 'none' | 'sm' | 'md' | 'lg' = 'md';

	/**
	 * Drop shadow intensity of the card
	 * @type {'none' | 'sm' | 'md' | 'lg'}
	 * @default 'lg'
	 */
	export let shadow: 'none' | 'sm' | 'md' | 'lg' = 'lg';

	/**
	 * Whether to show hover effects (enhanced shadow on hover)
	 * @type {boolean}
	 * @default false
	 */
	export let hover: boolean = false;

	/**
	 * Whether the card is clickable (shows pointer cursor)
	 * @type {boolean}
	 * @default false
	 */
	export let clickable: boolean = false;

	/**
	 * Optional title displayed in the card header
	 * @type {string}
	 * @default ''
	 */
	export let title: string = '';

	/**
	 * Visual variant for the card
	 * @type {'default' | 'info' | 'success' | 'warning' | 'error'}
	 * @default 'default'
	 */
	export let variant: 'default' | 'info' | 'success' | 'warning' | 'error' = 'default';

	/**
	 * Additional CSS classes to apply to the card
	 * @type {string}
	 * @default ''
	 */
	let className: string = '';
	export { className as class };

	import { classBuilder } from '$lib/design-system';

	const variantClasses = {
		default: '',
		info: 'border-l-4 border-l-blue-500',
		success: 'border-l-4 border-l-green-500',
		warning: 'border-l-4 border-l-yellow-500',
		error: 'border-l-4 border-l-red-500'
	};

	$: cardClass = [
		classBuilder.card(padding, hover, shadow !== 'none'),
		variantClasses[variant],
		clickable ? 'cursor-pointer' : '',
		className
	]
		.filter(Boolean)
		.join(' ');
</script>

<!--
@slot header - Optional card header content (takes priority over title prop)
@slot default - Main card content
@slot {string} padding - Current padding size
@slot {string} shadow - Current shadow intensity
@slot {boolean} hover - Whether hover effects are enabled
@slot {boolean} clickable - Whether the card is clickable
-->
{#if clickable}
	<div class={cardClass} on:click on:keydown role="button" tabindex="0" aria-pressed="false">
		{#if $$slots.header}
			<div class="mb-3">
				<slot name="header" />
			</div>
		{:else if title}
			<h3 class="text-lg font-semibold mb-3">{title}</h3>
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
			<h3 class="text-lg font-semibold mb-3">{title}</h3>
		{/if}
		<slot {padding} {shadow} {hover} {clickable} />
	</div>
{/if}
