<script lang="ts">
	/**
	 * @component ConditionalSection
	 * @description A component that conditionally shows/hides content based on form state
	 * @category Forms
	 * @version 1.0.0
	 * @author GWTM Team
	 * @since 2024-01-25
	 */

	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	/**
	 * Whether the section should be visible
	 * @type {boolean}
	 * @default false
	 */
	export let show: boolean = false;

	/**
	 * CSS class for the section container
	 * @type {string}
	 * @default ''
	 */
	export let className: string = '';

	/**
	 * Animation duration in milliseconds
	 * @type {number}
	 * @default 300
	 */
	export let duration: number = 300;

	/**
	 * Section title (optional)
	 * @type {string}
	 * @default ''
	 */
	export let title: string = '';

	/**
	 * Whether to use slide animation
	 * @type {boolean}
	 * @default true
	 */
	export let animate: boolean = true;

	// Animation functions
	function slideDown(node: HTMLElement, { duration = 300 }) {
		return {
			duration,
			css: (t: number) => `
				max-height: ${t * node.scrollHeight}px;
				opacity: ${t};
				overflow: hidden;
			`
		};
	}

	function slideUp(node: HTMLElement, { duration = 300 }) {
		return {
			duration,
			css: (t: number) => `
				max-height: ${t * node.scrollHeight}px;
				opacity: ${t};
				overflow: hidden;
			`
		};
	}
</script>

{#if show}
	<div
		class="conditional-section {className}"
		in:slideDown={{ duration: animate ? duration : 0 }}
		out:slideUp={{ duration: animate ? duration : 0 }}
	>
		{#if title}
			<h3 class="section-title">{title}</h3>
		{/if}
		<div class="section-content">
			<slot />
		</div>
	</div>
{/if}

<style>
	.conditional-section {
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		padding: 1rem;
		margin: 1rem 0;
		background-color: #f9fafb;
		overflow: hidden;
	}

	.section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: #374151;
		margin: 0 0 1rem 0;
	}

	.section-content {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	/* Theme variations */
	.conditional-section.planned {
		border-color: #3b82f6;
		background-color: #eff6ff;
	}

	.conditional-section.completed {
		border-color: #10b981;
		background-color: #ecfdf5;
	}

	.conditional-section.cancelled {
		border-color: #ef4444;
		background-color: #fef2f2;
	}

	/* Reduced motion support */
	@media (prefers-reduced-motion: reduce) {
		.conditional-section {
			transition: none;
		}
	}
</style>