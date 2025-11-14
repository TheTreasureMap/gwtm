<!--
@component ControlGroup
@description A reusable form control group component that wraps label, input, and error display
@category UI Primitives
@version 1.0.0
@author GWTM Team
@since 2024-01-25

@example
```svelte
<ControlGroup label="Instrument" required>
  <select bind:value={selectedInstrument} class="form-select">
    <option value="">Select instrument...</option>
    {#each instruments as instrument}
      <option value={instrument.id}>{instrument.name}</option>
    {/each}
  </select>
</ControlGroup>

<ControlGroup label="Coverage" inline>
  <input type="number" bind:value={coverage} class="form-input" />
  <span slot="suffix">%</span>
</ControlGroup>
```

@prop {string} label - Label text for the control
@prop {boolean} required - Whether the field is required
@prop {boolean} inline - Whether to display inline vs stacked
@prop {string} helpText - Optional help text below the control
@prop {string} error - Error message to display
@prop {string} class - Additional CSS classes

@slot default - The form control element
@slot prefix - Content before the control (inline mode)
@slot suffix - Content after the control (inline mode)
@slot help - Custom help content
-->
<script lang="ts">
	/**
	 * Label text for the control
	 * @type {string}
	 * @default ''
	 */
	export let label: string = '';

	/**
	 * Whether the field is required
	 * @type {boolean}
	 * @default false
	 */
	export let required: boolean = false;

	/**
	 * Whether to display inline vs stacked
	 * @type {boolean}
	 * @default false
	 */
	export let inline: boolean = false;

	/**
	 * Optional help text below the control
	 * @type {string}
	 * @default ''
	 */
	export let helpText: string = '';

	/**
	 * Error message to display
	 * @type {string}
	 * @default ''
	 */
	export let error: string = '';

	/**
	 * Additional CSS classes
	 * @type {string}
	 * @default ''
	 */
	let className: string = '';
	export { className as class };

	// Generate unique ID for accessibility
	const controlId = `control_${Math.random().toString(36).substr(2, 9)}`;

	$: containerClass = [inline ? 'inline-flex items-center gap-2' : 'space-y-1', className]
		.filter(Boolean)
		.join(' ');

	$: labelClass = [
		inline ? 'whitespace-nowrap' : 'block',
		'text-sm font-medium text-gray-700',
		required ? "after:content-['*'] after:ml-0.5 after:text-red-500" : ''
	]
		.filter(Boolean)
		.join(' ');
</script>

<div class={containerClass}>
	{#if label}
		<label for={controlId} class={labelClass}>
			{label}
		</label>
	{/if}

	<div class={inline ? 'flex items-center gap-1' : 'relative'}>
		{#if $$slots.prefix}
			<div class="text-sm text-gray-600">
				<slot name="prefix" />
			</div>
		{/if}

		<div class="flex-1">
			<slot {controlId} />
		</div>

		{#if $$slots.suffix}
			<div class="text-sm text-gray-600">
				<slot name="suffix" />
			</div>
		{/if}
	</div>

	{#if error}
		<p class="text-sm text-red-600" role="alert">
			{error}
		</p>
	{:else if helpText || $$slots.help}
		<div class="text-sm text-gray-500">
			<slot name="help">
				{helpText}
			</slot>
		</div>
	{/if}
</div>

<style>
	/* CSS for required field asterisk */
	.required-marker::after {
		content: '*';
		color: #ef4444;
		margin-left: 0.125rem;
	}
</style>
