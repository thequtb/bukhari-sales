<script>
  import { onMount } from 'svelte';
  import Header from '../components/Header.svelte';
  import { fetchTelegramConversations, fetchTelegramConversation } from '../lib/api.js';

  let conversations = [];
  let selectedConv = null;
  let loading = true;
  let chatLoading = false;
  let searchQuery = '';

  onMount(async () => {
    await loadConversations();
  });

  async function loadConversations() {
    try {
      loading = true;
      conversations = await fetchTelegramConversations();
    } catch (e) {
      console.error('Failed to load Telegram conversations:', e);
    } finally {
      loading = false;
    }
  }

  async function selectConversation(conv) {
    if (selectedConv?.id === conv.id) return;
    chatLoading = true;
    selectedConv = null;
    try {
      selectedConv = await fetchTelegramConversation(conv.id);
    } catch (e) {
      console.error('Failed to load conversation:', e);
    } finally {
      chatLoading = false;
    }
  }

  function formatTime(ts) {
    if (!ts) return '';
    const d = new Date(ts);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return 'только что';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} мин назад`;
    if (diff < 86400000) return d.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });
    return d.toLocaleDateString('ru', { day: '2-digit', month: 'short' });
  }

  function formatTimeFull(ts) {
    if (!ts) return '';
    return new Date(ts).toLocaleString('ru', {
      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
    });
  }

  $: filtered = conversations.filter(c => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.full_name || '').toLowerCase().includes(q) ||
      (c.username || '').toLowerCase().includes(q) ||
      (c.last_message || '').toLowerCase().includes(q)
    );
  });

  function getInitials(conv) {
    if (conv.full_name) return conv.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    if (conv.username) return conv.username.slice(0, 2).toUpperCase();
    return 'TG';
  }
</script>

<div class="page">
  <Header title="Telegram Беседы" subtitle="Чаты с клиентами через Telegram-бота" />

  <div class="conv-layout">
    <!-- Sidebar List -->
    <aside class="conv-sidebar">
      <div class="search-bar">
        <span class="search-icon">🔍</span>
        <input
          class="search-input"
          type="text"
          placeholder="Поиск по имени или сообщению..."
          bind:value={searchQuery}
        />
      </div>

      {#if loading}
        <div class="empty-state">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>
      {:else if filtered.length === 0}
        <div class="empty-state">
          <span class="empty-icon">✈️</span>
          <p>{conversations.length === 0 ? 'Пока нет бесед в Telegram' : 'Ничего не найдено'}</p>
          {#if conversations.length === 0}
            <small>Начните чат с ботом в Telegram, и беседа появится здесь</small>
          {/if}
        </div>
      {:else}
        <div class="conv-list">
          {#each filtered as conv (conv.id)}
            <button
              class="conv-item"
              class:active={selectedConv?.id === conv.id}
              on:click={() => selectConversation(conv)}
            >
              <div class="avatar" style="--hue: {(parseInt(conv.telegram_user_id) || 0) % 360}deg">
                {getInitials(conv)}
              </div>
              <div class="conv-info">
                <div class="conv-header-row">
                  <span class="conv-name">
                    {conv.full_name || conv.username || `User ${conv.telegram_user_id}`}
                  </span>
                  <span class="conv-time">{formatTime(conv.last_message_at)}</span>
                </div>
                {#if conv.username}
                  <div class="conv-handle">@{conv.username}</div>
                {/if}
                <div class="conv-preview">{conv.last_message || '—'}</div>
              </div>
              <span class="status-dot-sm" class:active={conv.status === 'active'}></span>
            </button>
          {/each}
        </div>
      {/if}
    </aside>

    <!-- Chat View -->
    <section class="chat-section">
      {#if chatLoading}
        <div class="chat-empty">
          <div class="spinner large"></div>
          <p>Загрузка переписки...</p>
        </div>
      {:else if selectedConv}
        <div class="chat-header">
          <div class="avatar" style="--hue: {(parseInt(selectedConv.telegram_user_id) || 0) % 360}deg">
            {getInitials(selectedConv)}
          </div>
          <div class="chat-header-info">
            <span class="chat-name">
              {selectedConv.full_name || selectedConv.username || `User ${selectedConv.telegram_user_id}`}
            </span>
            {#if selectedConv.username}
              <span class="chat-handle">@{selectedConv.username}</span>
            {/if}
          </div>
          <div class="chat-meta">
            <span class="meta-chip">🆔 {selectedConv.telegram_user_id}</span>
            <span class="meta-chip status-{selectedConv.status}">{selectedConv.status}</span>
          </div>
        </div>

        <div class="chat-messages">
          {#each selectedConv.messages as msg (msg.id)}
            <div class="message-row" class:bot={msg.sender === 'bot'}>
              <div class="bubble" class:bot={msg.sender === 'bot'} class:user={msg.sender === 'user'}>
                <p>{msg.content}</p>
                <span class="msg-time">{formatTimeFull(msg.timestamp)}</span>
              </div>
            </div>
          {/each}

          {#if selectedConv.messages.length === 0}
            <div class="no-messages">Нет сообщений в этой беседе</div>
          {/if}
        </div>
      {:else}
        <div class="chat-empty">
          <span class="empty-big">✈️</span>
          <h3>Выберите беседу</h3>
          <p>Нажмите на контакт слева, чтобы просмотреть переписку</p>
        </div>
      {/if}
    </section>
  </div>
</div>

<style>
  .page {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    height: 100vh;
    overflow: hidden;
  }

  .conv-layout {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  /* ── Sidebar ── */
  .conv-sidebar {
    width: 320px;
    min-width: 280px;
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border-subtle);
    background: var(--bg-secondary);
    overflow: hidden;
  }

  .search-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-subtle);
  }

  .search-icon { font-size: 0.9rem; color: var(--text-muted); }

  .search-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-primary);
    font-size: 0.85rem;
    font-family: var(--font-family);
  }

  .search-input::placeholder { color: var(--text-muted); }

  .conv-list {
    flex: 1;
    overflow-y: auto;
  }

  .conv-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    width: 100%;
    padding: 12px 16px;
    border: none;
    background: transparent;
    cursor: pointer;
    text-align: left;
    border-bottom: 1px solid var(--border-subtle);
    transition: background 0.15s;
    position: relative;
    font-family: var(--font-family);
  }

  .conv-item:hover { background: var(--bg-glass); }
  .conv-item.active { background: rgba(37, 163, 232, 0.08); border-left: 3px solid #25a3e8; }

  .avatar {
    width: 42px;
    height: 42px;
    min-width: 42px;
    border-radius: 50%;
    background: hsl(var(--hue, 200deg), 60%, 45%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    color: white;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
  }

  .conv-info { flex: 1; min-width: 0; }

  .conv-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    margin-bottom: 2px;
  }

  .conv-name {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .conv-time {
    font-size: 0.72rem;
    color: var(--text-muted);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .conv-handle {
    font-size: 0.75rem;
    color: #25a3e8;
    margin-bottom: 2px;
  }

  .conv-preview {
    font-size: 0.78rem;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-dot-sm {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--border-subtle);
    margin-top: 6px;
    flex-shrink: 0;
  }
  .status-dot-sm.active { background: var(--accent-green); box-shadow: 0 0 5px rgba(16,185,129,0.5); }

  /* ── Chat ── */
  .chat-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg-primary);
  }

  .chat-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border-subtle);
    background: var(--bg-secondary);
  }

  .chat-header-info { flex: 1; min-width: 0; }

  .chat-name {
    display: block;
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary);
  }

  .chat-handle { font-size: 0.78rem; color: #25a3e8; }

  .chat-meta { display: flex; gap: 8px; align-items: center; }

  .meta-chip {
    font-size: 0.72rem;
    padding: 3px 9px;
    border-radius: 100px;
    background: var(--bg-glass);
    color: var(--text-muted);
    border: 1px solid var(--border-subtle);
  }

  .status-active { color: var(--accent-green) !important; border-color: var(--accent-green) !important; }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .message-row {
    display: flex;
    justify-content: flex-start;
  }

  .message-row.bot { justify-content: flex-end; }

  .bubble {
    max-width: 66%;
    padding: 10px 14px;
    border-radius: 14px;
    font-size: 0.875rem;
    line-height: 1.5;
    position: relative;
  }

  .bubble p { margin: 0 0 4px; color: var(--text-primary); white-space: pre-wrap; word-break: break-word; }

  .bubble.user {
    background: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    border-bottom-left-radius: 4px;
  }

  .bubble.bot {
    background: linear-gradient(135deg, #0088cc, #25a3e8);
    border-bottom-right-radius: 4px;
  }

  .bubble.bot p { color: white; }

  .msg-time {
    display: block;
    font-size: 0.68rem;
    opacity: 0.6;
    text-align: right;
  }

  .bubble.bot .msg-time { color: rgba(255,255,255,0.8); }

  .chat-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: var(--text-muted);
    text-align: center;
    padding: 40px;
  }

  .chat-empty h3 { font-size: 1.1rem; color: var(--text-secondary); margin: 0; }
  .chat-empty p { font-size: 0.85rem; margin: 0; }

  .empty-big { font-size: 3rem; }

  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 30px 20px;
    color: var(--text-muted);
    text-align: center;
  }

  .empty-icon { font-size: 2.5rem; }
  .empty-state p { font-size: 0.85rem; margin: 0; }
  .empty-state small { font-size: 0.75rem; }

  .no-messages {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.85rem;
    padding: 40px;
  }

  .spinner {
    width: 28px;
    height: 28px;
    border: 3px solid var(--border-subtle);
    border-top-color: #25a3e8;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  .spinner.large { width: 40px; height: 40px; }

  @keyframes spin { to { transform: rotate(360deg); } }
</style>
