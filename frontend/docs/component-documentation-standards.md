# Component Documentation Standards

This document outlines the standards for documenting Svelte components in the GWTM frontend codebase.

## Overview

All components should be documented using JSDoc-style comments with specific conventions for Svelte. This ensures consistency, maintainability, and good developer experience.

## Documentation Structure

### 1. Component Header Documentation

Every component must start with a comprehensive JSDoc comment block:

````svelte
<script lang="ts">
	/**
	 * @component ComponentName
	 * @description Brief description of what the component does and its purpose
	 * @category UI|Layout|Visualization|Forms|etc.
	 * @version 1.0.0
	 * @author Your Name
	 * @since 2024-01-01
	 *
	 * @example
	 * ```svelte
	 * <ComponentName
	 *   prop1="value"
	 *   prop2={variable}
	 *   on:event={handler}
	 * >
	 *   Content goes here
	 * </ComponentName>
	 * ```
	 */

	// Component implementation...
</script>
````

### 2. Props Documentation

Each exported prop must be documented:

```typescript
/**
 * The visual style variant of the component
 * @type {'primary' | 'secondary' | 'danger' | 'success'}
 * @default 'primary'
 */
export let variant: 'primary' | 'secondary' | 'danger' | 'success' = 'primary';

/**
 * Whether the component is disabled
 * @type {boolean}
 * @default false
 */
export let disabled: boolean = false;

/**
 * Custom CSS classes to apply to the component
 * @type {string}
 * @default ''
 * @optional
 */
export let className: string = '';
```

### 3. Events Documentation

Document all dispatched events:

```typescript
/**
 * @event click - Fired when the component is clicked
 * @event {CustomEvent<{value: string}>} change - Fired when value changes
 * @event {CustomEvent<{error: Error}>} error - Fired when an error occurs
 */
import { createEventDispatcher } from 'svelte';

const dispatch = createEventDispatcher<{
	click: never;
	change: { value: string };
	error: { error: Error };
}>();
```

### 4. Slots Documentation

Document all available slots:

```svelte
<!--
@slot default - Main content area
@slot header - Header content (optional)
@slot footer - Footer content (optional)
@slot {string} title - Title text for accessibility
@slot {boolean} loading - Whether content is loading
-->
<div class="component">
	<header>
		<slot name="header" {title} {loading} />
	</header>

	<main>
		<slot {loading} />
	</main>

	<footer>
		<slot name="footer" />
	</footer>
</div>
```

## Documentation Tags Reference

### Required Tags

- `@component` - Component name
- `@description` - What the component does
- `@category` - Component category for organization

### Recommended Tags

- `@example` - Usage examples
- `@version` - Component version
- `@author` - Component author
- `@since` - Date created
- `@see` - Related components or documentation

### Prop Tags

- `@type` - TypeScript type definition
- `@default` - Default value
- `@optional` - Mark optional props
- `@deprecated` - Mark deprecated props

### Event Tags

- `@event` - Event name and description
- Include payload type information

### Slot Tags

- `@slot` - Slot name and description
- Include slot props information

## Categories

Organize components into these categories:

- **UI** - Basic UI elements (Button, Card, Modal, etc.)
- **Layout** - Layout components (Navigation, Sidebar, Grid, etc.)
- **Forms** - Form-related components (Input, Select, Checkbox, etc.)
- **Visualization** - Data visualization components
- **Tables** - Table and data display components
- **Feedback** - Error handling, loading, toast components
- **Navigation** - Navigation and routing components
- **Utility** - Utility and helper components

## Accessibility Documentation

Include accessibility information:

```typescript
/**
 * @accessibility
 * - Uses semantic HTML elements
 * - Supports keyboard navigation
 * - Includes ARIA labels and roles
 * - Tested with screen readers
 * - Maintains focus management
 */
```

## Performance Notes

Document performance considerations:

```typescript
/**
 * @performance
 * - Uses Svelte's built-in reactivity
 * - Minimal DOM updates through keyed blocks
 * - Lazy loading for heavy content
 * - Debounced input handling
 */
```

## Testing Information

Include testing notes:

```typescript
/**
 * @testing
 * - Unit tests: ComponentName.test.ts
 * - Integration tests: ComponentName.integration.test.ts
 * - Visual regression tests included
 * - Accessibility tests with jest-axe
 */
```

## Complete Example

````svelte
<script lang="ts">
	/**
	 * @component Button
	 * @description A versatile button component with multiple variants and states
	 * @category UI
	 * @version 1.2.0
	 * @author GWTM Team
	 * @since 2024-01-15
	 *
	 * @accessibility
	 * - Fully keyboard accessible
	 * - Screen reader compatible
	 * - Focus management included
	 * - ARIA attributes for states
	 *
	 * @performance
	 * - Minimal CSS-in-JS overhead
	 * - Efficient event handling
	 * - No unnecessary re-renders
	 *
	 * @example
	 * ```svelte
	 * <!-- Basic usage -->
	 * <Button variant="primary" on:click={handleClick}>
	 *   Click me
	 * </Button>
	 *
	 * <!-- With loading state -->
	 * <Button loading={isLoading} disabled={isLoading}>
	 *   {isLoading ? 'Processing...' : 'Submit'}
	 * </Button>
	 *
	 * <!-- As link -->
	 * <Button href="/dashboard" variant="secondary">
	 *   Go to Dashboard
	 * </Button>
	 * ```
	 *
	 * @see Card - For container-style buttons
	 * @see Link - For text-only links
	 */

	import { createEventDispatcher } from 'svelte';

	/**
	 * @event click - Fired when button is clicked (not when disabled or loading)
	 * @event {CustomEvent<{timestamp: number}>} interact - Fired on any interaction
	 */
	const dispatch = createEventDispatcher<{
		click: never;
		interact: { timestamp: number };
	}>();

	/**
	 * Visual style variant
	 * @type {'primary' | 'secondary' | 'ghost' | 'outline' | 'danger'}
	 * @default 'primary'
	 */
	export let variant: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' = 'primary';

	/**
	 * Button size
	 * @type {'sm' | 'md' | 'lg'}
	 * @default 'md'
	 */
	export let size: 'sm' | 'md' | 'lg' = 'md';

	/**
	 * Whether the button is disabled
	 * @type {boolean}
	 * @default false
	 */
	export let disabled: boolean = false;

	/**
	 * Whether the button is in a loading state
	 * @type {boolean}
	 * @default false
	 */
	export let loading: boolean = false;

	/**
	 * Whether the button should take full width
	 * @type {boolean}
	 * @default false
	 */
	export let fullWidth: boolean = false;

	/**
	 * HTML button type attribute
	 * @type {'button' | 'submit' | 'reset'}
	 * @default 'button'
	 */
	export let type: 'button' | 'submit' | 'reset' = 'button';

	/**
	 * When provided, renders as a link instead of button
	 * @type {string}
	 * @optional
	 */
	export let href: string | undefined = undefined;

	// Implementation continues...
</script>

<!--
@slot default - Button content (text, icons, etc.)
@slot {boolean} loading - Current loading state
@slot {boolean} disabled - Current disabled state
-->
{#if href && !disabled && !loading}
	<a {href} class={buttonClass} on:click>
		<slot {loading} {disabled} />
	</a>
{:else}
	<button {type} {disabled} class={buttonClass} on:click>
		<slot {loading} {disabled} />
	</button>
{/if}
````

## Documentation Tools

### VS Code Extensions

- **Svelte for VS Code** - Syntax highlighting and IntelliSense
- **TypeScript Importer** - Auto-import support
- **JSDoc Comments** - JSDoc snippet support

### Automated Documentation

- Use tools like `@storybook/svelte` for component documentation
- Generate API documentation from JSDoc comments
- Include component documentation in build process

## Best Practices

1. **Keep descriptions concise but complete**
2. **Always include at least one example**
3. **Document edge cases and error states**
4. **Update documentation when changing component APIs**
5. **Use consistent terminology across components**
6. **Include accessibility and performance notes for complex components**
7. **Reference related components when relevant**
8. **Document breaking changes in version history**

## Enforcement

- Use ESLint rules to enforce JSDoc presence
- Include documentation checks in PR reviews
- Generate documentation coverage reports
- Integrate with CI/CD pipeline for validation
