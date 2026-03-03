<script lang="ts">
	import { fly } from 'svelte/transition';
	import { globalErrors, errorHandler } from '$lib/utils/errorHandling';

	const alertClass: Record<string, string> = {
		error: 'alert-error',
		warning: 'alert-warning',
		info: 'alert-info'
	};
</script>

<div class="toast toast-top toast-end z-50">
	{#each $globalErrors as error (error.id)}
		<div
			class="alert {alertClass[error.type] ?? 'alert-info'} shadow-lg max-w-sm"
			transition:fly={{ x: 100, duration: 200 }}
		>
			<span class="font-semibold">{error.message}</span>
			{#if error.context}
				<span class="text-sm">{error.context}</span>
			{/if}
			{#if error.dismissible}
				<button
					class="btn btn-sm btn-ghost ml-auto"
					on:click={() => errorHandler.dismissError(error.id)}>✕</button
				>
			{/if}
		</div>
	{/each}
</div>
