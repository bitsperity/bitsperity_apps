<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	// Navigation Items mit natürlichen Hydroponic Icons
	const navItems = [
		{
			path: '/',
			icon: '🌱',
			label: 'Garten',
			description: 'Dashboard'
		},
		{
			path: '/devices',
			icon: '🔧',
			label: 'Geräte',
			description: 'Steuerung'
		},
		{
			path: '/monitoring',
			icon: '📊',
			label: 'Monitor',
			description: 'Überwachung'
		},
		{
			path: '/rules',
			icon: '🌿',
			label: 'Regeln',
			description: 'Automation'
		},
		{
			path: '/settings',
			icon: '⚙️',
			label: 'Settings',
			description: 'Einstellungen'
		}
	];

	function handleNavigation(path) {
		goto(path);
	}

	$: currentPath = $page.url.pathname;
</script>

<!-- Bottom Navigation mit natürlichem Design -->
<nav class="fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-gray-900/95 backdrop-blur-lg border-t border-green-200/30 dark:border-green-800/30 safe-area-bottom">
	<!-- Natürlicher Verlauf -->
	<div class="absolute inset-0 bg-gradient-to-t from-green-50/20 to-transparent dark:from-green-900/20"></div>
	
	<div class="relative grid grid-cols-5 h-16">
		{#each navItems as item}
			<button
				on:click={() => handleNavigation(item.path)}
				class="flex flex-col items-center justify-center px-2 py-2 transition-all duration-200 group relative
					{currentPath === item.path 
						? 'text-green-600 dark:text-green-400' 
						: 'text-gray-500 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400'
					}"
			>
				<!-- Active Indicator - Natürliche Form -->
				{#if currentPath === item.path}
					<div class="absolute -top-0.5 left-1/2 -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-green-400 to-green-600 rounded-full"></div>
				{/if}
				
				<!-- Icon mit natürlicher Animation -->
				<div class="text-lg mb-1 transform transition-all duration-200 
					{currentPath === item.path ? 'scale-110' : 'group-hover:scale-105'}"
				>
					{item.icon}
				</div>
				
				<!-- Label -->
				<span class="text-xs font-medium leading-tight">
					{item.label}
				</span>
				
				<!-- Hover Effect - Subtle Glow -->
				<div class="absolute inset-0 rounded-lg bg-green-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
			</button>
		{/each}
	</div>
	
	<!-- Safe Area Bottom Padding -->
	<div class="h-safe-bottom"></div>
</nav>

<style>
	.safe-area-bottom {
		padding-bottom: env(safe-area-inset-bottom);
	}
	
	.h-safe-bottom {
		height: env(safe-area-inset-bottom);
	}
</style> 