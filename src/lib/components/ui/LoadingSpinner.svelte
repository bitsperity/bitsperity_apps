<script>
  export let size = 'medium'; // 'small', 'medium', 'large'
  export let color = 'primary'; // 'primary', 'white', 'gray'
  
  $: sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-6 h-6', 
    large: 'w-8 h-8'
  };
  
  $: colorClasses = {
    primary: 'border-primary-200 border-t-primary-500',
    white: 'border-white/20 border-t-white',
    gray: 'border-gray-200 border-t-gray-500'
  };
</script>

<div 
  class="spinner {sizeClasses[size]} {colorClasses[color]} border-2 border-solid rounded-full animate-spin"
  role="status"
  aria-label="Loading"
>
  <span class="sr-only">Loading...</span>
</div>

<style>
  .spinner {
    border-top-style: solid;
  }
</style> 