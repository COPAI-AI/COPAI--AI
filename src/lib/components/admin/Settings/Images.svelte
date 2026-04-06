<script lang="ts">
	import { toast } from 'svelte-sonner';

	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config as backendConfig, user } from '$lib/stores';

	import { getBackendConfig } from '$lib/apis';
	import {
		getImageGenerationModels,
		getImageGenerationConfig,
		updateImageGenerationConfig,
		getConfig,
		updateConfig,
		verifyConfigUrl
	} from '$lib/apis/images';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import SelectDropdown from '$lib/components/common/SelectDropdown.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	const dispatch = createEventDispatcher();

	const i18n = getContext('i18n');

	let loading = false;

	let config = null;
	let imageGenerationConfig = null;

	let models = null;

	let samplers = [
		'DPM++ 2M',
		'DPM++ SDE',
		'DPM++ 2M SDE',
		'DPM++ 2M SDE Heun',
		'DPM++ 2S a',
		'DPM++ 3M SDE',
		'Euler a',
		'Euler',
		'LMS',
		'Heun',
		'DPM2',
		'DPM2 a',
		'DPM fast',
		'DPM adaptive',
		'Restart',
		'DDIM',
		'DDIM CFG++',
		'PLMS',
		'UniPC'
	];

	let schedulers = [
		'Automatic',
		'Uniform',
		'Karras',
		'Exponential',
		'Polyexponential',
		'SGM Uniform',
		'KL Optimal',
		'Align Your Steps',
		'Simple',
		'Normal',
		'DDIM',
		'Beta'
	];

	let requiredWorkflowNodes = [
		{
			type: 'prompt',
			key: 'text',
			node_ids: ''
		},
		{
			type: 'model',
			key: 'ckpt_name',
			node_ids: ''
		},
		{
			type: 'width',
			key: 'width',
			node_ids: ''
		},
		{
			type: 'height',
			key: 'height',
			node_ids: ''
		},
		{
			type: 'steps',
			key: 'steps',
			node_ids: ''
		},
		{
			type: 'seed',
			key: 'seed',
			node_ids: ''
		}
	];

	const getModels = async () => {
		models = await getImageGenerationModels(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
	};

	const updateConfigHandler = async () => {
		const res = await updateConfig(localStorage.token, config)
			.catch((error) => {
				toast.error(`${error}`);
				return null;
			})
			.catch((error) => {
				toast.error(`${error}`);
				return null;
			});

		if (res) {
			config = res;
		}

		if (config.enabled) {
			backendConfig.set(await getBackendConfig());
			getModels();
		}
	};

	const validateJSON = (json) => {
		try {
			const obj = JSON.parse(json);

			if (obj && typeof obj === 'object') {
				return true;
			}
		} catch (e) {}
		return false;
	};

	const saveHandler = async () => {
		loading = true;

		if (config?.comfyui?.COMFYUI_WORKFLOW) {
			if (!validateJSON(config.comfyui.COMFYUI_WORKFLOW)) {
				toast.error('Invalid JSON format for ComfyUI Workflow.');
				loading = false;
				return;
			}
		}

		if (config?.comfyui?.COMFYUI_WORKFLOW) {
			config.comfyui.COMFYUI_WORKFLOW_NODES = requiredWorkflowNodes.map((node) => {
				return {
					type: node.type,
					key: node.key,
					node_ids:
						node.node_ids.trim() === '' ? [] : node.node_ids.split(',').map((id) => id.trim())
				};
			});
		}

		await updateConfig(localStorage.token, config).catch((error) => {
			toast.error(`${error}`);
			loading = false;
			return null;
		});

		await updateImageGenerationConfig(localStorage.token, imageGenerationConfig).catch((error) => {
			toast.error(`${error}`);
			loading = false;
			return null;
		});

		getModels();
		dispatch('save');
		loading = false;
	};

	onMount(async () => {
		if ($user?.role === 'admin') {
			const res = await getConfig(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res) {
				config = res;
			}

			if (config.enabled) {
				getModels();
			}

			if (config.comfyui.COMFYUI_WORKFLOW) {
				try {
					config.comfyui.COMFYUI_WORKFLOW = JSON.stringify(
						JSON.parse(config.comfyui.COMFYUI_WORKFLOW),
						null,
						2
					);
				} catch (e) {
					console.log(e);
				}
			}

			requiredWorkflowNodes = requiredWorkflowNodes.map((node) => {
				const n = config.comfyui.COMFYUI_WORKFLOW_NODES.find((n) => n.type === node.type) ?? node;

				console.log(n);

				return {
					type: n.type,
					key: n.key,
					node_ids: typeof n.node_ids === 'string' ? n.node_ids : n.node_ids.join(',')
				};
			});

			const imageConfigRes = await getImageGenerationConfig(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (imageConfigRes) {
				imageGenerationConfig = imageConfigRes;
			}
		}
	});
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={async () => {
		saveHandler();
	}}
>
	<div class=" space-y-3 overflow-y-auto scrollbar-hidden pr-2" style="padding-bottom: 50px; gap: 20px;">
		{#if config && imageGenerationConfig}
			<!-- Image Settings Section -->
			<div style="background: linear-gradient(to bottom, rgba(0,0,0,0.02), transparent); border-radius: 12px; padding: 20px; border: 1px solid rgba(0,0,0,0.05);">
				<div class="mb-4 flex items-center gap-2">
					<div class="w-1 h-6 bg-orange-500 rounded-sm"></div>
					<div class="text-base font-medium text-gray-800 dark:text-gray-200 tracking-tight">
						{$i18n.t('Image Settings')}
					</div>
				</div>

				<div style="background: white; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.06); space-y-3;">
					<div class="space-y-3">
				<div class="py-0.5 flex w-full flex-col gap-2 sm:flex-row sm:justify-between sm:items-center" style="padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.04);">
					<div class="self-center text-xs font-medium" style="color: #374151; font-size: 13px;">{$i18n.t('Image Generation')}</div>

						<div class="px-1">
							<Switch
								bind:state={config.enabled}
								on:change={(e) => {
									const enabled = e.detail;

									if (enabled) {
										if (
											config.engine === 'automatic1111' &&
											config.automatic1111.AUTOMATIC1111_BASE_URL === ''
										) {
											toast.error($i18n.t('AUTOMATIC1111 Base URL is required.'));
											config.enabled = false;
										} else if (
											config.engine === 'comfyui' &&
											config.comfyui.COMFYUI_BASE_URL === ''
										) {
											toast.error($i18n.t('ComfyUI Base URL is required.'));
											config.enabled = false;
										} else if (config.engine === 'openai' && config.openai.OPENAI_API_KEY === '') {
											toast.error($i18n.t('OpenAI API Key is required.'));
											config.enabled = false;
										} else if (config.engine === 'gemini' && config.gemini.GEMINI_API_KEY === '') {
											toast.error($i18n.t('Gemini API Key is required.'));
											config.enabled = false;
										}
									}

									updateConfigHandler();
								}}
							/>
						</div>
					</div>
				</div>

				{#if config.enabled}
					<div class=" py-1 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Image Prompt Generation')}</div>
						<div class="px-1">
							<Switch bind:state={config.prompt_generation} />
						</div>
					</div>
				{/if}

				<div class="py-0.5 flex w-full flex-col gap-2 sm:flex-row sm:justify-between sm:items-center" style="padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.04); margin-top: 14px;">
					<div class="self-center text-xs font-medium" style="color: #374151; font-size: 13px;">{$i18n.t('Image Generation Engine')}</div>
					<div class="w-full sm:w-auto relative">
						<SelectDropdown
							align="right"
							value={config.engine}
							options={[
								{ value: 'openai', label: 'Default (Open AI)' },
								{ value: 'comfyui', label: 'ComfyUI' },
								{ value: 'automatic1111', label: 'Automatic1111' },
								{ value: 'gemini', label: 'Gemini' }
							]}
							on:change={async (e) => {
								config.engine = e.detail.value;
								await updateConfigHandler();
							}}
						/>
					</div>
				</div>
				</div>
			</div>
			

			<div class="flex flex-col gap-2" style="margin-top: 20px;">
				{#if (config?.engine ?? 'automatic1111') === 'automatic1111'}
					<div style="border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; padding: 16px;">
						<div class="text-sm font-semibold mb-4" style="color: #1f2937;">{$i18n.t('AUTOMATIC1111 Config')}</div>

						<div class="space-y-4" style="gap: 16px;">
							<!-- Base URL -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('Base URL')}
								</label>
								<div class="flex gap-2">
									<input
										class="flex-1 w-full rounded-lg py-2 px-4 text-sm outline-hidden"
										placeholder="http://127.0.0.1:7860/"
										bind:value={config.automatic1111.AUTOMATIC1111_BASE_URL}
										style="border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
									/>
									<button
										class="px-3 py-2 bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white rounded-lg transition-all duration-200 text-xs font-medium"
										type="button"
										on:click={async () => {
											await updateConfigHandler();
											const res = await verifyConfigUrl(localStorage.token).catch((error) => {
												toast.error(`${error}`);
												return null;
											});

											if (res) {
												toast.success($i18n.t('Server connection verified'));
											}
										}}
									>
										Test
									</button>
								</div>
							</div>

							<!-- API Auth -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('API Auth String')}
								</label>
								<SensitiveInput
									placeholder="username:password"
									bind:value={config.automatic1111.AUTOMATIC1111_API_AUTH}
									required={false}
									style="border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb; border-radius: 8px;"
								/>
							</div>

							<!-- Sampler -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('Sampler')}
								</label>
								<input
									list="sampler-list"
									class="w-full rounded-lg py-2 px-4 text-sm outline-hidden"
									placeholder="Euler a"
									bind:value={config.automatic1111.AUTOMATIC1111_SAMPLER}
									style="border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
								/>

								<datalist id="sampler-list">
									{#each samplers ?? [] as sampler}
										<option value={sampler}>{sampler}</option>
									{/each}
								</datalist>
							</div>

							<!-- Scheduler -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('Scheduler')}
								</label>
								<input
									list="scheduler-list"
									class="w-full rounded-lg py-2 px-4 text-sm outline-hidden"
									placeholder="Karras"
									bind:value={config.automatic1111.AUTOMATIC1111_SCHEDULER}
									style="border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
								/>

								<datalist id="scheduler-list">
									{#each schedulers ?? [] as scheduler}
										<option value={scheduler}>{scheduler}</option>
									{/each}
								</datalist>
							</div>

							<!-- CFG Scale -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('CFG Scale')}
								</label>
								<input
									class="w-full rounded-lg py-2 px-4 text-sm outline-hidden"
									placeholder="7.0"
									bind:value={config.automatic1111.AUTOMATIC1111_CFG_SCALE}
									style="border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
								/>
							</div>
						</div>
					</div>
				{:else if config?.engine === 'comfyui'}
					<div style="padding: 12px; background: #f9fafb; border-radius: 8px; border: 1px solid rgba(0,0,0,0.06);">
						<div class=" mb-2 text-sm font-medium" style="color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px;">{$i18n.t('ComfyUI Base URL')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<input
									class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
									placeholder={$i18n.t('Enter URL (e.g. http://127.0.0.1:7860/)')}
									bind:value={config.comfyui.COMFYUI_BASE_URL}
								/>
							</div>
							<button
								class="px-3 py-2 bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white rounded-lg transition-all duration-200 shadow-md hover:shadow-lg flex items-center justify-center"
								type="button"
								on:click={async () => {
									await updateConfigHandler();
									const res = await verifyConfigUrl(localStorage.token).catch((error) => {
										toast.error(`${error}`);
										return null;
									});

									if (res) {
										toast.success($i18n.t('Server connection verified'));
									}
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									class="w-4 h-4"
								>
									<path
										fill-rule="evenodd"
										d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z"
										clip-rule="evenodd"
									/>
								</svg>
							</button>
						</div>
					</div>

					<div class="">
						<div class=" mb-2 text-sm font-medium">{$i18n.t('ComfyUI API Key')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<SensitiveInput
									placeholder={$i18n.t('sk-1234')}
									bind:value={config.comfyui.COMFYUI_API_KEY}
									required={false}
								/>
							</div>
						</div>
					</div>

					<div class="">
						<div class=" mb-2 text-sm font-medium">{$i18n.t('ComfyUI Workflow')}</div>

						{#if config.comfyui.COMFYUI_WORKFLOW}
							<textarea
								class="w-full rounded-lg mb-1 py-2 px-4 text-xs bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden disabled:text-gray-600 resize-none"
								rows="10"
								bind:value={config.comfyui.COMFYUI_WORKFLOW}
								required
							/>
						{/if}

						<div class="flex w-full">
							<div class="flex-1">
								<input
									id="upload-comfyui-workflow-input"
									hidden
									type="file"
									accept=".json"
									on:change={(e) => {
										const file = e.target.files[0];
										const reader = new FileReader();

										reader.onload = (e) => {
											config.comfyui.COMFYUI_WORKFLOW = e.target.result;
											e.target.value = null;
										};

										reader.readAsText(file);
									}}
								/>

								<button
									class="w-full text-sm font-medium py-2 bg-transparent hover:bg-gray-100 border border-dashed dark:border-gray-850 dark:hover:bg-gray-850 text-center rounded-xl"
									type="button"
									on:click={() => {
										document.getElementById('upload-comfyui-workflow-input')?.click();
									}}
								>
									{$i18n.t('Click here to upload a workflow.json file.')}
								</button>
							</div>
						</div>

						<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Make sure to export a workflow.json file as API format from ComfyUI.')}
						</div>
					</div>

					{#if config.comfyui.COMFYUI_WORKFLOW}
						<div class="">
							<div class=" mb-2 text-sm font-medium">{$i18n.t('ComfyUI Workflow Nodes')}</div>

							<div class="text-xs flex flex-col gap-1.5">
								{#each requiredWorkflowNodes as node}
									<div class="flex w-full items-center border dark:border-gray-850 rounded-lg">
										<div class="shrink-0">
											<div
												class=" capitalize line-clamp-1 font-medium px-3 py-1 w-20 text-center rounded-l-lg bg-green-500/10 text-green-700 dark:text-green-200"
											>
												{node.type}{node.type === 'prompt' ? '*' : ''}
											</div>
										</div>
										<div class="">
											<Tooltip content="Input Key (e.g. text, unet_name, steps)">
												<input
													class="py-1 px-3 w-24 text-xs text-center bg-transparent outline-hidden border-r dark:border-gray-850"
													placeholder="Key"
													bind:value={node.key}
													required
												/>
											</Tooltip>
										</div>

										<div class="w-full">
											<Tooltip
												content="Comma separated Node Ids (e.g. 1 or 1,2)"
												placement="top-start"
											>
												<input
													class="w-full py-1 px-4 rounded-r-lg text-xs bg-transparent outline-hidden"
													placeholder="Node Ids"
													bind:value={node.node_ids}
												/>
											</Tooltip>
										</div>
									</div>
								{/each}
							</div>

							<div class="mt-2 text-xs text-right text-gray-400 dark:text-gray-500">
								{$i18n.t('*Prompt node ID(s) are required for image generation')}
							</div>
						</div>
					{/if}
				{:else if config?.engine === 'openai'}
					<div style="border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; padding: 16px;">
						<div class="text-sm font-semibold mb-4" style="color: #1f2937;">{$i18n.t('OpenAI API Config')}</div>

						<div class="space-y-3" style="gap: 12px;">
							<!-- API Base URL -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('API Base URL')} <span style="color: #ef4444;">*</span>
								</label>
								<input
									class="w-full text-sm rounded-lg outline-hidden"
									placeholder="https://api.openai.com/v1"
									bind:value={config.openai.OPENAI_API_BASE_URL}
									style="padding: 10px 14px; border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
									required
								/>
							</div>

							<!-- API Key -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('API Key')} <span style="color: #ef4444;">*</span>
								</label>
								<SensitiveInput
									placeholder="sk-..."
									bind:value={config.openai.OPENAI_API_KEY}
									style="padding: 10px 14px; border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb; border-radius: 8px;"
								/>
							</div>
						</div>
					</div>
				{:else if config?.engine === 'gemini'}
					<div style="border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; padding: 16px;">
						<div class="text-sm font-semibold mb-4" style="color: #1f2937;">{$i18n.t('Gemini API Config')}</div>

						<div class="space-y-3" style="gap: 12px;">
							<!-- API Base URL -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('API Base URL')} <span style="color: #ef4444;">*</span>
								</label>
								<input
									class="w-full text-sm rounded-lg outline-hidden"
									placeholder="https://generativelanguage.googleapis.com"
									bind:value={config.gemini.GEMINI_API_BASE_URL}
									style="padding: 10px 14px; border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
									required
								/>
							</div>

							<!-- API Key -->
							<div>
								<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
									{$i18n.t('API Key')} <span style="color: #ef4444;">*</span>
								</label>
								<SensitiveInput
									placeholder="AIzaSy..."
									bind:value={config.gemini.GEMINI_API_KEY}
									style="padding: 10px 14px; border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb; border-radius: 8px;"
								/>
							</div>
						</div>
					</div>
				{/if}
			</div>

			{#if config?.enabled}
				<hr class=" border-gray-100 dark:border-gray-850" />

				<div style="border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; padding: 16px;">
					<div class="text-sm font-semibold mb-4" style="color: #1f2937;">{$i18n.t('Default Settings')}</div>

					<div class="space-y-4" style="gap: 16px;">
						<!-- Set Default Model -->
						<div>
							<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
								{$i18n.t('Default Model')}
							</label>
							<input
								list="model-list"
								class="w-full rounded-lg py-2 px-4 text-sm outline-hidden"
								bind:value={imageGenerationConfig.MODEL}
								placeholder="Select a model"
								style="border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
								required
							/>

							<datalist id="model-list">
								{#each models ?? [] as model}
									<option value={model.id}>{model.name}</option>
								{/each}
							</datalist>
						</div>

						<!-- Set Image Size -->
						<div>
							<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
								{$i18n.t('Image Size')}
							</label>
							<input
								class="w-full rounded-lg py-2 px-4 text-sm outline-hidden"
								placeholder="512x512"
								bind:value={imageGenerationConfig.IMAGE_SIZE}
								style="border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
								required
							/>
						</div>

						<!-- Set Steps -->
						<div>
							<label class="block text-xs font-medium mb-2" style="color: #6b7280;">
								{$i18n.t('Steps')}
							</label>
							<input
								class="w-full rounded-lg py-2 px-4 text-sm outline-hidden"
								placeholder="50"
								bind:value={imageGenerationConfig.IMAGE_STEPS}
								style="border: 1px solid rgba(0, 0, 0, 0.1); background: #f9fafb;"
								required
							/>
						</div>
					</div>
				</div>
			{/if}
		{/if}
	</div>

	<div class="flex justify-end text-sm font-medium" style="border-top: 1px solid rgba(0,0,0,0.08); padding-top: 16px;">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-orange-600 hover:bg-orange-700 active:bg-orange-800 text-white transition rounded-lg shadow-md hover:shadow-lg"
			type="submit"
			disabled={loading}
		>
			{$i18n.t('Save')}

			{#if loading}
				<div class="ml-2 self-center">
					<svg
						class=" w-4 h-4"
						viewBox="0 0 24 24"
						fill="currentColor"
						xmlns="http://www.w3.org/2000/svg"
						><style>
							.spinner_ajPY {
								transform-origin: center;
								animation: spinner_AtaB 0.75s infinite linear;
							}
							@keyframes spinner_AtaB {
								100% {
									transform: rotate(360deg);
								}
							}
						</style><path
							d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z"
							opacity=".25"
						/><path
							d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z"
							class="spinner_ajPY"
						/></svg
					>
				</div>
			{/if}
		</button>
	</div>
</form>
