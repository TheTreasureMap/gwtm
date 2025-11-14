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

	// Reactive calculations for slider positioning
	$: range = maxTime - minTime;
	$: minHandlePosition = range > 0 ? ((timeRange[0] - minTime) / range) * 100 : 0;
	$: maxHandlePosition = range > 0 ? ((timeRange[1] - minTime) / range) * 100 : 0;
	$: rangeWidth = range > 0 ? ((timeRange[1] - timeRange[0]) / range) * 100 : 0;
	$: isSliderDisabled = range <= 0 || (minTime === maxTime && minTime === 0);

	// Debug logging (disabled to reduce noise)
	// $: console.log('TimeControls reactive update:', {
	//	timeRange, minTime, maxTime, range, minHandlePosition, maxHandlePosition, rangeWidth
	// });

	function startDrag(e: MouseEvent | TouchEvent, handle: 'min' | 'max') {
		e.preventDefault();
		isDragging = true;
		dragHandle = handle;

		// console.log('Starting drag:', { handle, timeRange, minTime, maxTime });

		// Add global event listeners
		if (typeof window !== 'undefined') {
			document.addEventListener('mousemove', handleDrag);
			document.addEventListener('mouseup', stopDrag);
			document.addEventListener('touchmove', handleDrag, { passive: false });
			document.addEventListener('touchend', stopDrag);
		}
	}

	function handleDrag(e: MouseEvent | TouchEvent) {
		if (!isDragging || !dragHandle || isSliderDisabled) return;

		e.preventDefault();

		// Get the slider wrapper element
		const sliderWrapper = document.querySelector('.time-slider-wrapper');
		if (!sliderWrapper) return;

		const rect = sliderWrapper.getBoundingClientRect();
		const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
		const percent = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));

		// Prevent division by zero or invalid calculations
		const range = maxTime - minTime;
		if (range === 0) return;

		const newValue = minTime + (percent / 100) * range;

		if (dragHandle === 'min') {
			timeRange[0] = Math.min(newValue, timeRange[1]);
		} else {
			timeRange[1] = Math.max(newValue, timeRange[0]);
		}

		// Trigger reactivity
		timeRange = [...timeRange];

		// console.log('Drag update:', { dragHandle, newValue, timeRange });

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
		<label for="pointing-status-select" class="block text-sm font-medium text-gray-700 mb-2">
			Pointing Status:
		</label>
		<select
			id="pointing-status-select"
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
		<div class="block text-sm font-medium text-gray-700 mb-2">
			Date range (days since Time of Signal): {timeRange[0]?.toFixed(1) || '0.0'} - {timeRange[1]?.toFixed(
				1
			) || '0.0'}
		</div>

		{#if isSliderDisabled}
			<div class="text-sm text-gray-500 italic mb-2">
				Time slider is disabled (no time range available)
			</div>
		{/if}

		<!-- Time Range Slider -->
		<div class="time-slider-container mt-4" class:disabled={isSliderDisabled}>
			<div class="time-slider-wrapper">
				<div class="time-slider-track" class:disabled={isSliderDisabled}></div>
				<div
					class="time-slider-range"
					class:disabled={isSliderDisabled}
					style="left: {minHandlePosition}%; width: {rangeWidth}%"
				></div>

				<!-- Min handle -->
				<div
					class="time-slider-handle min-handle"
					class:dragging={isDragging && dragHandle === 'min'}
					class:disabled={isSliderDisabled}
					style="left: {minHandlePosition}%"
					on:mousedown={(e) => (isSliderDisabled ? null : startDrag(e, 'min'))}
					on:touchstart={(e) => (isSliderDisabled ? null : startDrag(e, 'min'))}
					title={isSliderDisabled
						? 'Time slider disabled'
						: `Minimum time: ${timeRange[0]?.toFixed(1) || '0.0'} days`}
					role="slider"
					tabindex={isSliderDisabled ? -1 : 0}
					aria-label="Minimum time range"
					aria-valuemin={minTime}
					aria-valuemax={maxTime}
					aria-valuenow={timeRange[0]}
					aria-disabled={isSliderDisabled}
				></div>

				<!-- Max handle -->
				<div
					class="time-slider-handle max-handle"
					class:dragging={isDragging && dragHandle === 'max'}
					class:disabled={isSliderDisabled}
					style="left: {maxHandlePosition}%"
					on:mousedown={(e) => (isSliderDisabled ? null : startDrag(e, 'max'))}
					on:touchstart={(e) => (isSliderDisabled ? null : startDrag(e, 'max'))}
					title={isSliderDisabled
						? 'Time slider disabled'
						: `Maximum time: ${timeRange[1]?.toFixed(1) || '0.0'} days`}
					role="slider"
					tabindex={isSliderDisabled ? -1 : 0}
					aria-label="Maximum time range"
					aria-valuemin={minTime}
					aria-valuemax={maxTime}
					aria-valuenow={timeRange[1]}
					aria-disabled={isSliderDisabled}
				></div>
			</div>

			<!-- Time labels -->
			<div class="time-labels mt-2">
				<span class="text-xs text-gray-500">{minTime?.toFixed(1) || '0.0'} days</span>
				<span class="text-xs text-gray-500 float-right">{maxTime?.toFixed(1) || '0.0'} days</span>
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

	/* Disabled slider styles */
	.time-slider-container.disabled {
		opacity: 0.5;
		pointer-events: none;
	}

	.time-slider-track.disabled {
		background-color: #f3f4f6; /* gray-100 */
	}

	.time-slider-range.disabled {
		background-color: #d1d5db; /* gray-300 */
	}

	.time-slider-handle.disabled {
		background-color: #d1d5db; /* gray-300 */
		cursor: not-allowed;
		transform: translate(-50%, -50%);
	}

	.time-slider-handle.disabled:hover {
		transform: translate(-50%, -50%);
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
