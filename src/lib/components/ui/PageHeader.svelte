<script>
  export let title;
  export let subtitle = '';
</script>

<div class="page-header mb-8">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{title}</h1>
      {#if subtitle}
        <p class="mt-1 text-gray-600 dark:text-gray-400">{subtitle}</p>
      {/if}
    </div>
    
    {#if $$slots.actions}
      <div class="flex-shrink-0">
        <slot name="actions" />
      </div>
    {/if}
  </div>
</div> 