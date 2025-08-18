<script lang="ts">
	/**
	 * @component PageContainer
	 * @description A responsive container component for page content with consistent max-width and padding
	 * @category Layout
	 * @version 1.1.0
	 * @author GWTM Team
	 * @since 2024-01-15
	 *
	 * @accessibility
	 * - Semantic container structure for page content
	 * - Responsive design that adapts to all screen sizes
	 * - Proper spacing that meets WCAG guidelines
	 *
	 * @performance
	 * - Efficient CSS class computation
	 * - No JavaScript overhead
	 * - Optimized for responsive layouts
	 *
	 * @example
	 * ```svelte
	 * <!-- Basic page container -->
	 * <PageContainer>
	 *   <h1>Page Title</h1>
	 *   <p>Page content goes here</p>
	 * </PageContainer>
	 *
	 * <!-- Narrow content container -->
	 * <PageContainer maxWidth="2xl" padding="lg">
	 *   <article>
	 *     <h1>Article Title</h1>
	 *     <p>Long form content...</p>
	 *   </article>
	 * </PageContainer>
	 *
	 * <!-- Minimal padding for full-width content -->
	 * <PageContainer padding="sm">
	 *   <div class="bg-gray-100 -mx-4 px-4 py-8">
	 *     Full-width section
	 *   </div>
	 * </PageContainer>
	 *
	 * <!-- Small container for forms -->
	 * <PageContainer maxWidth="md">
	 *   <form>
	 *     <!-- Form content -->
	 *   </form>
	 * </PageContainer>
	 * ```
	 *
	 * @see PageHeader - For consistent page headers
	 * @see Card - For content sections within pages
	 */

	/**
	 * Maximum width of the container
	 * @type {'sm' | 'md' | 'lg' | 'xl' | '2xl' | '4xl' | '7xl'}
	 * @default '7xl'
	 */
	export let maxWidth: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '4xl' | '7xl' = '7xl';

	/**
	 * Padding around the container content
	 * @type {'sm' | 'md' | 'lg'}
	 * @default 'md'
	 */
	export let padding: 'sm' | 'md' | 'lg' = 'md';

	import { classBuilder } from '$lib/design-system';

	// Map maxWidth to container size
	$: containerSize =
		maxWidth === '7xl'
			? 'responsive'
			: maxWidth === '4xl'
				? 'lg'
				: maxWidth === '2xl'
					? 'md'
					: 'sm';

	$: containerClass = classBuilder.container(containerSize, padding);
</script>

<!--
@slot default - Page content
@slot {string} maxWidth - Current maximum width setting
@slot {string} padding - Current padding setting
-->
<div class={containerClass}>
	<slot {maxWidth} {padding} />
</div>
