<script>
  import { onMount } from 'svelte';
  import Header from '../components/Header.svelte';
  import StatsCard from '../components/StatsCard.svelte';
  import { stats, activityFeed, conversations } from '../lib/stores.js';
  import { fetchStats, fetchConversations } from '../lib/api.js';

  onMount(async () => {
    try {
      const [s, c] = await Promise.all([fetchStats(), fetchConversations()]);
      stats.set(s);
      conversations.set(c);
    } catch (e) { console.error('Dashboard load error:', e); }
  });

  const statusLabel = { active: 'Активна', expired: 'Истекла', closed: 'Закрыта' };
</script>

<div class="page">
  <Header title="Панель управления" subtitle="Обзор работы Instagram AI-ассистента по продажам" />

  <div class="dashboard-content">
    <div class="stats-grid">
      <StatsCard icon="💬" label="Всего бесед" value={$stats.total_conversations} gradient="purple" />
      <StatsCard icon="⚡" label="Активных сейчас" value={$stats.active_conversations} gradient="cool" />
      <StatsCard icon="📩" label="Сообщений сегодня" value={$stats.messages_today} gradient="warm" />
      <StatsCard icon="🤖" label="Ответов AI" value={$stats.bot_messages} gradient="success" />
    </div>

    <div class="dashboard-panels">
      <div class="panel glass">
        <h3 class="panel-title">📊 Статистика сообщений</h3>
        <div class="breakdown-bars">
          <div class="bar-item">
            <div class="bar-label"><span>Сообщения клиентов</span><span>{$stats.user_messages}</span></div>
            <div class="bar-track"><div class="bar-fill user" style="width: {$stats.total_messages ? ($stats.user_messages / $stats.total_messages * 100) : 0}%"></div></div>
          </div>
          <div class="bar-item">
            <div class="bar-label"><span>Ответы AI</span><span>{$stats.bot_messages}</span></div>
            <div class="bar-track"><div class="bar-fill bot" style="width: {$stats.total_messages ? ($stats.bot_messages / $stats.total_messages * 100) : 0}%"></div></div>
          </div>
        </div>
        <div class="total-stat">Всего сообщений: <strong>{$stats.total_messages}</strong></div>
      </div>

      <div class="panel glass">
        <h3 class="panel-title">🕐 Последние беседы</h3>
        <div class="recent-list">
          {#if $conversations.length === 0}
            <p class="no-data">Беседы пока отсутствуют. Ожидайте первых сообщений!</p>
          {:else}
            {#each $conversations.slice(0, 5) as conv}
              <div class="recent-item">
                <div class="recent-avatar">{(conv.username || 'К')[0].toUpperCase()}</div>
                <div class="recent-info">
                  <span class="recent-name">{conv.username || 'Клиент'}</span>
                  <span class="recent-preview">{conv.last_message || 'Нет сообщений'}</span>
                </div>
                <span class="badge badge-{conv.status}">{statusLabel[conv.status] || conv.status}</span>
              </div>
            {/each}
          {/if}
        </div>
      </div>
    </div>
  </div>
</div>

<style>
.page{flex:1;display:flex;flex-direction:column;min-width:0}
.dashboard-content{padding:var(--space-xl);overflow-y:auto;flex:1}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:var(--space-md);margin-bottom:var(--space-xl)}
.dashboard-panels{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-lg)}
.panel{padding:var(--space-lg)}
.panel-title{font-size:1rem;font-weight:700;margin-bottom:var(--space-lg);color:var(--text-primary)}
.breakdown-bars{display:flex;flex-direction:column;gap:var(--space-md)}
.bar-item{display:flex;flex-direction:column;gap:4px}
.bar-label{display:flex;justify-content:space-between;font-size:.8rem;color:var(--text-secondary)}
.bar-label span:last-child{font-weight:700;color:var(--text-primary)}
.bar-track{height:8px;background:var(--bg-input);border-radius:var(--radius-full);overflow:hidden}
.bar-fill{height:100%;border-radius:var(--radius-full);transition:width 1s ease}
.bar-fill.user{background:var(--gradient-warm)}
.bar-fill.bot{background:var(--gradient-purple)}
.total-stat{margin-top:var(--space-lg);font-size:.85rem;color:var(--text-secondary);text-align:center}
.total-stat strong{color:var(--text-primary)}
.recent-list{display:flex;flex-direction:column;gap:var(--space-sm)}
.recent-item{display:flex;align-items:center;gap:var(--space-md);padding:var(--space-sm);border-radius:var(--radius-md);transition:background var(--transition-fast)}
.recent-item:hover{background:var(--bg-glass)}
.recent-avatar{width:36px;height:36px;border-radius:50%;background:var(--gradient-instagram);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;color:white;flex-shrink:0}
.recent-info{flex:1;min-width:0}
.recent-name{display:block;font-size:.85rem;font-weight:600}
.recent-preview{display:block;font-size:.75rem;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.no-data{font-size:.85rem;color:var(--text-muted);text-align:center;padding:var(--space-lg)}
@media(max-width:900px){.dashboard-panels{grid-template-columns:1fr}}
</style>
