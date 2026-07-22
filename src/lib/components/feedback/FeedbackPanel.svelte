<script lang="ts">
	import { onMount } from 'svelte';
	import { fly, fade } from 'svelte/transition';
	import { toast } from 'svelte-sonner';
	import { createNewFeedback } from '$lib/apis/evaluations';

	export let open = false;

	let token = '';
	let message = '';
	let submitting = false;

	onMount(() => {
		token = localStorage.getItem('token') ?? '';
	});

	const close = () => {
		open = false;
	};

	const handleKeydown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') close();
	};

	const submitFeedback = async () => {
		if (!token) {
			toast.error('Please sign in before sending feedback.');
			return;
		}

		if (!message.trim()) {
			toast.error('Please describe your feedback before sending.');
			return;
		}

		submitting = true;
		try {
			await createNewFeedback(token, {
				type: 'community_feedback',
				data: {
					comment: message
				},
				meta: {
					source: 'nav',
					page: 'feedback',
					origin: 'app_panel'
				}
			});

			message = '';
			toast.success('Thanks for your feedback!');
			close();
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			submitting = false;
		}
	};
</script>

<svelte:window on:keydown={open ? handleKeydown : undefined} />

{#if open}
	<button
		type="button"
		class="fixed inset-0 z-[9999] bg-black/30"
		transition:fade={{ duration: 150 }}
		on:click={close}
		aria-label="Close feedback panel"
	></button>

	<div
		class="fixed inset-y-0 right-0 z-[10000] flex w-full max-w-md flex-col border-l border-gray-200 bg-white shadow-2xl dark:border-gray-800 dark:bg-gray-900"
		transition:fly={{ x: 400, duration: 220 }}
		role="dialog"
		aria-modal="true"
		aria-label="Send feedback"
	>
		<div class="flex items-center justify-between border-b border-gray-200 px-5 py-4 dark:border-gray-800">
			<h2 class="text-lg font-bold text-gray-900 dark:text-white">Send feedback</h2>
			<button
				type="button"
				class="rounded-full p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
				on:click={close}
				aria-label="Close"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
				</svg>
			</button>
		</div>

		<div class="flex-1 overflow-y-auto px-5 py-5">
			<label class="mb-2 block text-sm font-semibold text-gray-800 dark:text-gray-200" for="feedback-message">
				Describe your feedback (required)
			</label>
			<textarea
				id="feedback-message"
				bind:value={message}
				rows="8"
				placeholder="Tell us what prompted this feedback..."
				class="w-full resize-none rounded-xl border border-gray-300 bg-white px-3.5 py-3 text-sm outline-none transition placeholder:text-gray-400 focus:border-orange-400 focus:ring-2 focus:ring-orange-100 dark:border-gray-700 dark:bg-gray-950 dark:focus:ring-orange-900/30"
			/>
			<p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
				Please don't include any sensitive information.
			</p>

			{#if !token}
				<p class="mt-4 text-sm font-medium text-orange-600 dark:text-orange-400">
					Please sign in to send feedback.
				</p>
			{/if}
		</div>

		<div class="flex items-center justify-end gap-3 border-t border-gray-200 px-5 py-4 dark:border-gray-800">
			<button
				type="button"
				class="rounded-lg px-4 py-2 text-sm font-semibold text-gray-600 transition hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
				on:click={close}
			>
				Cancel
			</button>
			<button
				type="button"
				on:click={submitFeedback}
				disabled={!token || submitting}
				class="inline-flex items-center justify-center rounded-lg bg-gradient-to-r from-orange-500 to-orange-600 px-5 py-2 text-sm font-bold text-white transition hover:from-orange-600 hover:to-orange-700 disabled:cursor-not-allowed disabled:opacity-50"
			>
				{submitting ? 'Sending...' : 'Send'}
			</button>
		</div>
	</div>
{/if}
