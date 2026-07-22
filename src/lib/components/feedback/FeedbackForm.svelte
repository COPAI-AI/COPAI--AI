<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { createNewFeedback } from '$lib/apis/evaluations';

	let token = '';
	let message = '';
	let submitting = false;
	let submitted = false;

	onMount(() => {
		token = localStorage.getItem('token') ?? '';
	});

	const submitFeedback = async () => {
		if (!token) {
			toast.error('Please sign in before sending feedback.');
			return;
		}

		if (!message.trim()) {
			toast.error('Please write a message before sending.');
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
					origin: 'welcome_nav'
				}
			});

			submitted = true;
			message = '';
			toast.success('Thanks for your feedback!');
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			submitting = false;
		}
	};
</script>

<div class="rounded-3xl border border-orange-100 bg-white p-6 shadow-2xl shadow-orange-100/50 dark:border-gray-800 dark:bg-gray-900">
	<div class="space-y-5">
		<div>
			<label class="mb-2 block text-sm font-semibold text-gray-700 dark:text-gray-300" for="message">
				What's on your mind?
			</label>
			<textarea
				id="message"
				bind:value={message}
				rows="7"
				placeholder="Share your thoughts, ideas, or issues with COPAI..."
				class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm outline-none transition placeholder:text-gray-400 focus:border-orange-400 focus:ring-2 focus:ring-orange-100 dark:border-gray-700 dark:bg-gray-950 dark:focus:ring-orange-900/30"
			/>
		</div>

		<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
			<p class="text-sm text-gray-500 dark:text-gray-400">
				{#if token}
					You are signed in and ready to submit.
				{:else}
					Please sign in to send feedback.
				{/if}
			</p>
			<button
				on:click={submitFeedback}
				disabled={!token || submitting}
				class="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 px-5 py-3 text-sm font-bold text-white transition hover:from-orange-600 hover:to-orange-700 disabled:cursor-not-allowed disabled:opacity-50"
			>
				{submitting ? 'Sending...' : 'Send feedback'}
			</button>
		</div>

		{#if submitted}
			<div class="rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm font-medium text-green-800 dark:border-green-900 dark:bg-green-950/30 dark:text-green-300">
				Thanks for your feedback.
			</div>
		{/if}
	</div>
</div>
