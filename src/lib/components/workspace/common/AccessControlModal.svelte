<script>
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import Modal from '$lib/components/common/Modal.svelte';
	import AccessControl from './AccessControl.svelte';

	export let show = false;
	export let accessControl = {};
	export let accessRoles = ['read'];
	export let allowPublic = true;

	export let onChange = () => {};
</script>

<Modal size="sm" bind:show>
	<div class="bg-white dark:bg-gray-800 rounded-xl overflow-hidden">
		<!-- Header -->
		<div class="flex justify-between items-center px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
			<h3 class="text-lg font-bold text-gray-900 dark:text-white">
				{$i18n.t('Access Control')}
			</h3>
			<button
				class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
				on:click={() => {
					show = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5 text-gray-500 dark:text-gray-400"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<!-- Content -->
		<div class="px-6 py-6">
			<AccessControl bind:accessControl {onChange} {accessRoles} {allowPublic} />
		</div>
	</div>
</Modal>
