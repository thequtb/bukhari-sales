<script>
  import { onMount, onDestroy } from 'svelte';
  import Sidebar from './components/Sidebar.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import Conversations from './pages/Conversations.svelte';
  import Products from './pages/Products.svelte';
  import Settings from './pages/Settings.svelte';
  import Demo from './pages/Demo.svelte';
  import Orders from './pages/Orders.svelte';
  import { currentPage, notifications, conversations, activityFeed } from './lib/stores.js';
  import { connectWebSocket } from './lib/api.js';

  let ws;

  onMount(() => {
    ws = connectWebSocket((data) => {
      if (data.type === 'new_message') {
        activityFeed.update(f => [data, ...f].slice(0, 50));
        // Refresh conversations list
        conversations.update(list => {
          const idx = list.findIndex(c => c.id === data.conversation_id);
          if (idx >= 0) {
            const updated = { ...list[idx], last_message: data.content };
            return [updated, ...list.filter((_, i) => i !== idx)];
          }
          return list;
        });
      }
    });
  });

  onDestroy(() => { ws?.close(); });

  $: page = $currentPage;
</script>

<Sidebar />

<main class="main-content">
  {#if page === 'dashboard'}
    <Dashboard />
  {:else if page === 'conversations'}
    <Conversations />
  {:else if page === 'products'}
    <Products />
  {:else if page === 'settings'}
    <Settings />
  {:else if page === 'demo'}
    <Demo />
  {:else if page === 'orders'}
    <Orders />
  {/if}
</main>

<!-- Notifications Toast -->
{#each $notifications as notif (notif.id)}
  <div class="toast toast-{notif.type}">
    <span>{notif.type === 'success' ? '✅' : notif.type === 'error' ? '❌' : 'ℹ️'}</span>
    <span>{notif.message}</span>
  </div>
{/each}

<style>
  .main-content {
    flex: 1;
    display: flex;
    min-width: 0;
    min-height: 100vh;
  }

  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    border-radius: var(--radius-md);
    font-size: 0.85rem;
    font-weight: 500;
    color: white;
    z-index: 9999;
    animation: fadeIn 0.3s ease, fadeIn 0.3s ease 3.5s reverse forwards;
    box-shadow: var(--shadow-lg);
  }

  .toast-success {
    background: linear-gradient(135deg, #10b981, #059669);
  }

  .toast-error {
    background: linear-gradient(135deg, #ef4444, #dc2626);
  }

  .toast-info {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
  }
</style>
