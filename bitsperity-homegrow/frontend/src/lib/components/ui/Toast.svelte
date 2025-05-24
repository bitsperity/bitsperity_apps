<script>
	import { onMount } from 'svelte';
	import { CheckCircle, AlertCircle, X, Info } from 'lucide-svelte';

	let toasts = [];
	let nextId = 1;

	// Toast types and their styling
	const toastTypes = {
		success: {
			icon: CheckCircle,
			bgClass: 'bg-green-50 border-green-200',
			iconClass: 'text-green-600',
			textClass: 'text-green-800'
		},
		error: {
			icon: AlertCircle,
			bgClass: 'bg-red-50 border-red-200',
			iconClass: 'text-red-600',
			textClass: 'text-red-800'
		},
		warning: {
			icon: AlertCircle,
			bgClass: 'bg-yellow-50 border-yellow-200',
			iconClass: 'text-yellow-600',
			textClass: 'text-yellow-800'
		},
		info: {
			icon: Info,
			bgClass: 'bg-blue-50 border-blue-200',
			iconClass: 'text-blue-600',
			textClass: 'text-blue-800'
		}
	};

	function addToast(type, message, duration = 5000) {
		const id = nextId++;
		const toast = { id, type, message, duration };
		
		toasts = [...toasts, toast];

		// Auto-remove after duration
		if (duration > 0) {
			setTimeout(() => {
				removeToast(id);
			}, duration);
		}

		return id;
	}

	function removeToast(id) {
		toasts = toasts.filter(toast => toast.id !== id);
	}

	// Global toast functions
	function success(message, duration) {
		return addToast('success', message, duration);
	}

	function error(message, duration) {
		return addToast('error', message, duration);
	}

	function warning(message, duration) {
		return addToast('warning', message, duration);
	}

	function info(message, duration) {
		return addToast('info', message, duration);
	}

	// Make toast functions globally available
	onMount(() => {
		if (typeof window !== 'undefined') {
			window.toast = { success, error, warning, info };
		}
	});
</script>

<!-- Toast Container -->
<div class="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
	{#each toasts as toast (toast.id)}
		<div 
			class="pointer-events-auto max-w-sm w-full rounded-lg border shadow-lg animate-slide-up"
			class:bg-green-50={toast.type === 'success'}
			class:border-green-200={toast.type === 'success'}
			class:bg-red-50={toast.type === 'error'}
			class:border-red-200={toast.type === 'error'}
			class:bg-yellow-50={toast.type === 'warning'}
			class:border-yellow-200={toast.type === 'warning'}
			class:bg-blue-50={toast.type === 'info'}
			class:border-blue-200={toast.type === 'info'}
		>
			<div class="p-4">
				<div class="flex items-start">
					<div class="flex-shrink-0">
						<svelte:component 
							this={toastTypes[toast.type].icon} 
							size={20}
							class={toastTypes[toast.type].iconClass}
						/>
					</div>
					<div class="ml-3 w-0 flex-1 pt-0.5">
						<p class="text-sm font-medium {toastTypes[toast.type].textClass}">
							{toast.message}
						</p>
					</div>
					<div class="ml-4 flex-shrink-0 flex">
						<button
							class="rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none"
							on:click={() => removeToast(toast.id)}
						>
							<X size={16} />
						</button>
					</div>
				</div>
			</div>
		</div>
	{/each}
</div> 