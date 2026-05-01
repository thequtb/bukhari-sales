<script>
  import { onMount } from 'svelte';
  import Header from '../components/Header.svelte';
  import { addNotification } from '../lib/stores.js';

  let orders = [];
  let loading = true;

  const statusLabel = {
    pending: 'Ожидает',
    confirmed: 'Подтверждён',
    completed: 'Выполнен',
    cancelled: 'Отменён',
  };

  const statusClass = {
    pending: 'badge-pending',
    confirmed: 'badge-active',
    completed: 'badge-stock',
    cancelled: 'badge-out',
  };

  onMount(async () => {
    await loadOrders();
  });

  async function loadOrders() {
    loading = true;
    try {
      const res = await fetch('/api/orders');
      orders = await res.json();
    } catch (e) {
      addNotification('Ошибка загрузки заказов: ' + e.message, 'error');
    } finally {
      loading = false;
    }
  }

  async function updateStatus(orderId, status) {
    try {
      const res = await fetch(`/api/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const updated = await res.json();
      orders = orders.map(o => o.id === updated.id ? updated : o);
      addNotification(`Статус заказа #${orderId} обновлён`, 'success');
    } catch (e) {
      addNotification('Ошибка обновления: ' + e.message, 'error');
    }
  }

  function formatDate(str) {
    if (!str) return '—';
    return new Date(str).toLocaleString('ru-RU', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }
</script>

<div class="page">
  <Header title="Заказы" subtitle="Заказы, оформленные AI-ассистентом в переписке" />

  <div class="orders-content">
    {#if loading}
      <div class="empty-state"><span class="icon">⏳</span><p>Загрузка...</p></div>
    {:else if orders.length === 0}
      <div class="empty-state">
        <span class="icon">📋</span>
        <p>Заказов пока нет. Они появятся здесь после того, как клиент подтвердит покупку в чате.</p>
      </div>
    {:else}
      <div class="orders-table glass">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Клиент</th>
              <th>Контакт</th>
              <th>Товар</th>
              <th>Вариант</th>
              <th>Сумма</th>
              <th>Статус</th>
              <th>Дата</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {#each orders as order (order.id)}
              <tr class="order-row" style="animation-delay: {orders.indexOf(order) * 0.04}s">
                <td class="order-id">#{order.id}</td>
                <td>
                  <div class="customer-info">
                    <span class="customer-name">{order.customer_name || '—'}</span>
                    {#if order.username}
                      <span class="customer-ig">@{order.username}</span>
                    {/if}
                  </div>
                </td>
                <td class="contact">{order.customer_contact || '—'}</td>
                <td class="product-name">{order.product?.name || '—'}</td>
                <td class="variant-name">{order.product?.variant_name || '—'}</td>
                <td class="price">
                  {#if order.product}
                    {order.product.price.toLocaleString('ru-RU')} ₸
                  {:else}—{/if}
                </td>
                <td>
                  <span class="badge {statusClass[order.status] || ''}">
                    {statusLabel[order.status] || order.status}
                  </span>
                </td>
                <td class="date">{formatDate(order.created_at)}</td>
                <td class="actions">
                  {#if order.status === 'confirmed'}
                    <button class="btn btn-ghost btn-sm" on:click={() => updateStatus(order.id, 'completed')}>✅</button>
                    <button class="btn btn-ghost btn-sm" on:click={() => updateStatus(order.id, 'cancelled')}>❌</button>
                  {:else if order.status === 'pending'}
                    <button class="btn btn-ghost btn-sm" on:click={() => updateStatus(order.id, 'confirmed')}>✔️</button>
                    <button class="btn btn-ghost btn-sm" on:click={() => updateStatus(order.id, 'cancelled')}>❌</button>
                  {:else}
                    <span class="closed-label">—</span>
                  {/if}
                </td>
              </tr>
              {#if order.notes}
                <tr class="notes-row">
                  <td colspan="9"><span class="notes-label">Примечание:</span> {order.notes}</td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>

<style>
  .page { flex: 1; display: flex; flex-direction: column; min-width: 0; }
  .orders-content { flex: 1; padding: var(--space-xl); overflow: auto; }

  .orders-table {
    overflow-x: auto;
    border-radius: var(--radius-lg);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }

  thead tr {
    background: rgba(168, 85, 247, 0.06);
    border-bottom: 1px solid var(--border-subtle);
  }

  th {
    padding: 12px 14px;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    text-align: left;
    white-space: nowrap;
  }

  .order-row {
    border-bottom: 1px solid var(--border-subtle);
    transition: background var(--transition-fast);
    animation: fadeIn 0.3s ease forwards;
    opacity: 0;
  }

  .order-row:hover { background: var(--bg-glass); }

  td {
    padding: 12px 14px;
    vertical-align: middle;
  }

  .order-id { font-weight: 700; color: var(--accent-purple); }

  .customer-info { display: flex; flex-direction: column; gap: 2px; }
  .customer-name { font-weight: 600; color: var(--text-primary); }
  .customer-ig { font-size: 0.72rem; color: var(--text-muted); }

  .contact { font-family: monospace; font-size: 0.8rem; }
  .product-name { font-weight: 600; }
  .variant-name { color: var(--text-secondary); font-size: 0.8rem; }

  .price {
    font-weight: 700;
    background: var(--gradient-warm);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    white-space: nowrap;
  }

  .date { color: var(--text-muted); font-size: 0.78rem; white-space: nowrap; }

  .actions { display: flex; gap: 4px; }
  .closed-label { color: var(--text-muted); font-size: 0.75rem; }

  .notes-row td {
    padding: 4px 14px 10px 14px;
    font-size: 0.78rem;
    color: var(--text-secondary);
    background: rgba(168, 85, 247, 0.03);
  }

  .notes-label { font-weight: 600; color: var(--text-muted); }

  /* Custom badge colours */
  :global(.badge-pending) {
    background: rgba(234, 179, 8, 0.15) !important;
    color: #eab308 !important;
  }
</style>
