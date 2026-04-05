<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		// Set mode to signup and redirect to auth page
		sessionStorage.setItem('authMode', 'signup');
		goto('/auth');
	});
</script>

<div class="flex items-center justify-center w-full h-screen">
	<div class="text-center">
		<div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
		<p class="mt-4 text-gray-600 dark:text-gray-300">Redirecting to registration...</p>
	</div>
</div>
