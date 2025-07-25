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

<!--
@slot default - Main card content
@slot {string} padding - Current padding size
@slot {string} shadow - Current shadow intensity
@slot {boolean} hover - Whether hover effects are enabled
@slot {boolean} clickable - Whether the card is clickable
-->
<div
	class={cardClass}
	on:click
	on:keydown
	role={clickable ? 'button' : undefined}
	tabindex={clickable ? 0 : undefined}
	aria-pressed={clickable ? 'false' : undefined}
>
	<slot {padding} {shadow} {hover} {clickable} />
</div>
