/**
 * Svelte stores for Bukhari Sales app state.
 */

import { writable, derived } from 'svelte/store';

// Current page / route
export const currentPage = writable('demo');

// Conversations
export const conversations = writable([]);
export const activeConversation = writable(null);

// Products
export const products = writable([]);

// Settings
export const aiConfig = writable(null);
export const webhookInfo = writable(null);

// Dashboard stats
export const stats = writable({
  total_conversations: 0,
  active_conversations: 0,
  total_messages: 0,
  messages_today: 0,
  bot_messages: 0,
  user_messages: 0,
});

// Real-time activity feed
export const activityFeed = writable([]);

// Loading states
export const loading = writable({
  conversations: false,
  products: false,
  settings: false,
  stats: false,
});

// Notifications / toasts
export const notifications = writable([]);

export function addNotification(message, type = 'info') {
  const id = Date.now();
  notifications.update(n => [...n, { id, message, type }]);
  setTimeout(() => {
    notifications.update(n => n.filter(item => item.id !== id));
  }, 4000);
}

// Derived: active conversation count
export const activeCount = derived(conversations, ($conversations) =>
  $conversations.filter(c => c.status === 'active').length
);
