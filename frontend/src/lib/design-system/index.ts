/**
 * Design System Utilities
 * Centralized styling utilities and constants for consistent UI
 */

// Color variants for components
export const colorVariants = {
	primary: 'primary',
	secondary: 'secondary',
	success: 'success',
	warning: 'warning',
	error: 'error',
	info: 'info',
	neutral: 'neutral'
} as const;

export type ColorVariant = keyof typeof colorVariants;

// Size variants for components
export const sizeVariants = {
	sm: 'sm',
	md: 'md',
	lg: 'lg',
	xl: 'xl'
} as const;

export type SizeVariant = keyof typeof sizeVariants;

// Card-specific padding type that includes 'none'
export type CardPaddingVariant = SizeVariant | 'none';

// Button variants
export const buttonVariants = {
	primary: 'primary',
	secondary: 'secondary',
	ghost: 'ghost',
	outline: 'outline',
	danger: 'danger'
} as const;

export type ButtonVariant = keyof typeof buttonVariants;

// Common class builders
export const classBuilder = {
	/**
	 * Build button classes based on variant and size
	 */
	button: (variant: ButtonVariant = 'primary', size: SizeVariant = 'md', fullWidth = false) => {
		const classes = ['btn-base', `btn-${variant}`, `btn-${size}`, fullWidth ? 'w-full' : ''];
		return classes.filter(Boolean).join(' ');
	},

	/**
	 * Build card classes based on padding, shadow, and hover
	 */
	card: (padding: CardPaddingVariant = 'md', hover = false, shadow = true) => {
		const classes = [
			'card-base',
			padding !== 'none' ? `card-padding-${padding}` : '',
			hover ? 'card-hover' : '',
			!shadow ? 'shadow-none' : ''
		];
		return classes.filter(Boolean).join(' ');
	},

	/**
	 * Build form input classes based on error state
	 */
	formInput: (hasError = false, disabled = false) => {
		const classes = [
			'form-input',
			hasError ? 'form-input-error' : '',
			disabled ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : 'bg-white'
		];
		return classes.filter(Boolean).join(' ');
	},

	/**
	 * Build form label classes based on error state
	 */
	formLabel: (hasError = false, required = false) => {
		const classes = [
			'form-label',
			hasError ? 'form-label-error' : '',
			required ? "after:content-['*'] after:ml-0.5 after:text-error-500" : ''
		];
		return classes.filter(Boolean).join(' ');
	},

	/**
	 * Build status badge classes
	 */
	statusBadge: (variant: ColorVariant = 'neutral', size: SizeVariant = 'md') => {
		const sizeClasses = {
			sm: 'px-2 py-0.5 text-xs',
			md: 'px-2.5 py-1 text-sm',
			lg: 'px-3 py-1.5 text-base',
			xl: 'px-4 py-2 text-lg'
		};

		const classes = [
			'inline-flex items-center gap-1.5 font-medium rounded-full border',
			`status-${variant}`,
			sizeClasses[size]
		];
		return classes.filter(Boolean).join(' ');
	},

	/**
	 * Build container classes
	 */
	container: (
		size: 'sm' | 'md' | 'lg' | 'responsive' = 'responsive',
		padding: SizeVariant = 'md'
	) => {
		const paddingClasses = {
			sm: 'px-4 py-4',
			md: 'px-4 py-8',
			lg: 'px-6 py-12',
			xl: 'px-8 py-16'
		};

		const classes = [`container-${size}`, paddingClasses[padding]];
		return classes.filter(Boolean).join(' ');
	}
};

// Animation utilities
export const animations = {
	fadeIn: 'animate-in fade-in duration-200',
	fadeOut: 'animate-out fade-out duration-200',
	slideIn: 'animate-in slide-in-from-top-2 duration-200',
	slideOut: 'animate-out slide-out-to-top-2 duration-200',
	spin: 'animate-spin'
};

// Common spacing utilities
export const spacing = {
	section: 'space-y-8',
	form: 'space-y-6',
	formField: 'space-y-2',
	buttonGroup: 'space-x-4',
	cardGrid: 'grid gap-6 md:grid-cols-2 lg:grid-cols-3'
};

// Responsive breakpoint utilities
export const breakpoints = {
	sm: '640px',
	md: '768px',
	lg: '1024px',
	xl: '1280px',
	'2xl': '1536px'
};
