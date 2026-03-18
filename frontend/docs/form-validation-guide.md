# Form Validation Guide

This guide provides comprehensive documentation for the GWTM frontend form validation system, including utilities, components, and best practices.

## Overview

The GWTM form validation system provides:

- **Reusable validation functions** with TypeScript support
- **Pre-defined schemas** for common use cases
- **Reactive form components** with built-in validation
- **Form state management** with stores and hooks
- **Accessibility compliance** with ARIA attributes
- **Real-time validation** with debouncing and performance optimization

## Table of Contents

1. [Validation Utilities](#validation-utilities)
2. [Form Components](#form-components)
3. [Form State Management](#form-state-management)
4. [Validation Schemas](#validation-schemas)
5. [Best Practices](#best-practices)
6. [Examples](#examples)
7. [Migration Guide](#migration-guide)

## Validation Utilities

### Core Validators

Located in `src/lib/validation/validators.ts`, these provide the foundation for form validation.

#### Basic Validators

```typescript
import { validators } from '$lib/validation/validators';

// Required field
validators.required('This field is required');

// String length
validators.minLength(3, 'Must be at least 3 characters');
validators.maxLength(100, 'Must be less than 100 characters');

// Email validation
validators.email('Please enter a valid email');

// Number validation
validators.number('Must be a valid number');
validators.min(0, 'Must be positive');
validators.max(100, 'Must be 100 or less');

// Pattern matching
validators.pattern(/^[a-zA-Z0-9_]+$/, 'Only letters, numbers, and underscores allowed');

// URL validation
validators.url('Please enter a valid URL');

// Date validation
validators.date('Please enter a valid date');
validators.minDate(new Date(), 'Date must be in the future');
validators.maxDate(new Date(2030, 0, 1), 'Date must be before 2030');
```

#### Security Validators

```typescript
// Safe string validation (prevents XSS)
validators.safe('Invalid characters detected');

// Custom validation
validators.custom((value, context) => {
	if (value === context.someOtherField) {
		return 'Values cannot be the same';
	}
	return true; // Valid
});
```

#### Password Validation

```typescript
validators.password({
	minLength: 8,
	requireUppercase: true,
	requireLowercase: true,
	requireNumbers: true,
	requireSpecialChars: false
});

// Confirm password (requires context)
validators.confirmPassword('password', 'Passwords do not match');
```

### Validation Schemas

Pre-defined schemas for common forms:

```typescript
import { validationSchemas } from '$lib/validation/validators';

// Authentication forms
validationSchemas.auth.login; // email, password
validationSchemas.auth.register; // email, username, password, confirmPassword, etc.

// Instrument forms
validationSchemas.instrument.create; // instrument_name, nickname, instrument_type

// Pointing forms
validationSchemas.pointing.create; // ra, dec, depth, time
```

### Custom Schema Creation

```typescript
import type { ValidationSchema } from '$lib/validation/validators';

const customSchema: ValidationSchema<{
	title: string;
	description: string;
	priority: number;
}> = {
	title: {
		required: true,
		validators: [
			validators.minLength(3, 'Title must be at least 3 characters'),
			validators.maxLength(100, 'Title must be less than 100 characters'),
			validators.safe()
		]
	},
	description: {
		validators: [
			validators.maxLength(500, 'Description must be less than 500 characters'),
			validators.safe()
		]
	},
	priority: {
		required: true,
		validators: [
			validators.number('Priority must be a number'),
			validators.min(1, 'Priority must be at least 1'),
			validators.max(5, 'Priority must be 5 or less')
		]
	}
};
```

## Form Components

### FormField Component

A comprehensive form field component with built-in validation:

```svelte
<script>
	import FormField from '$lib/components/forms/FormField.svelte';
	import { validators } from '$lib/validation/validators';

	let email = '';
	let password = '';
</script>

<!-- Basic text input -->
<FormField
	name="email"
	label="Email Address"
	type="email"
	required
	bind:value={email}
	validators={[validators.email()]}
	placeholder="Enter your email"
	helpText="We'll never share your email"
/>

<!-- Password with custom validation -->
<FormField
	name="password"
	label="Password"
	type="password"
	required
	bind:value={password}
	validators={[validators.password()]}
	helpText="Must contain uppercase, lowercase, and numbers"
/>

<!-- Select dropdown -->
<FormField
	name="category"
	label="Category"
	type="select"
	required
	bind:value={category}
	options={[
		{ value: '1', label: 'Category 1' },
		{ value: '2', label: 'Category 2' }
	]}
/>

<!-- Textarea -->
<FormField
	name="description"
	label="Description"
	type="textarea"
	bind:value={description}
	rows={4}
	validators={[validators.maxLength(500)]}
/>

<!-- Checkbox -->
<FormField name="agree" label="I agree to the terms" type="checkbox" required bind:value={agree} />

<!-- Radio buttons -->
<FormField
	name="priority"
	label="Priority Level"
	type="radio"
	required
	bind:value={priority}
	options={[
		{ value: 'low', label: 'Low' },
		{ value: 'medium', label: 'Medium' },
		{ value: 'high', label: 'High' }
	]}
/>
```

#### FormField Props

| Prop                | Type                | Default | Description                   |
| ------------------- | ------------------- | ------- | ----------------------------- |
| `name`              | string              | -       | Field name/id (required)      |
| `label`             | string              | -       | Field label (required)        |
| `type`              | string              | 'text'  | Input type                    |
| `value`             | any                 | ''      | Field value                   |
| `required`          | boolean             | false   | Whether field is required     |
| `disabled`          | boolean             | false   | Whether field is disabled     |
| `validators`        | ValidatorFunction[] | []      | Array of validation functions |
| `helpText`          | string              | ''      | Help text below field         |
| `placeholder`       | string              | ''      | Placeholder text              |
| `options`           | Option[]            | []      | Options for select/radio      |
| `validationContext` | any                 | {}      | Context for validation        |

#### FormField Events

- `validate` - Fired when validation state changes
- `change` - Fired when value changes
- `focus` - Fired when field receives focus
- `blur` - Fired when field loses focus

### Form Component

A comprehensive form wrapper with schema validation:

```svelte
<script>
	import Form from '$lib/components/forms/Form.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import { validationSchemas } from '$lib/validation/validators';

	let formData = {
		email: '',
		password: ''
	};

	async function handleSubmit(data) {
		const result = await api.login(data);
		return {
			success: result.success,
			error: result.error
		};
	}
</script>

<Form
	schema={validationSchemas.auth.login}
	bind:data={formData}
	onSubmit={handleSubmit}
	submitText="Sign In"
	let:isValid
	let:isSubmitting
>
	<FormField name="email" label="Email" type="email" required bind:value={formData.email} />

	<FormField
		name="password"
		label="Password"
		type="password"
		required
		bind:value={formData.password}
	/>
</Form>
```

#### Form Props

| Prop                       | Type             | Default  | Description                     |
| -------------------------- | ---------------- | -------- | ------------------------------- |
| `data`                     | object           | {}       | Form data object                |
| `schema`                   | ValidationSchema | -        | Validation schema               |
| `onSubmit`                 | function         | -        | Submit handler                  |
| `submitText`               | string           | 'Submit' | Submit button text              |
| `showSubmitButton`         | boolean          | true     | Whether to show submit button   |
| `preventInvalidSubmission` | boolean          | true     | Prevent invalid form submission |

#### Form Slot Props

- `data` - Current form data
- `isValid` - Whether form is valid
- `isSubmitting` - Whether form is submitting
- `fieldErrors` - Field validation errors
- `validate` - Manual validation function
- `reset` - Form reset function

## Form State Management

### useFormValidation Hook

For component-level form state management:

```svelte
<script>
	import { useFormValidation } from '$lib/hooks/useFormValidation';
	import { validationSchemas } from '$lib/validation/validators';

	const form = useFormValidation({
		schema: validationSchemas.auth.login,
		initialValues: { email: '', password: '' }
	});

	function handleSubmit() {
		if (form.validateAll()) {
			// Submit form
			console.log('Form data:', $form.values);
		}
	}
</script>

<form on:submit|preventDefault={handleSubmit}>
	<input
		type="email"
		bind:value={$form.values.email}
		on:blur={() => form.setFieldTouched('email')}
	/>
	{#if $form.errors.email}
		<p class="error">{$form.errors.email[0]}</p>
	{/if}

	<input
		type="password"
		bind:value={$form.values.password}
		on:blur={() => form.setFieldTouched('password')}
	/>
	{#if $form.errors.password}
		<p class="error">{$form.errors.password[0]}</p>
	{/if}

	<button type="submit" disabled={!$form.isValid}> Submit </button>
</form>
```

### createFormStore

For complex form state management across components:

```svelte
<script>
	import { createFormStore } from '$lib/stores/formStore';
	import { validationSchemas } from '$lib/validation/validators';

	const formStore = createFormStore({
		initialValues: { email: '', password: '' },
		validationSchema: validationSchemas.auth.login,
		submitHandler: async (data) => {
			const result = await api.login(data);
			return { success: result.success, error: result.error };
		}
	});

	async function handleSubmit() {
		const result = await formStore.submit();
		if (result.success) {
			console.log('Login successful');
		}
	}
</script>

<form on:submit|preventDefault={handleSubmit}>
	<!-- Form fields bound to formStore -->
</form>
```

## Best Practices

### 1. Validation Strategy

```typescript
// ✅ Good: Combine multiple validation modes
const fieldConfig = {
	required: true,
	validators: [
		validators.email(),
		validators.custom(async (email) => {
			const exists = await checkEmailExists(email);
			return exists ? 'Email already registered' : true;
		})
	]
};

// ❌ Avoid: Overly complex single validators
const badValidator = validators.custom((value) => {
	if (!value) return 'Required';
	if (value.length < 3) return 'Too short';
	if (!/^[a-zA-Z0-9]+$/.test(value)) return 'Invalid characters';
	// ... many more conditions
});
```

### 2. Error Handling

```svelte
<!-- ✅ Good: Specific, actionable error messages -->
<FormField
	name="email"
	label="Email"
	validators={[
		validators.required('Please enter your email address'),
		validators.email('Please enter a valid email address (e.g., user@example.com)')
	]}
/>

<!-- ❌ Avoid: Generic error messages -->
<FormField
	name="email"
	label="Email"
	validators={[validators.required('Invalid'), validators.email('Wrong format')]}
/>
```

### 3. Performance Optimization

```svelte
<!-- ✅ Good: Debounced validation -->
<FormField
  name="username"
  label="Username"
  validators={[validators.custom(checkUsernameAvailability)]}
  validateOnInput={true}  <!-- Debounced by default -->
/>

<!-- ✅ Good: Validate on blur for expensive operations -->
<FormField
  name="domain"
  label="Domain"
  validators={[validators.custom(validateDomainDNS)]}
  validateOnInput={false}
  validateOnBlur={true}
/>
```

### 4. Accessibility

```svelte
<!-- ✅ Good: Proper ARIA attributes -->
<FormField
	name="password"
	label="Password"
	type="password"
	required
	helpText="Must be at least 8 characters"
	validators={[validators.password()]}
/>

<!-- ✅ Good: Descriptive labels and help text -->
<FormField
	name="ra"
	label="Right Ascension (degrees)"
	helpText="Enter coordinates in decimal degrees (0-360)"
	validators={[validators.min(0), validators.max(360)]}
/>
```

### 5. Schema Organization

```typescript
// ✅ Good: Organized by feature
export const validationSchemas = {
	auth: {
		login: {
			/* ... */
		},
		register: {
			/* ... */
		},
		resetPassword: {
			/* ... */
		}
	},
	instrument: {
		create: {
			/* ... */
		},
		edit: {
			/* ... */
		}
	},
	pointing: {
		create: {
			/* ... */
		},
		bulk: {
			/* ... */
		}
	}
};
```

## Examples

### Basic Contact Form

```svelte
<script>
	import Form from '$lib/components/forms/Form.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import { validators } from '$lib/validation/validators';

	const schema = {
		name: {
			required: true,
			validators: [validators.minLength(2), validators.safe()]
		},
		email: {
			required: true,
			validators: [validators.email()]
		},
		message: {
			required: true,
			validators: [validators.minLength(10), validators.maxLength(1000)]
		}
	};

	let formData = { name: '', email: '', message: '' };

	async function handleSubmit(data) {
		const response = await fetch('/api/contact', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(data)
		});

		return {
			success: response.ok,
			error: response.ok ? undefined : 'Failed to send message'
		};
	}
</script>

<Form {schema} bind:data={formData} onSubmit={handleSubmit}>
	<FormField
		name="name"
		label="Full Name"
		required
		bind:value={formData.name}
		placeholder="Enter your full name"
	/>

	<FormField
		name="email"
		label="Email Address"
		type="email"
		required
		bind:value={formData.email}
		placeholder="your@email.com"
	/>

	<FormField
		name="message"
		label="Message"
		type="textarea"
		required
		bind:value={formData.message}
		rows={5}
		placeholder="Enter your message..."
		helpText="Minimum 10 characters, maximum 1000"
	/>
</Form>
```

### Advanced Settings Form

```svelte
<script>
	import Form from '$lib/components/forms/Form.svelte';
	import FormField from '$lib/components/forms/FormField.svelte';
	import { validators } from '$lib/validation/validators';

	const schema = {
		apiKey: {
			required: true,
			validators: [
				validators.pattern(/^[a-zA-Z0-9]{32}$/, 'API key must be 32 alphanumeric characters'),
				validators.custom(async (key) => {
					const valid = await validateApiKey(key);
					return valid ? true : 'Invalid API key';
				})
			]
		},
		webhookUrl: {
			validators: [validators.url()]
		},
		retryAttempts: {
			required: true,
			validators: [
				validators.number(),
				validators.min(1, 'Must be at least 1'),
				validators.max(10, 'Cannot exceed 10 attempts')
			]
		},
		timeout: {
			required: true,
			validators: [
				validators.number(),
				validators.min(1000, 'Minimum timeout is 1 second'),
				validators.max(300000, 'Maximum timeout is 5 minutes')
			]
		},
		enableLogging: {},
		logLevel: {
			dependsOn: ['enableLogging'],
			validators: [
				validators.custom((value, context) => {
					if (context.enableLogging && !value) {
						return 'Log level is required when logging is enabled';
					}
					return true;
				})
			]
		}
	};

	let formData = {
		apiKey: '',
		webhookUrl: '',
		retryAttempts: 3,
		timeout: 30000,
		enableLogging: false,
		logLevel: 'info'
	};
</script>

<Form {schema} bind:data={formData} let:isValid>
	<div class="space-y-6">
		<div>
			<h3 class="text-lg font-medium">API Configuration</h3>

			<FormField
				name="apiKey"
				label="API Key"
				type="password"
				required
				bind:value={formData.apiKey}
				helpText="Your 32-character API key"
			/>

			<FormField
				name="webhookUrl"
				label="Webhook URL"
				type="url"
				bind:value={formData.webhookUrl}
				placeholder="https://api.example.com/webhook"
				helpText="Optional webhook for notifications"
			/>
		</div>

		<div>
			<h3 class="text-lg font-medium">Connection Settings</h3>

			<div class="grid grid-cols-2 gap-4">
				<FormField
					name="retryAttempts"
					label="Retry Attempts"
					type="number"
					required
					bind:value={formData.retryAttempts}
				/>

				<FormField
					name="timeout"
					label="Timeout (ms)"
					type="number"
					required
					bind:value={formData.timeout}
				/>
			</div>
		</div>

		<div>
			<h3 class="text-lg font-medium">Logging</h3>

			<FormField
				name="enableLogging"
				label="Enable detailed logging"
				type="checkbox"
				bind:value={formData.enableLogging}
			/>

			{#if formData.enableLogging}
				<FormField
					name="logLevel"
					label="Log Level"
					type="select"
					required
					bind:value={formData.logLevel}
					options={[
						{ value: 'debug', label: 'Debug' },
						{ value: 'info', label: 'Info' },
						{ value: 'warn', label: 'Warning' },
						{ value: 'error', label: 'Error' }
					]}
					validationContext={formData}
				/>
			{/if}
		</div>
	</div>
</Form>
```

## Migration Guide

### From Basic HTML Forms

**Before:**

```svelte
<form on:submit|preventDefault={handleSubmit}>
	<input type="email" bind:value={email} required class:error={emailError} />
	{#if emailError}
		<p class="error">{emailError}</p>
	{/if}

	<button type="submit" disabled={!isValid}>Submit</button>
</form>
```

**After:**

```svelte
<Form {schema} bind:data={formData} onSubmit={handleSubmit}>
	<FormField name="email" label="Email" type="email" required bind:value={formData.email} />
</Form>
```

### From Manual Validation

**Before:**

```svelte
<script>
	let errors = {};

	function validateEmail(email) {
		if (!email) return 'Email is required';
		if (!/\S+@\S+\.\S+/.test(email)) return 'Invalid email';
		return null;
	}

	function handleSubmit() {
		errors.email = validateEmail(formData.email);
		if (Object.values(errors).some(Boolean)) return;

		// Submit...
	}
</script>
```

**After:**

```svelte
<script>
	import { validators, validationSchemas } from '$lib/validation/validators';

	// Use pre-built schemas or create custom ones
	const schema = validationSchemas.auth.login;
</script>
```

### Performance Considerations

- **Debouncing**: Built-in 300ms debouncing for input validation
- **Lazy Validation**: Only validates fields that have been touched
- **Memoization**: Validation results are cached when possible
- **Async Validation**: Properly handles and cancels in-flight requests

## Troubleshooting

### Common Issues

1. **Validation not triggering**

   - Ensure `validateOnInput` or `validateOnBlur` is enabled
   - Check that validators are properly configured
   - Verify the validation schema is correctly applied

2. **Form not submitting**

   - Check `preventInvalidSubmission` setting
   - Ensure all required fields are valid
   - Verify the `onSubmit` handler returns proper result format

3. **Performance issues**

   - Use `validateOnBlur` for expensive validations
   - Implement proper debouncing for async validators
   - Consider lazy loading for large forms

4. **TypeScript errors**
   - Ensure proper typing for form data and schemas
   - Use the provided type interfaces
   - Check validator function signatures

### Debug Mode

Enable detailed logging for form validation:

```svelte
<script>
	import { browser } from '$app/environment';

	// Enable debug mode in development
	if (browser && import.meta.env.DEV) {
		window.gwtmFormDebug = true;
	}
</script>
```

This comprehensive guide provides everything needed to implement robust, accessible, and maintainable forms in the GWTM frontend application.
