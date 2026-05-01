<script>
  import { activeConversation } from '../lib/stores.js';
  import { sendManualReply } from '../lib/api.js';
  import { addNotification } from '../lib/stores.js';

  let replyText = '';
  let sending = false;
  let chatContainer;

  $: conv = $activeConversation;
  $: if (conv && chatContainer) {
    setTimeout(() => { chatContainer.scrollTop = chatContainer.scrollHeight; }, 50);
  }

  const statusLabel = { active: 'Активна', expired: 'Истекла', closed: 'Закрыта' };

  function formatTime(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  }

  async function handleSendReply() {
    if (!replyText.trim() || !conv || sending) return;
    sending = true;
    try {
      await sendManualReply(conv.id, replyText.trim());
      activeConversation.update(c => ({
        ...c,
        messages: [...c.messages, {
          id: Date.now(),
          sender: 'operator',
          content: replyText.trim(),
          timestamp: new Date().toISOString(),
        }],
      }));
      replyText = '';
      addNotification('Ответ отправлен!', 'success');
    } catch (e) {
      addNotification(`Ошибка отправки: ${e.message}`, 'error');
    } finally {
      sending = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendReply(); }
  }
</script>

<div class="chat-view">
  {#if !conv}
    <div class="empty-state" style="flex: 1;">
      <span class="icon">💬</span>
      <p>Выберите беседу для просмотра сообщений</p>
    </div>
  {:else}
    <div class="chat-header">
      <div class="chat-user">
        <div class="chat-avatar">
          {#if conv.profile_pic_url}
            <img src={conv.profile_pic_url} alt="" />
          {:else}
            <span>{(conv.username || 'К')[0].toUpperCase()}</span>
          {/if}
        </div>
        <div>
          <h3>{conv.username || 'Клиент Instagram'}</h3>
          <span class="chat-meta">
            <span class="badge badge-{conv.status}">{statusLabel[conv.status] || conv.status}</span>
            {#if conv.is_within_window}
              <span class="window-active">⏱️ Окно открыто</span>
            {:else}
              <span class="window-expired">⏱️ Окно истекло</span>
            {/if}
          </span>
        </div>
      </div>
      <div class="chat-actions">
        <span class="msg-count">{conv.messages?.length || 0} сообщений</span>
      </div>
    </div>

    <div class="chat-messages" bind:this={chatContainer}>
      {#each conv.messages || [] as msg, i}
        <div
          class="message"
          class:outgoing={msg.sender === 'bot' || msg.sender === 'operator'}
          class:incoming={msg.sender === 'user'}
          style="animation-delay: {Math.min(i * 0.03, 0.5)}s"
        >
          <div class="msg-bubble">
            {#if msg.sender === 'operator'}
              <span class="operator-badge">👤 Оператор</span>
            {:else if msg.sender === 'bot'}
              <span class="bot-badge">🤖 AI</span>
            {/if}
            <p>{msg.content}</p>
            <span class="msg-time">{formatTime(msg.timestamp)}</span>
          </div>
        </div>
      {/each}
    </div>

    {#if conv.is_within_window}
      <div class="chat-input">
        <textarea
          class="input reply-input"
          placeholder="Написать ответ вручную..."
          bind:value={replyText}
          on:keydown={handleKeydown}
          disabled={sending}
          rows="1"
        ></textarea>
        <button
          class="btn btn-primary send-btn"
          on:click={handleSendReply}
          disabled={!replyText.trim() || sending}
        >
          {sending ? '⏳' : '📤'} Отправить
        </button>
      </div>
    {:else}
      <div class="window-notice">
        <span>⚠️ 24-часовое окно ответа для этой беседы истекло.</span>
      </div>
    {/if}
  {/if}
</div>

<style>
  .chat-view{flex:1;display:flex;flex-direction:column;min-width:0}
  .chat-header{display:flex;align-items:center;justify-content:space-between;padding:var(--space-md) var(--space-lg);border-bottom:1px solid var(--border-subtle);background:rgba(18,18,26,.5)}
  .chat-user{display:flex;align-items:center;gap:var(--space-md)}
  .chat-avatar{width:40px;height:40px;border-radius:50%;background:var(--gradient-instagram);display:flex;align-items:center;justify-content:center;overflow:hidden;font-weight:700;color:white}
  .chat-avatar img{width:100%;height:100%;object-fit:cover}
  .chat-user h3{font-size:.95rem;font-weight:600}
  .chat-meta{display:flex;align-items:center;gap:var(--space-sm);font-size:.75rem;margin-top:2px}
  .window-active{color:var(--accent-green);font-weight:500}
  .window-expired{color:var(--accent-red);font-weight:500}
  .msg-count{font-size:.8rem;color:var(--text-muted)}
  .chat-messages{flex:1;overflow-y:auto;padding:var(--space-lg);display:flex;flex-direction:column;gap:var(--space-sm)}
  .message{display:flex;animation:fadeIn .3s ease forwards;opacity:0}
  .message.incoming{justify-content:flex-start}
  .message.outgoing{justify-content:flex-end}
  .msg-bubble{max-width:70%;padding:var(--space-md);border-radius:var(--radius-lg);position:relative}
  .incoming .msg-bubble{background:var(--bg-card);border:1px solid var(--border-subtle);border-bottom-left-radius:var(--space-xs)}
  .outgoing .msg-bubble{background:rgba(168,85,247,.12);border:1px solid rgba(168,85,247,.2);border-bottom-right-radius:var(--space-xs)}
  .msg-bubble p{font-size:.875rem;line-height:1.5;white-space:pre-wrap;word-wrap:break-word}
  .msg-time{display:block;font-size:.65rem;color:var(--text-muted);margin-top:var(--space-xs);text-align:right}
  .bot-badge,.operator-badge{display:inline-block;font-size:.65rem;font-weight:600;padding:1px 6px;border-radius:var(--radius-full);margin-bottom:var(--space-xs)}
  .bot-badge{background:rgba(168,85,247,.15);color:var(--accent-purple)}
  .operator-badge{background:rgba(59,130,246,.15);color:var(--accent-blue)}
  .chat-input{display:flex;align-items:flex-end;gap:var(--space-sm);padding:var(--space-md) var(--space-lg);border-top:1px solid var(--border-subtle);background:rgba(18,18,26,.5)}
  .reply-input{flex:1;min-height:42px;max-height:120px;resize:none}
  .send-btn{height:42px;white-space:nowrap}
  .window-notice{padding:var(--space-md) var(--space-lg);text-align:center;color:var(--accent-red);font-size:.85rem;border-top:1px solid var(--border-subtle);background:rgba(239,68,68,.05)}
</style>
