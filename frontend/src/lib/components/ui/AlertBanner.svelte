<!--
@component AlertBanner
@description A reusable alert banner component for displaying important messages with consistent styling
@category UI Primitives
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<AlertBanner variant="warning" title="Test Alert">
  This is a test gravitational wave alert for development purposes.
</AlertBanner>

<AlertBanner variant="error" title="Alert Retracted" dismissible>
  This alert has been retracted by LIGO/Virgo.
</AlertBanner>

<AlertBanner variant="info" icon="info">
  Processing skymap data...
</AlertBanner>
```

@prop {'info' | 'warning' | 'error' | 'success'} variant - Alert variant for styling
@prop {string} title - Optional title for the alert
@prop {boolean} dismissible - Whether the alert can be dismissed
@prop {string} icon - Optional icon name
@prop {string} class - Additional CSS classes

@slot default - Alert content
@slot icon - Custom icon content
@slot actions - Custom action buttons

@event dismiss - Fired when alert is dismissed
-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{
		dismiss: void;
	}>();

	/**
	 * Alert variant for styling
	 * @type {'info' | 'warning' | 'error' | 'success'}
	 * @default 'info'
	 */
	export let variant: 'info' | 'warning' | 'error' | 'success' = 'info';

	/**
	 * Optional title for the alert
	 * @type {string}
	 * @default ''
	 */
	export let title: string = '';

	/**
	 * Whether the alert can be dismissed
	 * @type {boolean}
	 * @default false
	 */
	export let dismissible: boolean = false;

	/**
	 * Optional icon name
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

	let visible = true;

	// Variant styles
	$: variantClasses = {
		info: 'bg-blue-50 border-blue-200 text-blue-900',
		warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
		error: 'bg-red-50 border-red-200 text-red-900',
		success: 'bg-green-50 border-green-200 text-green-900'
	}[variant];

	// Icon styles
	$: iconClasses = {
		info: 'text-blue-400',
		warning: 'text-yellow-400',
		error: 'text-red-400',
		success: 'text-green-400'
	}[variant];

	$: alertClass = ['border rounded-lg p-4', variantClasses, className].filter(Boolean).join(' ');

	// Default icons
	$: defaultIcon = {
		info: 'ℹ',
		warning: '⚠',
		error: '✗',
		success: '✓'
	}[variant];

	function handleDismiss() {
		visible = false;
		dispatch('dismiss');
	}
</script>

{#if visible}
	<div class={alertClass} role="alert">
		<div class="flex">
			{#if icon || $$slots.icon}
				<div class="flex-shrink-0">
					<div class="w-5 h-5 {iconClasses}">
						<slot name="icon">
							{icon || defaultIcon}
						</slot>
					</div>
				</div>
			{/if}

			<div class="ml-3 flex-1">
				{#if title}
					<h3 class="text-sm font-medium mb-1">
						{title}
					</h3>
				{/if}

				<div class="text-sm">
					<slot />
				</div>

				{#if $$slots.actions}
					<div class="mt-3">
						<slot name="actions" />
					</div>
				{/if}
			</div>

			{#if dismissible}
				<div class="ml-auto pl-3">
					<div class="-mx-1.5 -my-1.5">
						<button
							type="button"
							class="inline-flex rounded-md p-1.5 {iconClasses} hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
							on:click={handleDismiss}
							aria-label="Dismiss alert"
						>
							<span class="sr-only">Dismiss</span>
							<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
								<path
									fill-rule="evenodd"
									d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}
