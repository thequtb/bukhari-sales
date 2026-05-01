<script>
  export let icon = '📊';
  export let label = '';
  export let value = 0;
  export let trend = '';
  export let gradient = 'purple';

  const gradientMap = {
    purple: 'var(--gradient-purple)',
    warm: 'var(--gradient-warm)',
    cool: 'var(--gradient-cool)',
    success: 'var(--gradient-success)',
  };
</script>

<div class="stat-card glass">
  <div class="stat-icon" style="background: {gradientMap[gradient]}">
    <span>{icon}</span>
  </div>
  <div class="stat-content">
    <span class="stat-label">{label}</span>
    <span class="stat-value">{value.toLocaleString()}</span>
    {#if trend}
      <span class="stat-trend">{trend}</span>
    {/if}
  </div>
</div>

<style>
  .stat-card {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    padding: var(--space-lg);
    transition: all var(--transition-smooth);
    animation: fadeIn 0.5s ease forwards;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-active);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    flex-shrink: 0;
  }

  .stat-content {
    display: flex;
    flex-direction: column;
  }

  .stat-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.2;
    margin-top: 2px;
  }

  .stat-trend {
    font-size: 0.7rem;
    color: var(--accent-green);
    font-weight: 600;
    margin-top: 2px;
  }
</style>
