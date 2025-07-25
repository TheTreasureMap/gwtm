# Component Usage Patterns

This guide provides comprehensive examples and patterns for using GWTM frontend components effectively.

## Basic UI Components

### Button Component

The Button component is the primary interactive element for user actions.

#### Basic Usage

```svelte
<script>
	import Button from '$lib/components/ui/Button.svelte';

	function handleClick() {
		console.log('Button clicked!');
	}
</script>

<Button on:click={handleClick}>Click me</Button>
```

#### All Variants

```svelte
<!-- Primary (default) -->
<Button variant="primary">Primary Action</Button>

<!-- Secondary -->
<Button variant="secondary">Secondary Action</Button>

<!-- Ghost (transparent background) -->
<Button variant="ghost">Ghost Action</Button>

<!-- Outline -->
<Button variant="outline">Outline Action</Button>

<!-- Danger -->
<Button variant="danger">Delete Item</Button>
```

#### Sizes

```svelte
<Button size="sm">Small</Button>
<Button size="md">Medium (default)</Button>
<Button size="lg">Large</Button>
```

#### States

```svelte
<script>
	let loading = false;

	async function handleSubmit() {
		loading = true;
		try {
			await submitData();
		} finally {
			loading = false;
		}
	}
</script>

<!-- Loading state -->
<Button {loading} on:click={handleSubmit}>
	{loading ? 'Submitting...' : 'Submit'}
</Button>

<!-- Disabled state -->
<Button disabled>Disabled Button</Button>

<!-- Full width -->
<Button fullWidth>Full Width Button</Button>
```

#### As Link

```svelte
<!-- Renders as <a> tag -->
<Button href="/dashboard" variant="secondary">Go to Dashboard</Button>
```

#### Form Integration

```svelte
<form on:submit|preventDefault={handleSubmit}>
	<input bind:value={formData.name} required />

	<div class="flex gap-2 mt-4">
		<Button type="submit" loading={submitting}>Save Changes</Button>
		<Button variant="secondary" on:click={cancel}>Cancel</Button>
	</div>
</form>
```

### Card Component

The Card component provides consistent container styling for grouping content.

#### Basic Usage

```svelte
<script>
	import Card from '$lib/components/ui/Card.svelte';
</script>

<Card>
	<h3 class="text-lg font-semibold mb-2">Card Title</h3>
	<p>This is the card content.</p>
</Card>
```

#### Interactive Cards

```svelte
<script>
	function handleCardClick() {
		// Navigate or perform action
		goto('/details');
	}
</script>

<Card clickable hover on:click={handleCardClick}>
	<div class="cursor-pointer">
		<h3>Clickable Card</h3>
		<p>Click me to navigate</p>
	</div>
</Card>
```

#### Image Cards

```svelte
<Card padding="none">
	<img src="/image.jpg" alt="Description" class="w-full h-48 object-cover rounded-t-lg" />
	<div class="p-6">
		<h3 class="text-lg font-semibold">Image Card</h3>
		<p>Content with full-width image</p>
	</div>
</Card>
```

#### Card Layouts

```svelte
<!-- Grid of cards -->
<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
	{#each items as item}
		<Card>
			<h3>{item.title}</h3>
			<p>{item.description}</p>
		</Card>
	{/each}
</div>

<!-- Horizontal card layout -->
<Card padding="none" class="flex">
	<img src={item.image} alt="" class="w-24 h-24 object-cover rounded-l-lg" />
	<div class="p-4 flex-1">
		<h3>{item.title}</h3>
		<p>{item.description}</p>
	</div>
</Card>
```

### ErrorMessage Component

For displaying error, warning, and informational messages.

#### Basic Error

```svelte
<script>
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';

	let error = '';

	async function loadData() {
		try {
			const data = await api.getData();
		} catch (err) {
			error = err.message;
		}
	}
</script>

{#if error}
	<ErrorMessage message={error} />
{/if}
```

#### Different Message Types

```svelte
<!-- Error (default) -->
<ErrorMessage message="Something went wrong!" />

<!-- Warning -->
<ErrorMessage type="warning" title="Warning" message="This action cannot be undone" />

<!-- Info -->
<ErrorMessage type="info" title="Information" message="Your data has been saved successfully" />
```

#### Dismissible Messages

```svelte
<script>
	let showMessage = true;

	function dismissMessage() {
		showMessage = false;
	}
</script>

{#if showMessage}
	<ErrorMessage
		type="info"
		message="This is a dismissible message"
		dismissible
		onDismiss={dismissMessage}
	/>
{/if}
```

## Advanced UI Components

### AsyncErrorBoundary Component

For handling async operations with loading states and error handling.

#### Basic Async Loading

```svelte
<script>
	import AsyncErrorBoundary from '$lib/components/ui/AsyncErrorBoundary.svelte';
	import { gwtmApi } from '$lib/api';

	let data = [];

	async function loadData() {
		data = await gwtmApi.getInstruments();
	}
</script>

<AsyncErrorBoundary
	asyncFunction={loadData}
	loadingText="Loading instruments..."
	errorFallback="Failed to load instruments. Please try again."
>
	{#each data as item}
		<div>{item.name}</div>
	{/each}
</AsyncErrorBoundary>
```

#### Manual Loading Control

```svelte
<AsyncErrorBoundary asyncFunction={loadExpensiveData} autoLoad={false} let:executeAsync>
	<Button on:click={executeAsync}>Load Data</Button>

	{#if data.length > 0}
		<!-- Display data -->
	{/if}
</AsyncErrorBoundary>
```

### ErrorBoundary Component

For wrapping components that might throw errors.

#### Component Error Handling

```svelte
<script>
	import ErrorBoundary from '$lib/components/ui/ErrorBoundary.svelte';
	import ComplexVisualization from './ComplexVisualization.svelte';
</script>

<ErrorBoundary fallback="Visualization failed to load" let:captureError>
	<ComplexVisualization data={complexData} on:error={(e) => captureError(e.detail.error)} />
</ErrorBoundary>
```

## Layout Components

### Navigation Component

The main navigation component handles authentication state and provides consistent navigation.

#### Usage in Layout

```svelte
<!-- +layout.svelte -->
<script>
	import Navigation from '$lib/components/layout/Navigation.svelte';
	import ErrorToast from '$lib/components/ui/ErrorToast.svelte';
</script>

<Navigation />
<main class="min-h-screen">
	<slot />
</main>
<ErrorToast />
```

### Container Components

#### PageContainer

```svelte
<script>
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
</script>

<PageContainer>
	<PageHeader title="Page Title" description="Page description" />

	<!-- Page content -->
</PageContainer>
```

## Form Patterns

### Form with Error Handling

```svelte
<script>
	import Button from '$lib/components/ui/Button.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';
	import { validation, validateForm } from '$lib/utils/errorHandling';

	let formData = {
		name: '',
		email: ''
	};
	let errors = {};
	let loading = false;
	let submitError = '';

	const validationRules = {
		name: [
			(value) => validation.isRequired(value, 'Name'),
			(value) => validation.minLength(value, 2, 'Name')
		],
		email: [(value) => validation.isRequired(value, 'Email'), (value) => validation.isEmail(value)]
	};

	async function handleSubmit() {
		// Validate form
		errors = validateForm(formData, validationRules);
		if (Object.keys(errors).length > 0) return;

		loading = true;
		submitError = '';

		try {
			await api.submitForm(formData);
			// Success handling
		} catch (err) {
			submitError = err.message;
		} finally {
			loading = false;
		}
	}
</script>

<form on:submit|preventDefault={handleSubmit}>
	<div class="space-y-4">
		<div>
			<label for="name">Name</label>
			<input
				id="name"
				bind:value={formData.name}
				class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
				class:border-red-500={errors.name}
			/>
			{#if errors.name}
				<p class="mt-1 text-sm text-red-600">{errors.name}</p>
			{/if}
		</div>

		<div>
			<label for="email">Email</label>
			<input
				id="email"
				type="email"
				bind:value={formData.email}
				class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
				class:border-red-500={errors.email}
			/>
			{#if errors.email}
				<p class="mt-1 text-sm text-red-600">{errors.email}</p>
			{/if}
		</div>
	</div>

	{#if submitError}
		<ErrorMessage message={submitError} />
	{/if}

	<div class="mt-6">
		<Button type="submit" {loading} disabled={loading}>
			{loading ? 'Submitting...' : 'Submit'}
		</Button>
	</div>
</form>
```

## Data Display Patterns

### Loading States

```svelte
<script>
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	let loading = true;
	let data = [];

	onMount(async () => {
		try {
			data = await api.getData();
		} finally {
			loading = false;
		}
	});
</script>

{#if loading}
	<LoadingSpinner text="Loading data..." />
{:else if data.length === 0}
	<div class="text-center py-8 text-gray-500">No data available</div>
{:else}
	{#each data as item}
		<Card>
			<h3>{item.title}</h3>
			<p>{item.description}</p>
		</Card>
	{/each}
{/if}
```

### Table Patterns

```svelte
<script>
	import Card from '$lib/components/ui/Card.svelte';

	export let instruments = [];
	export let loading = false;
</script>

<Card padding="none">
	{#if loading}
		<div class="p-6">
			<LoadingSpinner />
		</div>
	{:else if instruments.length === 0}
		<div class="p-6 text-center text-gray-500">No instruments found</div>
	{:else}
		<div class="overflow-x-auto">
			<table class="min-w-full divide-y divide-gray-200">
				<thead class="bg-gray-50">
					<tr>
						<th
							class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
						>
							Name
						</th>
						<th
							class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
						>
							Type
						</th>
						<th
							class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
						>
							Pointings
						</th>
					</tr>
				</thead>
				<tbody class="bg-white divide-y divide-gray-200">
					{#each instruments as instrument}
						<tr class="hover:bg-gray-50">
							<td class="px-6 py-4 whitespace-nowrap">
								<div class="text-sm font-medium text-gray-900">
									{instrument.instrument_name}
								</div>
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
								{instrument.instrument_type}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
								{instrument.num_pointings || 0}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</Card>
```

## Component Composition Patterns

### Modal with Form

```svelte
<script>
	import Modal from '$lib/components/ui/Modal.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import ErrorMessage from '$lib/components/ui/ErrorMessage.svelte';

	let showModal = false;
	let loading = false;
	let error = '';

	async function handleSave() {
		loading = true;
		error = '';

		try {
			await saveData();
			showModal = false;
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}
</script>

<Button on:click={() => (showModal = true)}>Open Modal</Button>

{#if showModal}
	<Modal on:close={() => (showModal = false)}>
		<div slot="header">
			<h2 class="text-lg font-semibold">Edit Item</h2>
		</div>

		<div slot="body">
			{#if error}
				<ErrorMessage message={error} />
			{/if}

			<!-- Form content -->
		</div>

		<div slot="footer" class="flex justify-end gap-2">
			<Button variant="secondary" on:click={() => (showModal = false)}>Cancel</Button>
			<Button on:click={handleSave} {loading}>Save</Button>
		</div>
	</Modal>
{/if}
```

### Dashboard Layout

```svelte
<script>
	import PageContainer from '$lib/components/ui/PageContainer.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import AsyncErrorBoundary from '$lib/components/ui/AsyncErrorBoundary.svelte';
</script>

<PageContainer>
	<div class="flex justify-between items-center mb-8">
		<PageHeader title="Dashboard" description="Overview of your telescope observations" />
		<Button href="/submit/pointing">New Pointing</Button>
	</div>

	<!-- Stats Grid -->
	<div class="grid md:grid-cols-3 gap-6 mb-8">
		<Card>
			<h3 class="text-sm font-medium text-gray-500">Total Pointings</h3>
			<p class="text-2xl font-bold text-gray-900">{stats.totalPointings}</p>
		</Card>
		<Card>
			<h3 class="text-sm font-medium text-gray-500">Active Instruments</h3>
			<p class="text-2xl font-bold text-gray-900">{stats.activeInstruments}</p>
		</Card>
		<Card>
			<h3 class="text-sm font-medium text-gray-500">Recent Alerts</h3>
			<p class="text-2xl font-bold text-gray-900">{stats.recentAlerts}</p>
		</Card>
	</div>

	<!-- Recent Activity -->
	<Card>
		<h2 class="text-lg font-semibold mb-4">Recent Activity</h2>
		<AsyncErrorBoundary asyncFunction={loadRecentActivity} loadingText="Loading recent activity...">
			<!-- Activity list -->
		</AsyncErrorBoundary>
	</Card>
</PageContainer>
```

## Best Practices

### 1. Consistent Error Handling

Always wrap async operations in error boundaries and provide meaningful error messages.

### 2. Loading States

Show loading indicators for all async operations to provide user feedback.

### 3. Accessibility

Use semantic HTML, ARIA attributes, and ensure keyboard accessibility for all interactive components.

### 4. Responsive Design

Use Tailwind's responsive classes to ensure components work on all screen sizes.

### 5. Component Composition

Favor composition over complex single components. Build complex UIs by combining simple, well-documented components.

### 6. Type Safety

Always use TypeScript types for props and maintain strict type checking throughout the component tree.

### 7. Performance

Use Svelte's reactivity efficiently and avoid unnecessary re-renders with proper dependency tracking.
