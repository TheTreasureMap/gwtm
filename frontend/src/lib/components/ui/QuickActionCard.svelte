<script lang="ts">
	import Card from './Card.svelte';
	export let title: string;
	export let description: string;
	export let href: string;
	export let linkText: string;
	export let btnClass: string = 'btn btn-primary';
</script>

<Card>
	<h3 class="text-xl font-semibold mb-4 flex items-center">
		<slot name="icon" />
		{title}
	</h3>
	<p class="text-gray-600 mb-4">{description}</p>
	<a {href} class={btnClass}>{linkText} →</a>
</Card>
