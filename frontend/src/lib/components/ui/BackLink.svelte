<script lang="ts">
	export let href: string;
</script>

<div class="mt-8">
	<a {href} class="inline-flex items-center text-blue-600 hover:text-blue-800">
		<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
		</svg>
		<slot />
	</a>
</div>
