<script>
  import { conversations, activeConversation } from '../lib/stores.js';
  import { fetchConversation } from '../lib/api.js';

  export let onSelect = null;

  let searchQuery = '';

  $: filtered = $conversations.filter(c => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (c.username || '').toLowerCase().includes(q) ||
           (c.last_message || '').toLowerCase().includes(q);
  });

  const statusLabel = { active: 'Активна', expired: 'Истекла', closed: 'Закрыта' };

  function timeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'только что';
    if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`;
    return `${Math.floor(diff / 86400)} д назад`;
  }

  async function selectConversation(conv) {
    try {
      const detail = await fetchConversation(conv.id);
      activeConversation.set(detail);
      if (onSelect) onSelect(detail);
    } catch (e) {
      console.error('Failed to load conversation:', e);
    }
  }
</script>

<div class="conversation-list">
  <div class="search-wrapper">
    <input
      class="input search-input"
      type="text"
      placeholder="Поиск бесед..."
      bind:value={searchQuery}
    />
    <span class="search-icon">🔍</span>
  </div>

  <div class="list-scroll">
    {#if filtered.length === 0}
      <div class="empty-state">
        <span class="icon">💬</span>
        <p>{searchQuery ? 'Беседы не найдены' : 'Бесед пока нет'}</p>
      </div>
    {:else}
      {#each filtered as conv, i}
        <button
          class="conv-item"
          class:active={$activeConversation?.id === conv.id}
          on:click={() => selectConversation(conv)}
          style="animation-delay: {i * 0.05}s"
        >
          <div class="conv-avatar">
            {#if conv.profile_pic_url}
              <img src={conv.profile_pic_url} alt="" />
            {:else}
              <span>{(conv.username || 'К')[0].toUpperCase()}</span>
            {/if}
          </div>
          <div class="conv-info">
            <div class="conv-header">
              <span class="conv-name">{conv.username || 'Клиент Instagram'}</span>
              <span class="conv-time">{timeAgo(conv.last_message_at)}</span>
            </div>
            <p class="conv-preview">{conv.last_message || 'Нет сообщений'}</p>
          </div>
          <span class="badge badge-{conv.status}">{statusLabel[conv.status] || conv.status}</span>
        </button>
      {/each}
    {/if}
  </div>
</div>

<style>
  .conversation-list {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 340px;
    min-width: 340px;
    border-right: 1px solid var(--border-subtle);
    background: rgba(15, 15, 23, 0.5);
  }

  .search-wrapper {
    position: relative;
    padding: var(--space-md);
  }

  .search-input {
    padding-left: 36px;
  }

  .search-icon {
    position: absolute;
    left: 26px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.85rem;
    opacity: 0.5;
  }

  .list-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 0 var(--space-sm);
  }

  .conv-item {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    width: 100%;
    padding: var(--space-md);
    border: none;
    border-radius: var(--radius-md);
    background: transparent;
    cursor: pointer;
    transition: all var(--transition-fast);
    text-align: left;
    animation: fadeIn 0.3s ease forwards;
    opacity: 0;
    color: inherit;
    font-family: var(--font-family);
  }

  .conv-item:hover { background: var(--bg-glass); }
  .conv-item.active {
    background: rgba(168, 85, 247, 0.08);
    border: 1px solid var(--border-active);
  }

  .conv-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: var(--gradient-instagram);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
    font-weight: 700;
    font-size: 1rem;
    color: white;
  }

  .conv-avatar img { width: 100%; height: 100%; object-fit: cover; }

  .conv-info { flex: 1; min-width: 0; }

  .conv-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-sm);
  }

  .conv-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .conv-time { font-size: 0.7rem; color: var(--text-muted); white-space: nowrap; }

  .conv-preview {
    font-size: 0.8rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
  }
</style>
