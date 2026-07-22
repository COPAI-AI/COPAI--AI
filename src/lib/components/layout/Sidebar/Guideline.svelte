  <script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { WEBUI_BASE_URL } from '$lib/constants';
	const i18n: any = getContext('i18n');

	const goBack = async () => {
		if (typeof window !== 'undefined' && window.history.length > 1) {
			window.history.back();
			return;
		}

		await goto('/');
	};
</script>

<div
	class="h-full max-h-[100dvh] w-full overflow-y-auto overscroll-contain touch-pan-y px-3 pb-6 pt-4 sm:px-6 sm:pt-6"
	style="-webkit-overflow-scrolling: touch;"
>
	<div class="sticky top-0 z-20 mb-5 bg-white pb-2 dark:bg-gray-950 sm:mb-8 sm:bg-transparent sm:pb-0">
		<div class="flex items-center justify-between">
			<button
				type="button"
				on:click={goBack}
				class="group inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white py-1.5 pl-1.5 pr-4 text-sm font-semibold text-gray-700 shadow-sm transition-all hover:border-orange-300 hover:text-orange-600 hover:shadow dark:border-gray-800 dark:bg-gray-900 dark:text-gray-200 dark:hover:border-orange-800 dark:hover:text-orange-400"
			>
				<span
					class="inline-flex size-6 items-center justify-center rounded-full bg-gray-100 text-gray-600 transition-colors group-hover:bg-orange-100 group-hover:text-orange-600 dark:bg-gray-800 dark:text-gray-300 dark:group-hover:bg-orange-950/50 dark:group-hover:text-orange-400"
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="size-3.5">
						<path
							fill-rule="evenodd"
							d="M17 10a.75.75 0 0 1-.75.75H5.56l3.22 3.22a.75.75 0 1 1-1.06 1.06l-4.5-4.5a.75.75 0 0 1 0-1.06l4.5-4.5a.75.75 0 1 1 1.06 1.06l-3.22 3.22h10.69A.75.75 0 0 1 17 10Z"
							clip-rule="evenodd"
						/>
					</svg>
				</span>
				{$i18n.t('Back')}
			</button>
			<div class="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 sm:hidden">
				{$i18n.t('Guideline')}
			</div>
		</div>
	</div>

	<!-- Header -->
	<div class="mb-5 hidden sm:mb-6 sm:block">
		<h1 class="text-xl font-bold text-gray-900 dark:text-white sm:text-2xl">
			{$i18n.t('Guideline')}
		</h1>
		<p class="mt-1 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
			Please read the following guidelines to use the system properly.
		</p>
	</div>

	<!-- Main Card -->
	<div
		class="rounded-2xl border border-gray-200 dark:border-gray-800
		bg-white dark:bg-gray-900 shadow-sm p-4 sm:p-6 space-y-5 sm:space-y-6"
	>
		<!-- Guideline Image -->
		<div class="flex justify-center">
			<img
				crossorigin="anonymous"
				src="{WEBUI_BASE_URL}/static/Guideline.png"
				class="h-auto w-full max-w-4xl rounded-lg border border-gray-100 shadow-sm dark:border-gray-800 sm:rounded-xl"
				alt="logo"
			/>
		</div>

		<!-- Section 1 -->
		<div>
			<h2 class="text-base font-semibold text-gray-900 dark:text-white mb-2">
				📌 General Rules
			</h2>
			<ul class="list-disc list-inside space-y-1 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
				<li>Use the system in a responsible and ethical manner.</li>
				<li>Avoid sharing personal, confidential, or sensitive information.</li>
				<li>Follow community standards and platform policies at all times.</li>
			</ul>
		</div>

		<!-- Section 2 -->
		<div>
			<h2 class="text-base font-semibold text-gray-900 dark:text-white mb-2">
				💬 Chat Usage
			</h2>
			<ul class="list-disc list-inside space-y-1 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
				<li>Ask clear, specific, and meaningful questions.</li>
				<li>Refrain from sending spam or repeated messages.</li>
				<li>Do not attempt to bypass system limitations or restrictions.</li>
			</ul>
		</div>

		<!-- Section 3 -->
		<div>
			<h2 class="text-base font-semibold text-gray-900 dark:text-white mb-2">
				🔐 Account & Security
			</h2>
			<p class="text-sm leading-relaxed text-gray-600 dark:text-gray-400">
				Keep your account secure at all times.
				Never share your password, access token, or login credentials with anyone.
				If you detect any unusual or suspicious activity, please log out immediately and contact support.
			</p>
		</div>

		<!-- Tip Box -->
		<div
			class="rounded-xl border border-blue-200 dark:border-blue-900
			bg-blue-50 dark:bg-blue-950/30 p-4"
		>
			<p class="text-sm leading-relaxed text-blue-800 dark:text-blue-300">
				💡 Tip: Following these guidelines ensures a better and safer experience for everyone.
			</p>
		</div>
	</div>

</div>
