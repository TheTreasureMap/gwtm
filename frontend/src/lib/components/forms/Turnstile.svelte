<script lang="ts">
	/**
	 * @component Turnstile
	 * @description Cloudflare Turnstile captcha widget. Exposes the challenge token through a bound prop.
	 * @category Forms
	 *
	 * @example
	 * <Turnstile bind:this={turnstile} bind:token siteKey={siteKey} />
	 */
	import { onMount } from 'svelte';

	interface TurnstileApi {
		render: (container: HTMLElement, options: Record<string, unknown>) => string;
		reset: (widgetId: string) => void;
		remove: (widgetId: string) => void;
	}

	const SCRIPT_URL = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';

	/** Cloudflare Turnstile site key. Nothing is rendered while this is empty. */
	export let siteKey: string;

	/** Current challenge token, empty until the challenge passes or after it expires. */
	export let token = '';

	let container: HTMLElement | undefined;
	let widgetId: string | undefined;
	let loadFailed = false;

	function getApi(): TurnstileApi | undefined {
		return (window as unknown as { turnstile?: TurnstileApi }).turnstile;
	}

	function loadScript(): Promise<void> {
		if (getApi()) return Promise.resolve();

		return new Promise((resolve, reject) => {
			let script = document.querySelector<HTMLScriptElement>(`script[src="${SCRIPT_URL}"]`);
			if (!script) {
				script = document.createElement('script');
				script.src = SCRIPT_URL;
				script.async = true;
				document.head.appendChild(script);
			}
			script.addEventListener('load', () => resolve());
			script.addEventListener('error', () => {
				// Drop the failed tag so the next mount fetches the script again.
				script?.remove();
				reject(new Error('Failed to load Turnstile'));
			});
		});
	}

	/** Turnstile tokens are single use, so call this after any failed submit. */
	export function reset() {
		token = '';
		if (widgetId) getApi()?.reset(widgetId);
	}

	onMount(() => {
		if (!siteKey) return;

		let cancelled = false;

		loadScript()
			.then(() => {
				if (cancelled || !container) return;
				widgetId = getApi()?.render(container, {
					sitekey: siteKey,
					callback: (value: string) => (token = value),
					'expired-callback': () => (token = ''),
					'error-callback': () => (token = '')
				});
			})
			.catch((err) => {
				console.error(err);
				loadFailed = true;
			});

		return () => {
			cancelled = true;
			if (widgetId) getApi()?.remove(widgetId);
		};
	});
</script>

{#if siteKey}
	<div bind:this={container}></div>
	{#if loadFailed}
		<p class="text-sm text-red-600" role="alert">
			The captcha failed to load. Refresh the page to try again.
		</p>
	{/if}
{/if}
