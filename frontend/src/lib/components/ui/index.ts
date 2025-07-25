/**
 * @fileoverview UI Components Index
 * @description Centralized exports for all reusable UI components
 * @category UI Components
 * @version 1.0.0
 * @author GWTM Team
 * @since 2024-01-25
 */

// Core UI Components
export { default as Button } from './Button.svelte';
export { default as Card } from './Card.svelte';

// Form Components
export { default as Form } from '../forms/Form.svelte';
export { default as FormField } from '../forms/FormField.svelte';

// New UI Primitives
export { default as LoadingState } from './LoadingState.svelte';
export { default as StatusBadge } from './StatusBadge.svelte';
export { default as AlertBanner } from './AlertBanner.svelte';
export { default as Table } from './Table.svelte';
export { default as ControlGroup } from './ControlGroup.svelte';
export { default as ToggleGroup } from './ToggleGroup.svelte';
export { default as TabNavigation } from './TabNavigation.svelte';

// Error Boundaries
export { default as ErrorBoundary } from './ErrorBoundary.svelte';
export { default as AsyncErrorBoundary } from './AsyncErrorBoundary.svelte';
export { default as ErrorToast } from './ErrorToast.svelte';

// Layout Components (if they exist)
// export { default as Container } from './Container.svelte';
// export { default as Grid } from './Grid.svelte';

/**
 * Type definitions for component props
 */
export interface ButtonProps {
	variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
	size?: 'small' | 'medium' | 'large';
	disabled?: boolean;
	loading?: boolean;
	type?: 'button' | 'submit' | 'reset';
}

export interface StatusBadgeProps {
	variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral';
	size?: 'small' | 'medium' | 'large';
	label?: string;
	pulse?: boolean;
	icon?: string;
}

export interface LoadingStateProps {
	message?: string;
	size?: 'small' | 'medium' | 'large';
	showSpinner?: boolean;
	inline?: boolean;
}

export interface AlertBannerProps {
	variant?: 'info' | 'warning' | 'error' | 'success';
	title?: string;
	dismissible?: boolean;
	icon?: string;
}

export interface TableColumn {
	key: string;
	label: string;
	sortable?: boolean;
	width?: string;
}

export interface TableProps {
	data?: Array<Record<string, any>>;
	columns?: TableColumn[];
	sortable?: boolean;
	paginated?: boolean;
	pageSize?: number;
	loading?: boolean;
	emptyMessage?: string;
}

export interface ControlGroupProps {
	label?: string;
	required?: boolean;
	inline?: boolean;
	helpText?: string;
	error?: string;
}

export interface ToggleGroupProps {
	label?: string;
	expanded?: boolean;
	variant?: 'primary' | 'secondary' | 'outline';
	size?: 'small' | 'medium' | 'large';
	disabled?: boolean;
}
