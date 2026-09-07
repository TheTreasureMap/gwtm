import { describe, it, expect, vi } from 'vitest';
import { get } from 'svelte/store';
import { createFormStore, useForm } from '../formStore';
import type { ValidationSchema } from '$lib/validation/validators';

interface TestForm extends Record<string, unknown> {
	name: string;
	age: number;
}

/** setFieldValue schedules a full revalidation on a macrotask. */
const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

const required = (message: string) => ({
	required: true,
	customMessage: message
});

const schema: ValidationSchema<TestForm> = {
	name: required('name is required'),
	age: {
		validators: [
			(value) =>
				typeof value === 'number' && value >= 18
					? { isValid: true, errors: [] }
					: { isValid: false, errors: ['must be 18 or over'] }
		]
	}
};

const makeForm = (overrides = {}) =>
	createFormStore<TestForm>({
		initialValues: { name: 'Ada', age: 36 },
		validationSchema: schema,
		...overrides
	});

describe('createFormStore', () => {
	describe('initial state', () => {
		it('seeds data from initial values', () => {
			const form = makeForm();
			expect(get(form.data)).toEqual({ name: 'Ada', age: 36 });
		});

		it('creates a field state per initial value', () => {
			const form = makeForm();
			expect(form.getFieldState('name')).toMatchObject({
				value: 'Ada',
				errors: [],
				touched: false,
				focused: false,
				isValid: true
			});
		});

		it('starts valid, clean and not submitting', () => {
			const form = makeForm();
			expect(get(form.isValid)).toBe(true);
			expect(get(form.isDirty)).toBe(false);
			expect(get(form.isSubmitting)).toBe(false);
			expect(get(form.globalError)).toBe('');
		});

		it('tolerates being created with no options at all', () => {
			const form = createFormStore();
			expect(get(form.data)).toEqual({});
			expect(get(form.isValid)).toBe(true);
		});

		it('synthesises a field state for a field it has never seen', () => {
			const form = createFormStore<TestForm>();
			expect(form.getFieldState('name')).toMatchObject({ errors: [], isValid: true });
		});
	});

	describe('setFieldValue', () => {
		it('updates the value and marks the form dirty', () => {
			const form = makeForm();
			form.setFieldValue('name', 'Grace');

			expect(get(form.data).name).toBe('Grace');
			expect(get(form.isDirty)).toBe(true);
		});

		it('records validation errors for an invalid value', () => {
			const form = makeForm();
			form.setFieldValue('name', '');

			expect(form.getError('name')).toEqual(['name is required']);
			expect(form.getFieldState('name').isValid).toBe(false);
		});

		it('clears a previous error once the value becomes valid', () => {
			const form = makeForm();
			form.setFieldValue('name', '');
			expect(form.getError('name')).toHaveLength(1);

			form.setFieldValue('name', 'Grace');
			expect(form.getError('name')).toEqual([]);
		});

		it('marks the whole form invalid after revalidation settles', async () => {
			const form = makeForm();
			form.setFieldValue('age', 12);
			await flush();

			expect(get(form.isValid)).toBe(false);
		});

		it('skips validation when validateOnChange is off', () => {
			const form = makeForm({ validateOnChange: false });
			form.setFieldValue('name', '');

			expect(form.getError('name')).toEqual([]);
		});

		it('validates anyway when explicitly asked', () => {
			const form = makeForm({ validateOnChange: false });
			form.setFieldValue('name', '', true);

			expect(form.getError('name')).toEqual(['name is required']);
		});

		it('creates a field that had no initial value', () => {
			const form = createFormStore<TestForm>({ validationSchema: schema });
			form.setFieldValue('name', 'Grace');

			expect(form.getFieldState('name').value).toBe('Grace');
		});
	});

	describe('touched and focused', () => {
		it('marks a field touched', () => {
			const form = makeForm();
			form.setFieldTouched('name');
			expect(form.getFieldState('name').touched).toBe(true);
		});

		it('can un-touch a field', () => {
			const form = makeForm();
			form.setFieldTouched('name');
			form.setFieldTouched('name', false);
			expect(form.getFieldState('name').touched).toBe(false);
		});

		it('tracks focus', () => {
			const form = makeForm();
			form.setFieldFocused('name');
			expect(form.getFieldState('name').focused).toBe(true);

			form.setFieldFocused('name', false);
			expect(form.getFieldState('name').focused).toBe(false);
		});

		it('creates the field on first touch when it had no initial value', () => {
			const form = createFormStore<TestForm>();
			form.setFieldTouched('name');
			expect(form.getFieldState('name').touched).toBe(true);
		});

		it('creates the field on first focus when it had no initial value', () => {
			const form = createFormStore<TestForm>();
			form.setFieldFocused('name');
			expect(form.getFieldState('name').focused).toBe(true);
		});
	});

	describe('setFieldError', () => {
		it('applies a server-supplied error', () => {
			const form = makeForm();
			form.setFieldError('name', ['already taken']);

			expect(form.getError('name')).toEqual(['already taken']);
			expect(get(form.isValid)).toBe(false);
		});

		it('creates the field when erroring one that had no initial value', () => {
			const form = createFormStore<TestForm>();
			form.setFieldError('name', ['required']);

			expect(form.getError('name')).toEqual(['required']);
			expect(form.getFieldState('name').isValid).toBe(false);
		});

		it('clearing the last error makes the form valid again', () => {
			const form = makeForm();
			form.setFieldError('name', ['already taken']);
			form.setFieldError('name', []);

			expect(form.getError('name')).toEqual([]);
			expect(get(form.isValid)).toBe(true);
		});
	});

	describe('validateAll', () => {
		it('passes when every field satisfies the schema', () => {
			const form = makeForm();
			expect(form.validateAll()).toBe(true);
		});

		it('fails and collects errors when a field does not', () => {
			const form = makeForm({ initialValues: { name: '', age: 36 } });

			expect(form.validateAll()).toBe(false);
			expect(get(form.errors).name).toEqual(['name is required']);
		});

		it('passes trivially with no schema', () => {
			const form = createFormStore<TestForm>({ initialValues: { name: '', age: 1 } });
			expect(form.validateAll()).toBe(true);
		});
	});

	describe('reset', () => {
		it('restores the initial values and clears dirty state', () => {
			const form = makeForm();
			form.setFieldValue('name', 'Grace');
			form.setFieldTouched('name');

			form.reset();

			expect(get(form.data)).toEqual({ name: 'Ada', age: 36 });
			expect(get(form.isDirty)).toBe(false);
			expect(form.getFieldState('name').touched).toBe(false);
		});

		it('clears errors and the global error', () => {
			const form = makeForm();
			form.setFieldError('name', ['boom']);
			form.setGlobalError('server exploded');

			form.reset();

			expect(get(form.errors)).toEqual({});
			expect(get(form.globalError)).toBe('');
			expect(get(form.isValid)).toBe(true);
		});
	});

	describe('submit', () => {
		it('refuses to submit an invalid form', async () => {
			const submitHandler = vi.fn();
			const form = makeForm({ initialValues: { name: '', age: 36 }, submitHandler });

			const result = await form.submit();

			expect(result).toEqual({ success: false, error: 'Validation failed' });
			expect(submitHandler).not.toHaveBeenCalled();
			expect(get(form.globalError)).toBe('Please correct the errors below');
			expect(get(form.isSubmitting)).toBe(false);
		});

		it('calls the handler with the current data', async () => {
			const submitHandler = vi.fn().mockResolvedValue({ success: true });
			const form = makeForm({ submitHandler });

			await form.submit();

			expect(submitHandler).toHaveBeenCalledWith({ name: 'Ada', age: 36 });
		});

		it('increments the submit count and clears the submitting flag', async () => {
			const form = makeForm({ submitHandler: vi.fn().mockResolvedValue({ success: true }) });

			await form.submit();

			expect(get(form).submitCount).toBe(1);
			expect(get(form.isSubmitting)).toBe(false);
		});

		it('surfaces a handler failure as the global error', async () => {
			const form = makeForm({
				submitHandler: vi.fn().mockResolvedValue({ success: false, error: 'duplicate entry' })
			});

			const result = await form.submit();

			expect(result.success).toBe(false);
			expect(get(form.globalError)).toBe('duplicate entry');
		});

		it('falls back to a generic message when the handler gives no reason', async () => {
			const form = makeForm({ submitHandler: vi.fn().mockResolvedValue({ success: false }) });

			await form.submit();

			expect(get(form.globalError)).toBe('Submission failed');
		});

		it('publishes the result on the submitResult store', async () => {
			const form = makeForm({
				submitHandler: vi.fn().mockResolvedValue({ success: true, result: { id: 7 } })
			});

			await form.submit();

			expect(get(form.submitResult)).toEqual({ success: true, result: { id: 7 } });
		});

		it('resets after a successful submit when configured to', async () => {
			const form = makeForm({
				submitHandler: vi.fn().mockResolvedValue({ success: true }),
				resetOnSubmit: true
			});
			form.setFieldValue('name', 'Grace');

			await form.submit();

			expect(get(form.data).name).toBe('Ada');
		});

		it('does not reset after a failed submit', async () => {
			const form = makeForm({
				submitHandler: vi.fn().mockResolvedValue({ success: false, error: 'nope' }),
				resetOnSubmit: true
			});
			form.setFieldValue('name', 'Grace');

			await form.submit();

			expect(get(form.data).name).toBe('Grace');
		});

		it('catches a throwing handler and reports its message', async () => {
			const form = makeForm({
				submitHandler: vi.fn().mockRejectedValue(new Error('network down'))
			});

			const result = await form.submit();

			expect(result).toEqual({ success: false, error: 'network down' });
			expect(get(form.globalError)).toBe('network down');
			expect(get(form.isSubmitting)).toBe(false);
		});

		it('stringifies a non-Error rejection', async () => {
			const form = makeForm({ submitHandler: vi.fn().mockRejectedValue('just a string') });

			const result = await form.submit();

			expect(result.error).toBe('just a string');
		});

		it('succeeds with no handler configured', async () => {
			const form = makeForm({ submitHandler: undefined });

			const result = await form.submit();

			expect(result).toEqual({ success: true });
			expect(get(form).submitCount).toBe(1);
		});
	});

	describe('handleSubmit', () => {
		it('prevents the default form action', async () => {
			const form = makeForm({ submitHandler: vi.fn().mockResolvedValue({ success: true }) });
			const event = new Event('submit', { cancelable: true });
			const preventDefault = vi.spyOn(event, 'preventDefault');

			await form.handleSubmit(event);

			expect(preventDefault).toHaveBeenCalled();
		});

		it('works with no event, as a direct call', async () => {
			const form = makeForm({ submitHandler: vi.fn().mockResolvedValue({ success: true }) });
			await expect(form.handleSubmit()).resolves.toEqual({ success: true });
		});
	});

	describe('global error', () => {
		it('sets and clears', () => {
			const form = makeForm();
			form.setGlobalError('something broke');
			expect(get(form.globalError)).toBe('something broke');

			form.clearGlobalError();
			expect(get(form.globalError)).toBe('');
		});
	});

	describe('accessors', () => {
		it('getValue reads a single field', () => {
			expect(makeForm().getValue('name')).toBe('Ada');
		});

		it('getError returns an empty array for a clean field', () => {
			expect(makeForm().getError('name')).toEqual([]);
		});

		it('getFieldConfig exposes the schema entry', () => {
			expect(makeForm().getFieldConfig('name')).toEqual(schema.name);
		});

		it('getFieldConfig is undefined without a schema', () => {
			expect(createFormStore<TestForm>().getFieldConfig('name')).toBeUndefined();
		});
	});
});

describe('useForm', () => {
	it('is an alias for createFormStore', () => {
		const form = useForm<TestForm>({ initialValues: { name: 'Ada', age: 36 } });
		expect(get(form.data)).toEqual({ name: 'Ada', age: 36 });
		expect(typeof form.submit).toBe('function');
	});
});
