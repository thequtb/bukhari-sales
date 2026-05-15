/**
 * API client for Bukhari Sales backend.
 */

const API_BASE = '/api';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ── Conversations ──────────────────────────────────────────────────────────

export async function fetchConversations() {
  return request('/conversations');
}

export async function fetchConversation(id) {
  return request(`/conversations/${id}`);
}

export async function fetchStats() {
  return request('/conversations/stats');
}

export async function sendManualReply(conversationId, content) {
  return request(`/conversations/${conversationId}/reply`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

// ── Telegram ───────────────────────────────────────────────────────────────

export async function fetchTelegramConversations() {
  return request('/telegram/conversations');
}

export async function fetchTelegramConversation(id) {
  return request(`/telegram/conversations/${id}`);
}

// ── Products ───────────────────────────────────────────────────────────────

export async function fetchProducts() {
  return request('/products');
}

export async function createProduct(data) {
  return request('/products', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProduct(id, data) {
  return request(`/products/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteProduct(id) {
  return request(`/products/${id}`, { method: 'DELETE' });
}

// ── Settings ───────────────────────────────────────────────────────────────

export async function fetchSettings() {
  return request('/settings');
}

export async function updateSettings(data) {
  return request('/settings', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function fetchWebhookInfo() {
  return request('/settings/webhook-info');
}

// ── WebSocket ──────────────────────────────────────────────────────────────

export function connectWebSocket(onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  let ws;
  let reconnectTimer;

  function connect() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[WS] Connected');
      // Ping every 30s to keep alive
      ws._pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      if (event.data === 'pong') return;
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.warn('[WS] Invalid message:', event.data);
      }
    };

    ws.onclose = () => {
      console.log('[WS] Disconnected, reconnecting in 3s...');
      clearInterval(ws._pingInterval);
      reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error('[WS] Error:', err);
      ws.close();
    };
  }

  connect();

  return {
    close() {
      clearTimeout(reconnectTimer);
      clearInterval(ws?._pingInterval);
      ws?.close();
    },
  };
}
