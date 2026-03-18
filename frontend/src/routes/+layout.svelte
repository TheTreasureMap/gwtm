<script>
	import '../app.css';
	import Navigation from '$lib/components/layout/Navigation.svelte';
	import ErrorToast from '$lib/components/ui/ErrorToast.svelte';
</script>

<Navigation />
<main class="min-h-screen">
	<slot />
</main>

<!-- Global error toast notifications -->
<ErrorToast />
