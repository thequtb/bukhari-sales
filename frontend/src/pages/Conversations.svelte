<script>
  import { onMount } from 'svelte';
  import Header from '../components/Header.svelte';
  import ConversationList from '../components/ConversationList.svelte';
  import ChatView from '../components/ChatView.svelte';
  import { conversations } from '../lib/stores.js';
  import { fetchConversations } from '../lib/api.js';

  onMount(async () => {
    try { const c = await fetchConversations(); conversations.set(c); }
    catch (e) { console.error(e); }
  });
</script>

<div class="page">
  <Header title="Беседы" subtitle="Управление перепиской в Instagram Direct" />
  <div class="conv-layout">
    <ConversationList />
    <ChatView />
  </div>
</div>

<style>
.page{flex:1;display:flex;flex-direction:column;min-width:0}
.conv-layout{flex:1;display:flex;overflow:hidden}
</style>
