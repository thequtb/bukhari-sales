<script>
  export let title = '';
  export let subtitle = '';
</script>

<header class="page-header">
  <div class="header-content">
    <h2 class="header-title">{title}</h2>
    {#if subtitle}
      <p class="header-subtitle">{subtitle}</p>
    {/if}
  </div>
  <slot />
</header>

<style>
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--space-lg) var(--space-xl);
    border-bottom: 1px solid var(--border-subtle);
    background: rgba(18, 18, 26, 0.5);
    backdrop-filter: blur(8px);
    position: sticky;
    top: 0;
    z-index: 50;
  }

  .header-title {
    font-size: 1.4rem;
    font-weight: 700;
    background: var(--gradient-purple);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-subtitle {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 2px;
  }
</style>
