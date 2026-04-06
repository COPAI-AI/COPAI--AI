<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext, tick } from 'svelte';
	import { getModels as _getModels } from '$lib/apis';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	import { models, settings, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Connection from '$lib/components/chat/Settings/Tools/Connection.svelte';

	import AddServerModal from '$lib/components/AddServerModal.svelte';
	import { getToolServerConnections, setToolServerConnections } from '$lib/apis/configs';

	export let saveSettings: Function;

	let servers = null;
	let showConnectionModal = false;

	const addConnectionHandler = async (server) => {
		servers = [...servers, server];
		await updateHandler();
	};

	const updateHandler = async () => {
		const res = await setToolServerConnections(localStorage.token, {
			TOOL_SERVER_CONNECTIONS: servers
		}).catch((err) => {
			toast.error($i18n.t('Failed to save connections'));

			return null;
		});

		if (res) {
			toast.success($i18n.t('Connections saved successfully'));
		}
	};

	onMount(async () => {
		const res = await getToolServerConnections(localStorage.token);
		servers = res.TOOL_SERVER_CONNECTIONS;
	});
</script>

<AddServerModal bind:show={showConnectionModal} onSubmit={addConnectionHandler} />

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={() => {
		updateHandler();
	}}
>
	<div class="mt-0.5 space-y-3 sm:space-y-4 overflow-y-auto scrollbar-hidden h-full pr-1">
		{#if servers !== null}
			<!-- Tool Servers Section -->
			<div class="mb-6 bg-gradient-to-b from-gray-50/50 to-transparent dark:from-gray-800/20 dark:to-transparent rounded-xl p-3 sm:p-5 border border-gray-200/60 dark:border-gray-700/30">
				<div class="mb-4 flex items-center gap-2">
					<div class="w-1 h-6 bg-orange-500 rounded-sm"></div>
					<div class="text-base font-semibold text-gray-900 dark:text-gray-100" style="letter-spacing: -0.01em;">{$i18n.t('Tool Servers')}</div>
				</div>

				<div class="space-y-3 bg-white dark:bg-gray-800/50 rounded-lg p-3 sm:p-4 shadow-sm border border-gray-200/80 dark:border-gray-700/50">
					<!-- Header with Description -->
					<div class="flex justify-between items-start gap-3 pb-3 border-b border-gray-200/60 dark:border-gray-700/40">
						<div class="flex-1">
							<div class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
								{$i18n.t('Manage Tool Servers')}
							</div>
							<div class="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
								{$i18n.t('Connect to your own OpenAPI compatible external tool servers.')}
							</div>
						</div>
						<Tooltip content={$i18n.t(`Add Connection`)}>
							<button
								class="p-2.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 hover:bg-blue-200 dark:hover:bg-blue-900/50 text-blue-600 dark:text-blue-400 transition-colors duration-200 flex-shrink-0"
								on:click={() => {
									showConnectionModal = true;
								}}
								type="button"
							>
								<Plus strokeWidth="2" className="size-4" />
							</button>
						</Tooltip>
					</div>

					<!-- Server Connections List -->
					<div class="pt-3">
						{#if servers.length > 0}
							<div class="flex flex-col gap-2.5">
								{#each servers as server, idx}
									<div class="bg-gray-50 dark:bg-gray-900/30 rounded-lg p-3 border border-gray-200/50 dark:border-gray-700/40">
										<Connection
											bind:connection={server}
											onSubmit={() => {
												updateHandler();
											}}
											onDelete={() => {
												servers = servers.filter((_, i) => i !== idx);
												updateHandler();
											}}
										/>
									</div>
								{/each}
							</div>
						{:else}
							<div class="flex flex-col items-center justify-center py-8">
								<svg class="w-10 h-10 text-gray-300 dark:text-gray-700 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
								</svg>
								<p class="text-xs text-gray-500 dark:text-gray-400 text-center">
									{$i18n.t('No tool servers connected')}
								</p>
								<button
									class="mt-3 px-3 py-1.5 text-xs font-medium bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 rounded-lg transition-colors duration-200"
									on:click={() => {
										showConnectionModal = true;
									}}
									type="button"
								>
									{$i18n.t('Add First Server')}
								</button>
							</div>
						{/if}
					</div>
				</div>
			</div>
		{:else}
			<div class="flex h-full justify-center">
				<div class="my-auto">
					<Spinner className="size-6" />
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3 border-t border-gray-200/60 dark:border-gray-700/30">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-orange-600 hover:bg-orange-700 text-white transition rounded-lg"
			type="submit"
		>
			{$i18n.t('Save')}
		</button>
	</div>
</form>
