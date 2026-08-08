<script lang="ts">
	import FeedbackForm from '$lib/components/feedback/FeedbackForm.svelte';
</script>

<svelte:head>
	<title>Feedback - COPAI</title>
	<meta
		name="description"
		content="Share feedback with COPAI to help improve the community experience."
	/>
</svelte:head>

<div class="min-h-screen bg-gradient-to-b from-orange-50 via-white to-white text-gray-900 dark:from-gray-950 dark:via-gray-950 dark:to-gray-900">
	<div class="mx-auto flex min-h-screen w-full max-w-4xl flex-col px-4 py-6 sm:px-8 lg:px-12">
		<div class="flex items-center justify-between gap-4 rounded-2xl border border-orange-100 bg-white/90 px-5 py-4 shadow-sm backdrop-blur dark:border-gray-800 dark:bg-gray-900/90">
			<a href="/" class="text-sm font-semibold text-orange-600 transition hover:text-orange-500">Back to home</a>
			<a href="/auth" class="text-sm font-semibold text-gray-600 transition hover:text-orange-500 dark:text-gray-300">Sign in</a>
		</div>

		<div class="grid flex-1 items-center gap-8 py-10 lg:grid-cols-[1.05fr_0.95fr]">
			<section class="space-y-6">
				<div class="inline-flex items-center gap-2 rounded-full border border-orange-200 bg-orange-50 px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-orange-600 dark:border-orange-900 dark:bg-orange-950/30 dark:text-orange-400">
					<span class="h-2 w-2 rounded-full bg-orange-500"></span>
					Share feedback
				</div>
				<h1 class="text-4xl font-black leading-tight sm:text-5xl">
					Help COPAI improve the community experience.
				</h1>
				<p class="max-w-xl text-lg leading-relaxed text-gray-600 dark:text-gray-300">
					Send a short note about what is working, what is missing, or what should be built next.
				</p>

				<div class="grid gap-4 sm:grid-cols-3">
					<div class="rounded-2xl border border-orange-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
						<div class="text-xs font-bold uppercase tracking-widest text-orange-500">Fast</div>
						<div class="mt-2 text-sm text-gray-600 dark:text-gray-300">One box, one click.</div>
					</div>
					<div class="rounded-2xl border border-orange-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
						<div class="text-xs font-bold uppercase tracking-widest text-orange-500">Private</div>
						<div class="mt-2 text-sm text-gray-600 dark:text-gray-300">Only signed-in users can submit.</div>
					</div>
					<div class="rounded-2xl border border-orange-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
						<div class="text-xs font-bold uppercase tracking-widest text-orange-500">Actionable</div>
						<div class="mt-2 text-sm text-gray-600 dark:text-gray-300">We store it in the existing feedback system.</div>
					</div>
				</div>
			</section>

			<section>
				<FeedbackForm />
			</section>
		</div>
	</div>
</div>
