<script>
  import { currentPage, activeCount } from '../lib/stores.js';

  const navItems = [
    { id: 'demo', label: 'Демо-чат', icon: '🧪' },
    { id: 'dashboard', label: 'Панель управления', icon: '📊' },
    { id: 'conversations', label: 'Беседы', icon: '💬' },
    { id: 'orders', label: 'Заказы', icon: '📋' },
    { id: 'products', label: 'Товары', icon: '🛍️' },
    { id: 'settings', label: 'Настройки', icon: '⚙️' },
  ];

  $: activePage = $currentPage;
</script>

<aside class="sidebar">
  <div class="sidebar-header">
    <div class="logo">
      <div class="logo-icon">
        <span class="logo-gradient">B</span>
      </div>
      <div class="logo-text">
        <h1>Bukhari</h1>
        <span class="logo-sub">Продажи AI</span>
      </div>
    </div>
  </div>

  <nav class="sidebar-nav">
    {#each navItems as item}
      <button
        class="nav-item"
        class:active={activePage === item.id}
        on:click={() => currentPage.set(item.id)}
      >
        <span class="nav-icon">{item.icon}</span>
        <span class="nav-label">{item.label}</span>
        {#if item.id === 'conversations' && $activeCount > 0}
          <span class="nav-badge">{$activeCount}</span>
        {/if}
      </button>
    {/each}
  </nav>

  <div class="sidebar-footer">
    <div class="status-indicator">
      <span class="status-dot"></span>
      <span class="status-text">AI-агент активен</span>
    </div>
  </div>
</aside>

<style>
  .sidebar {
    width: var(--sidebar-width);
    min-width: var(--sidebar-width);
    height: 100vh;
    position: sticky;
    top: 0;
    display: flex;
    flex-direction: column;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-subtle);
    padding: var(--space-lg) var(--space-md);
    z-index: 100;
  }

  .sidebar-header {
    margin-bottom: var(--space-xl);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: var(--space-md);
  }

  .logo-icon {
    width: 42px;
    height: 42px;
    border-radius: var(--radius-md);
    background: var(--gradient-instagram);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-glow-purple);
  }

  .logo-gradient {
    font-size: 1.3rem;
    font-weight: 800;
    color: white;
  }

  .logo-text h1 {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
  }

  .logo-sub {
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .sidebar-nav {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    padding: 11px 14px;
    border: none;
    border-radius: var(--radius-md);
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-family);
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-normal);
    position: relative;
    text-align: left;
    width: 100%;
  }

  .nav-item:hover {
    background: var(--bg-glass);
    color: var(--text-primary);
  }

  .nav-item.active {
    background: rgba(168, 85, 247, 0.1);
    color: var(--accent-purple);
  }

  .nav-item.active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 60%;
    background: var(--gradient-purple);
    border-radius: var(--radius-full);
  }

  .nav-icon {
    font-size: 1.1rem;
    width: 24px;
    text-align: center;
  }

  .nav-badge {
    margin-left: auto;
    background: var(--gradient-warm);
    color: white;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: var(--radius-full);
    min-width: 18px;
    text-align: center;
  }

  .sidebar-footer {
    padding-top: var(--space-md);
    border-top: 1px solid var(--border-subtle);
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-sm);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent-green);
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
    animation: pulse 2s infinite;
  }

  .status-text {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 500;
  }
</style>
