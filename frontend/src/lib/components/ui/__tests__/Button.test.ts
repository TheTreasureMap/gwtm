import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import Button from '../Button.svelte';

describe('Button', () => {
	describe('element choice', () => {
		it('renders a button by default', () => {
			render(Button);
			expect(screen.getByRole('button')).toBeInstanceOf(HTMLButtonElement);
		});

		it('renders an anchor when given an href', () => {
			render(Button, { href: '/alerts' });
			const el = screen.getByRole('button');
			expect(el).toBeInstanceOf(HTMLAnchorElement);
			expect(el).toHaveAttribute('href', '/alerts');
		});

		it('falls back to a button when an href is given but disabled', () => {
			render(Button, { href: '/alerts', disabled: true });
			expect(screen.getByRole('button')).toBeInstanceOf(HTMLButtonElement);
		});
	});

	describe('styling', () => {
		it('applies the variant class', () => {
			render(Button, { variant: 'danger' });
			expect(screen.getByRole('button')).toHaveClass('btn', 'btn-error');
		});

		it('defaults to the primary variant', () => {
			render(Button);
			expect(screen.getByRole('button')).toHaveClass('btn-primary');
		});

		it('applies a size modifier only when not medium', () => {
			const { unmount } = render(Button, { size: 'lg' });
			expect(screen.getByRole('button')).toHaveClass('btn-lg');
			unmount();

			render(Button, { size: 'md' });
			expect(screen.getByRole('button').className).not.toMatch(/btn-(sm|lg)/);
		});

		it('stretches to full width when asked', () => {
			render(Button, { fullWidth: true });
			expect(screen.getByRole('button')).toHaveClass('w-full');
		});

		it('dims the button when disabled or loading', () => {
			const { unmount } = render(Button, { disabled: true });
			expect(screen.getByRole('button')).toHaveClass('opacity-50', 'cursor-not-allowed');
			unmount();

			render(Button, { loading: true });
			expect(screen.getByRole('button')).toHaveClass('opacity-50', 'pointer-events-none');
		});
	});

	describe('state', () => {
		it('marks the native disabled attribute', () => {
			render(Button, { disabled: true });
			expect(screen.getByRole('button')).toBeDisabled();
		});

		it('exposes the loading state to assistive technology', () => {
			render(Button, { loading: true });
			expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
		});

		it('shows a spinner while loading', () => {
			render(Button, { loading: true });
			expect(screen.getByRole('button').querySelector('.animate-spin')).not.toBeNull();
		});

		it('shows no spinner when idle', () => {
			render(Button);
			expect(screen.getByRole('button').querySelector('.animate-spin')).toBeNull();
		});

		it('honours the requested type', () => {
			render(Button, { type: 'submit' });
			expect(screen.getByRole('button')).toHaveAttribute('type', 'submit');
		});
	});

	describe('interaction', () => {
		// Svelte 5 removed component.$on, so forwarded events are wired through
		// mount's `events` option, which render() passes straight through.
		it('forwards clicks', async () => {
			const onClick = vi.fn();
			render(Button, { events: { click: onClick } });

			await userEvent.click(screen.getByRole('button'));

			expect(onClick).toHaveBeenCalledTimes(1);
		});

		it('does not fire when disabled', async () => {
			const onClick = vi.fn();
			render(Button, { props: { disabled: true }, events: { click: onClick } });

			await userEvent.click(screen.getByRole('button'));

			expect(onClick).not.toHaveBeenCalled();
		});
	});
});
