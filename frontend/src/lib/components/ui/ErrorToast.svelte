<script lang="ts">
	import { globalErrors, errorHandler, type AppError } from '$lib/utils/errorHandling';
	import { fade, fly } from 'svelte/transition';
	import { flip } from 'svelte/animate';

	function getIconForType(type: AppError['type']) {
		switch (type) {
			case 'error':
				return '❌';
			case 'warning':
				return '⚠️';
			case 'info':
				return 'ℹ️';
			default:
				return '•';
		}
	}

	function getColorClasses(type: AppError['type']) {
		switch (type) {
			case 'error':
				return {
					container: 'bg-red-50 border-red-200 text-red-800',
					icon: 'text-red-600',
					button: 'text-red-600 hover:text-red-800 hover:bg-red-100'
				};
			case 'warning':
				return {
					container: 'bg-yellow-50 border-yellow-200 text-yellow-800',
					icon: 'text-yellow-600',
					button: 'text-yellow-600 hover:text-yellow-800 hover:bg-yellow-100'
				};
			case 'info':
				return {
					container: 'bg-blue-50 border-blue-200 text-blue-800',
					icon: 'text-blue-600',
					button: 'text-blue-600 hover:text-blue-800 hover:bg-blue-100'
				};
			default:
				return {
					container: 'bg-gray-50 border-gray-200 text-gray-800',
					icon: 'text-gray-600',
					button: 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
				};
		}
	}

	function formatTimestamp(timestamp: Date): string {
		return timestamp.toLocaleTimeString([], {
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<!-- Toast Container -->
<div class="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
	{#each $globalErrors as error (error.id)}
		{@const colors = getColorClasses(error.type)}
		<div
			class="border rounded-lg shadow-lg {colors.container} p-4 min-w-80"
			animate:flip={{ duration: 200 }}
			in:fly={{ x: 300, duration: 200 }}
			out:fade={{ duration: 150 }}
			role="alert"
			aria-live="polite"
		>
			<div class="flex items-start justify-between">
				<div class="flex items-start space-x-3 flex-1">
					<!-- Icon -->
					<div class="flex-shrink-0 {colors.icon} text-lg">
						{getIconForType(error.type)}
					</div>

					<!-- Content -->
					<div class="flex-1 min-w-0">
						<div class="text-sm font-medium">
							{error.message}
						</div>

						{#if error.context}
							<div class="text-xs opacity-75 mt-1">
								{error.context}
							</div>
						{/if}

						<div class="text-xs opacity-60 mt-1">
							{formatTimestamp(error.timestamp)}
						</div>

						{#if error.details && import.meta.env.DEV}
							<details class="mt-2">
								<summary class="text-xs cursor-pointer hover:opacity-80"> Details </summary>
								<pre
									class="text-xs mt-1 whitespace-pre-wrap bg-black bg-opacity-10 p-2 rounded max-h-32 overflow-auto">
									{JSON.stringify(error.details, null, 2)}
								</pre>
							</details>
						{/if}
					</div>
				</div>

				<!-- Dismiss Button -->
				{#if error.dismissible}
					<button
						type="button"
						class="flex-shrink-0 ml-2 p-1 rounded-md {colors.button} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-opacity-50 transition-colors"
						on:click={() => errorHandler.dismissError(error.id)}
						aria-label="Dismiss notification"
					>
						<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
							<path
								fill-rule="evenodd"
								d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
				{/if}
			</div>
		</div>
	{/each}
</div>

<!-- Clear All Button (only show when there are multiple errors) -->
{#if $globalErrors.length > 1}
	<div class="fixed top-4 right-4 z-40">
		<button
			type="button"
			class="mt-2 px-3 py-1 text-xs bg-gray-700 text-white rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
			on:click={errorHandler.clearAllErrors}
		>
			Clear All ({$globalErrors.length})
		</button>
	</div>
{/if}
