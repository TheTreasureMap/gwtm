<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let pointingStatus: string = 'completed';
	export let timeRange: number[] = [-1, 7];
	export let minTime: number = -1;
	export let maxTime: number = 7;
	export let loading: boolean = false;

	const dispatch = createEventDispatcher();

	// Time slider drag handling
	let isDragging = false;
	let dragHandle: 'min' | 'max' | null = null;

	function startDrag(e: MouseEvent | TouchEvent, handle: 'min' | 'max') {
		e.preventDefault();
		isDragging = true;
		dragHandle = handle;

		// Add global event listeners
		if (typeof window !== 'undefined') {
			document.addEventListener('mousemove', handleDrag);
			document.addEventListener('mouseup', stopDrag);
			document.addEventListener('touchmove', handleDrag, { passive: false });
			document.addEventListener('touchend', stopDrag);
		}
	}

	function handleDrag(e: MouseEvent | TouchEvent) {
		if (!isDragging || !dragHandle) return;

		e.preventDefault();

		// Get the slider wrapper element
		const sliderWrapper = document.querySelector('.time-slider-wrapper');
		if (!sliderWrapper) return;

		const rect = sliderWrapper.getBoundingClientRect();
		const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
		const percent = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
		const newValue = minTime + (percent / 100) * (maxTime - minTime);

		if (dragHandle === 'min') {
			timeRange[0] = Math.min(newValue, timeRange[1]);
		} else {
			timeRange[1] = Math.max(newValue, timeRange[0]);
		}

		// Trigger reactivity
		timeRange = [...timeRange];

		// Notify parent of time range change
		dispatch('timeRangeChange', { timeRange: [...timeRange] });
	}

	function stopDrag() {
		isDragging = false;
		dragHandle = null;

		// Remove global event listeners
		if (typeof window !== 'undefined') {
			document.removeEventListener('mousemove', handleDrag);
			document.removeEventListener('mouseup', stopDrag);
			document.removeEventListener('touchmove', handleDrag);
			document.removeEventListener('touchend', stopDrag);
		}
	}

	function handlePointingStatusChange(e: Event) {
		const value = (e.target as HTMLSelectElement).value;
		dispatch('pointingStatusChange', { pointingStatus: value });
	}

	// Cleanup on destroy
	import { onDestroy } from 'svelte';
	onDestroy(() => {
		if (typeof window !== 'undefined') {
			document.removeEventListener('mousemove', handleDrag);
			document.removeEventListener('mouseup', stopDrag);
			document.removeEventListener('touchmove', handleDrag);
			document.removeEventListener('touchend', stopDrag);
		}
	});
</script>

<!-- Time Controls Section -->
<div class="bg-white border rounded-lg p-4">
	<h3 class="text-lg font-semibold mb-3">Time Controls</h3>
	<div class="mb-4">
		<label class="block text-sm font-medium text-gray-700 mb-2"> Pointing Status: </label>
		<select
			value={pointingStatus}
			on:change={handlePointingStatusChange}
			class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
			disabled={loading}
		>
			<option value="completed">Completed</option>
			<option value="planned">Planned</option>
			<option value="all">All</option>
		</select>
	</div>

	<div class="mb-4">
		<label class="block text-sm font-medium text-gray-700 mb-2">
			Date range (days since Time of Signal): {timeRange[0].toFixed(1)} - {timeRange[1].toFixed(1)}
		</label>

		<!-- Time Range Slider -->
		<div class="time-slider-container mt-4">
			<div class="time-slider-wrapper">
				<div class="time-slider-track"></div>
				<div
					class="time-slider-range"
					style="left: {((timeRange[0] - minTime) / (maxTime - minTime)) * 100}%; 
						   width: {((timeRange[1] - timeRange[0]) / (maxTime - minTime)) * 100}%"
				></div>

				<!-- Min handle -->
				<div
					class="time-slider-handle min-handle"
					class:dragging={isDragging && dragHandle === 'min'}
					style="left: {((timeRange[0] - minTime) / (maxTime - minTime)) * 100}%"
					on:mousedown={(e) => startDrag(e, 'min')}
					on:touchstart={(e) => startDrag(e, 'min')}
					title="Minimum time: {timeRange[0].toFixed(1)} days"
				></div>

				<!-- Max handle -->
				<div
					class="time-slider-handle max-handle"
					class:dragging={isDragging && dragHandle === 'max'}
					style="left: {((timeRange[1] - minTime) / (maxTime - minTime)) * 100}%"
					on:mousedown={(e) => startDrag(e, 'max')}
					on:touchstart={(e) => startDrag(e, 'max')}
					title="Maximum time: {timeRange[1].toFixed(1)} days"
				></div>
			</div>

			<!-- Time labels -->
			<div class="time-labels mt-2">
				<span class="text-xs text-gray-500">{minTime.toFixed(1)} days</span>
				<span class="text-xs text-gray-500 float-right">{maxTime.toFixed(1)} days</span>
			</div>
		</div>
	</div>
</div>

<style>
	/* Time slider styles */
	.time-slider-container {
		width: 100%;
		margin-top: 1rem;
	}

	.time-slider-wrapper {
		position: relative;
		height: 20px;
		width: 100%;
		cursor: pointer;
	}

	.time-slider-track {
		position: absolute;
		top: 50%;
		left: 0;
		right: 0;
		height: 4px;
		background-color: #e5e7eb; /* gray-200 */
		border-radius: 2px;
		transform: translateY(-50%);
	}

	.time-slider-range {
		position: absolute;
		top: 50%;
		height: 4px;
		background-color: #3b82f6; /* blue-500 */
		border-radius: 2px;
		transform: translateY(-50%);
	}

	.time-slider-handle {
		position: absolute;
		top: 50%;
		width: 16px;
		height: 16px;
		background-color: #3b82f6; /* blue-500 */
		border: 2px solid white;
		border-radius: 50%;
		cursor: grab;
		transform: translate(-50%, -50%);
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
		z-index: 10;
		transition: transform 0.1s ease;
	}

	.time-slider-handle:hover {
		transform: translate(-50%, -50%) scale(1.1);
	}

	.time-slider-handle:active,
	.time-slider-handle.dragging {
		cursor: grabbing;
		transform: translate(-50%, -50%) scale(1.15);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
	}

	.time-labels {
		display: flex;
		justify-content: space-between;
		margin-top: 0.5rem;
	}

	select:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>
