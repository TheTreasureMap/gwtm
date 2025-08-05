<!--
@component Carousel
@description A reusable image carousel component with automatic rotation and manual controls
@category UI Primitives  
@version 1.0.0
@author GWTM Team
@since 2024-08-05

@example
```svelte
<Carousel 
  images={[
    { src: '/image1.jpg', alt: 'Description 1' },
    { src: '/image2.jpg', alt: 'Description 2' }
  ]}
  autoPlay={true}
  interval={5000}
/>
```

@prop {Array} images - Array of image objects with src and alt properties
@prop {boolean} autoPlay - Whether to automatically advance slides
@prop {number} interval - Time in milliseconds between auto advances
@prop {string} class - Additional CSS classes
-->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	/**
	 * Array of images to display
	 * @type {Array<{src: string, alt: string}>}
	 */
	export let images: Array<{ src: string; alt: string }> = [];

	/**
	 * Whether to automatically advance slides
	 * @type {boolean}
	 * @default true
	 */
	export let autoPlay: boolean = true;

	/**
	 * Time in milliseconds between auto advances
	 * @type {number}
	 * @default 4000
	 */
	export let interval: number = 4000;

	/**
	 * Additional CSS classes
	 * @type {string}
	 * @default ''
	 */
	let className: string = '';
	export { className as class };

	let currentIndex = 0;
	let intervalId: NodeJS.Timeout | null = null;

	$: totalImages = images.length;

	function nextSlide() {
		currentIndex = (currentIndex + 1) % totalImages;
	}

	function prevSlide() {
		currentIndex = (currentIndex - 1 + totalImages) % totalImages;
	}

	function goToSlide(index: number) {
		currentIndex = index;
	}

	function startAutoPlay() {
		if (autoPlay && totalImages > 1) {
			intervalId = setInterval(nextSlide, interval);
		}
	}

	function stopAutoPlay() {
		if (intervalId) {
			clearInterval(intervalId);
			intervalId = null;
		}
	}

	onMount(() => {
		startAutoPlay();
	});

	onDestroy(() => {
		stopAutoPlay();
	});

	// Restart autoplay when settings change
	$: {
		stopAutoPlay();
		startAutoPlay();
	}
</script>

<div class="relative w-full h-full overflow-hidden rounded-lg bg-gray-100 {className}" 
     on:mouseenter={stopAutoPlay} 
     on:mouseleave={startAutoPlay}
     role="region" 
     aria-label="Image carousel">
	
	{#if totalImages > 0}
		<!-- Images -->
		<div class="relative w-full h-full">
			{#each images as image, index}
				<div 
					class="absolute inset-0 transition-opacity duration-500 ease-in-out"
					class:opacity-100={index === currentIndex}
					class:opacity-0={index !== currentIndex}
				>
					<img 
						src={image.src} 
						alt={image.alt}
						class="w-full h-full object-cover"
						loading="lazy"
					/>
				</div>
			{/each}
		</div>

		{#if totalImages > 1}
			<!-- Navigation dots -->
			<div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
				{#each images as _, index}
					<button
						class="w-3 h-3 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50 {index === currentIndex ? 'bg-white' : 'bg-white/50'}"
						on:click={() => goToSlide(index)}
						aria-label="Go to slide {index + 1}"
					></button>
				{/each}
			</div>

			<!-- Previous/Next buttons -->
			<button
				class="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
				on:click={prevSlide}
				aria-label="Previous image"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
			</button>

			<button
				class="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
				on:click={nextSlide}
				aria-label="Next image"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
			</button>
		{/if}
	{:else}
		<!-- Empty state -->
		<div class="flex items-center justify-center h-full text-gray-500">
			<div class="text-center">
				<svg class="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
				</svg>
				<p class="text-sm">No images to display</p>
			</div>
		</div>
	{/if}
</div>