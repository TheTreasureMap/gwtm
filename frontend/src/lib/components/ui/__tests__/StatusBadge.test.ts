import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import StatusBadge from '../StatusBadge.svelte';

describe('StatusBadge', () => {
	it('renders the label', () => {
		render(StatusBadge, { label: 'Completed' });
		expect(screen.getByRole('status')).toHaveTextContent('Completed');
	});

	it('applies the variant class', () => {
		render(StatusBadge, { label: 'Failed', variant: 'error' });
		expect(screen.getByRole('status')).toHaveClass('badge', 'badge-error');
	});

	it('defaults to the neutral variant', () => {
		render(StatusBadge, { label: 'Unknown' });
		expect(screen.getByRole('status')).toHaveClass('badge-neutral');
	});

	it('applies the size modifier only when not medium', () => {
		const { unmount } = render(StatusBadge, { label: 'Small', size: 'small' });
		expect(screen.getByRole('status')).toHaveClass('badge-sm');
		unmount();

		render(StatusBadge, { label: 'Medium', size: 'medium' });
		const badge = screen.getByRole('status');
		expect(badge.className).not.toMatch(/badge-(sm|lg)/);
	});

	it('adds the pulse animation when asked', () => {
		render(StatusBadge, { label: 'Live', pulse: true });
		expect(screen.getByRole('status')).toHaveClass('animate-pulse');
	});

	it('merges a caller-supplied class', () => {
		render(StatusBadge, { label: 'Tagged', class: 'custom-class' });
		expect(screen.getByRole('status')).toHaveClass('custom-class');
	});

	it('renders the symbol for a known icon name', () => {
		render(StatusBadge, { label: 'Done', icon: 'check' });
		expect(screen.getByRole('status')).toHaveTextContent('✓');
	});

	it('renders no icon element for an unknown icon name', () => {
		render(StatusBadge, { label: 'Plain' });
		expect(screen.getByRole('status').querySelector('[aria-hidden="true"]')).toBeNull();
	});
});
