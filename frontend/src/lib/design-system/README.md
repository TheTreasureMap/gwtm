# GWTM Design System

This design system provides consistent styling utilities and components for the Gravitational Wave Treasure Map frontend application.

## Overview

The design system is built on top of Tailwind CSS and provides:

- Consistent color palette and spacing
- Reusable component classes
- Utility functions for building component styles
- Type-safe styling utilities

## Color System

### Primary Colors

- **Primary Blue**: Used for primary actions, links, and brand elements
  - `primary-50` to `primary-900`
  - Main brand color: `primary-600` (#2563eb)

### Semantic Colors

- **Success Green**: `success-50`, `success-100`, `success-500`, `success-600`, `success-700`
- **Warning Yellow**: `warning-50`, `warning-100`, `warning-500`, `warning-600`, `warning-700`
- **Error Red**: `error-50`, `error-100`, `error-500`, `error-600`, `error-700`

## Component Classes

### Buttons

```css
.btn-base          /* Base button styles */
.btn-primary       /* Primary button variant */
.btn-secondary     /* Secondary button variant */
.btn-ghost         /* Ghost button variant */
.btn-outline       /* Outline button variant */
.btn-danger        /* Danger button variant */

.btn-sm            /* Small button size */
.btn-md            /* Medium button size */
.btn-lg            /* Large button size */
```

### Cards

```css
.card-base         /* Base card styles */
.card-hover        /* Hover effect for cards */
.card-padding-sm   /* Small padding */
.card-padding-md   /* Medium padding */
.card-padding-lg   /* Large padding */
```

### Forms

```css
.form-input        /* Base input styles */
.form-input-error  /* Error state for inputs */
.form-label        /* Base label styles */
.form-label-error  /* Error state for labels */
```

### Navigation

```css
.nav-link          /* Navigation link styles */
.nav-dropdown      /* Dropdown menu container */
.nav-dropdown-item /* Dropdown menu items */
```

### Status Badges

```css
.status-success    /* Success status styling */
.status-warning    /* Warning status styling */
.status-error      /* Error status styling */
.status-info       /* Info status styling */
.status-neutral    /* Neutral status styling */
```

### Containers

```css
.container-responsive  /* Responsive container (max-w-7xl) */
.container-sm         /* Small container (max-w-md) */
.container-md         /* Medium container (max-w-2xl) */
.container-lg         /* Large container (max-w-4xl) */
```

## Utility Functions

### classBuilder

The `classBuilder` object provides functions to generate consistent class strings:

```typescript
import { classBuilder } from '$lib/design-system';

// Button classes
const buttonClass = classBuilder.button('primary', 'md', true); // fullWidth = true

// Card classes
const cardClass = classBuilder.card('md', true, true); // padding, hover, shadow

// Form input classes
const inputClass = classBuilder.formInput(false, false); // hasError, disabled

// Status badge classes
const badgeClass = classBuilder.statusBadge('success', 'md');

// Container classes
const containerClass = classBuilder.container('responsive', 'md');
```

## Usage Examples

### Button Component

```svelte
<script>
	import { classBuilder } from '$lib/design-system';

	export let variant = 'primary';
	export let size = 'md';
	export let fullWidth = false;

	$: buttonClass = classBuilder.button(variant, size, fullWidth);
</script>

<button class={buttonClass}>
	<slot />
</button>
```

### Card Component

```svelte
<script>
	import { classBuilder } from '$lib/design-system';

	export let padding = 'md';
	export let hover = false;
	export let shadow = true;

	$: cardClass = classBuilder.card(padding, hover, shadow);
</script>

<div class={cardClass}>
	<slot />
</div>
```

## Spacing System

### Common Spacing Utilities

```typescript
import { spacing } from '$lib/design-system';

// Apply to containers
<div class={spacing.section}>     <!-- space-y-8 -->
<form class={spacing.form}>       <!-- space-y-6 -->
<div class={spacing.formField}>   <!-- space-y-2 -->
<div class={spacing.buttonGroup}> <!-- space-x-4 -->
<div class={spacing.cardGrid}>    <!-- grid gap-6 md:grid-cols-2 lg:grid-cols-3 -->
```

## Animation Utilities

```typescript
import { animations } from '$lib/design-system';

// Apply animations
<div class={animations.fadeIn}>
<div class={animations.slideIn}>
<div class={animations.spin}>
```

## Migration Guide

When updating existing components:

1. Import the design system utilities
2. Replace hardcoded Tailwind classes with design system classes
3. Use `classBuilder` functions for dynamic styling
4. Update color references to use the new color tokens

### Before

```svelte
<button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"> Click me </button>
```

### After

```svelte
<script>
	import { classBuilder } from '$lib/design-system';
</script>

<button class={classBuilder.button('primary', 'md')}> Click me </button>
```

## Benefits

- **Consistency**: All components use the same color palette and spacing
- **Maintainability**: Changes to the design system propagate to all components
- **Type Safety**: TypeScript ensures correct usage of variants and sizes
- **Performance**: Reduced CSS bundle size through shared classes
- **Developer Experience**: Easier to build new components with consistent styling
