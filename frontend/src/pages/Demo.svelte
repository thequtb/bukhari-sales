<script>
  import Header from '../components/Header.svelte';
  import { addNotification } from '../lib/stores.js';

  let messages = [];
  let inputText = '';
  let sending = false;
  let chatContainer;

  $: if (messages.length && chatContainer) {
    setTimeout(() => { chatContainer.scrollTop = chatContainer.scrollHeight; }, 50);
  }

  function formatTime() {
    return new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  }

  async function sendMessage() {
    if (!inputText.trim() || sending) return;
    const text = inputText.trim();
    inputText = '';

    messages = [...messages, { sender: 'user', content: text, time: formatTime() }];
    sending = true;
    messages = [...messages, { sender: 'typing', content: '', time: '' }];

    try {
      const res = await fetch('/api/demo/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      messages = messages.filter(m => m.sender !== 'typing');
      messages = [...messages, { sender: 'bot', content: data.bot_reply, time: formatTime() }];
    } catch (e) {
      messages = messages.filter(m => m.sender !== 'typing');
      messages = [...messages, { sender: 'error', content: `Ошибка: ${e.message}`, time: formatTime() }];
      addNotification('Не удалось получить ответ AI: ' + e.message, 'error');
    } finally {
      sending = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  async function resetChat() {
    try {
      await fetch('/api/demo/reset', { method: 'POST' });
      messages = [];
      addNotification('Беседа сброшена!', 'success');
    } catch (e) {
      addNotification('Ошибка сброса: ' + e.message, 'error');
    }
  }

  // Quick suggestions in both KZ and RU
  const suggestions = [
    { text: 'Какие у вас товары?', label: 'RU' },
    { text: 'Сізде қандай тауарлар бар?', label: 'KZ' },
    { text: 'Какая цена на духи?', label: 'RU' },
    { text: 'Жеткізу бар ма?', label: 'KZ' },
  ];
</script>

<div class="page">
  <Header title="Демо-чат" subtitle="Тест AI-ассистента без подключения Instagram">
    <button class="btn btn-secondary" on:click={resetChat}>🔄 Сбросить чат</button>
  </Header>

  <div class="demo-layout">
    <!-- Phone mockup -->
    <div class="phone-frame">
      <div class="phone-header">
        <div class="phone-avatar"><span>B</span></div>
        <div class="phone-user">
          <span class="phone-name">Bukhari Sales</span>
          <span class="phone-status">🤖 AI-ассистент · Онлайн</span>
        </div>
      </div>

      <div class="phone-messages" bind:this={chatContainer}>
        {#if messages.length === 0}
          <div class="welcome-msg">
            <div class="welcome-icon">💬</div>
            <h3>Тестируйте AI-бота по продажам</h3>
            <p>Напишите сообщение на русском или казахском — бот ответит на том же языке.</p>
            <div class="suggestions">
              {#each suggestions as s}
                <button class="suggestion" on:click={() => { inputText = s.text; sendMessage(); }}>
                  <span class="lang-tag">{s.label}</span>
                  {s.text}
                </button>
              {/each}
            </div>
          </div>
        {/if}

        {#each messages as msg, i}
          {#if msg.sender === 'typing'}
            <div class="message bot">
              <div class="msg-bubble bot-bubble">
                <div class="typing-indicator">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
            </div>
          {:else if msg.sender === 'error'}
            <div class="message bot">
              <div class="msg-bubble error-bubble"><p>{msg.content}</p></div>
            </div>
          {:else}
            <div class="message {msg.sender}" style="animation-delay: {Math.min(i * 0.05, 0.3)}s">
              <div class="msg-bubble {msg.sender}-bubble">
                <p>{msg.content}</p>
                <span class="msg-time">{msg.time}</span>
              </div>
            </div>
          {/if}
        {/each}
      </div>

      <div class="phone-input">
        <textarea
          class="chat-input"
          placeholder="Введите сообщение... / Хабарлама жіберіңіз..."
          bind:value={inputText}
          on:keydown={handleKeydown}
          disabled={sending}
          rows="1"
        ></textarea>
        <button
          class="send-btn"
          on:click={sendMessage}
          disabled={!inputText.trim() || sending}
        >{sending ? '⏳' : '📤'}</button>
      </div>
    </div>

    <!-- Info panel -->
    <div class="info-panel glass">
      <h3>🧪 Демо-режим</h3>
      <p>Полная симуляция работы Instagram Direct без подключения к Meta:</p>
      <ol>
        <li>Ваше сообщение сохраняется как «входящий Direct»</li>
        <li>LangChain формирует контекст: история + каталог товаров</li>
        <li>OpenAI генерирует ответ на языке клиента (RU / KZ)</li>
        <li>Ответ сохраняется и отображается в чате</li>
      </ol>

      <div class="info-section">
        <h4>🌐 Двуязычный режим:</h4>
        <p>Пишите по-русски — бот отвечает по-русски.<br/>Казахша жазсаңыз — қазақша жауап береді.</p>
      </div>

      <div class="info-section">
        <h4>💡 Попробуйте спросить:</h4>
        <ul>
          <li>О наличии и цене товара</li>
          <li>О доставке и оплате</li>
          <li>Помощь в выборе</li>
          <li>Оформление заказа</li>
        </ul>
      </div>

      <div class="info-section">
        <h4>⚙️ Кастомизация:</h4>
        <p>Раздел <strong>Товары</strong> — добавьте свои позиции в каталог.<br/>Раздел <strong>Настройки</strong> — измените промпт или модель AI.</p>
      </div>
    </div>
  </div>
</div>

<style>
  .page { flex: 1; display: flex; flex-direction: column; min-width: 0; }

  .demo-layout {
    flex: 1;
    display: flex;
    gap: var(--space-xl);
    padding: var(--space-xl);
    align-items: flex-start;
    justify-content: center;
    overflow-y: auto;
  }

  .phone-frame {
    width: 420px;
    min-width: 420px;
    height: calc(100vh - 160px);
    max-height: 700px;
    display: flex;
    flex-direction: column;
    background: var(--bg-secondary);
    border: 1px solid var(--border-glass);
    border-radius: var(--radius-xl);
    overflow: hidden;
    box-shadow: var(--shadow-lg), 0 0 60px rgba(168, 85, 247, 0.08);
  }

  .phone-header {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    padding: var(--space-md) var(--space-lg);
    background: rgba(10, 10, 15, 0.8);
    border-bottom: 1px solid var(--border-subtle);
  }

  .phone-avatar {
    width: 38px; height: 38px; border-radius: 50%;
    background: var(--gradient-instagram);
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1rem; color: white;
  }

  .phone-name { display: block; font-size: 0.9rem; font-weight: 700; }
  .phone-status { font-size: 0.7rem; color: var(--accent-green); font-weight: 500; }

  .phone-messages {
    flex: 1; overflow-y: auto; padding: var(--space-lg);
    display: flex; flex-direction: column; gap: var(--space-sm);
  }

  .welcome-msg { text-align: center; padding: var(--space-xl) var(--space-md); animation: fadeIn 0.5s ease; }
  .welcome-icon { font-size: 3rem; margin-bottom: var(--space-md); }
  .welcome-msg h3 {
    font-size: 1rem; font-weight: 700; margin-bottom: var(--space-sm);
    background: var(--gradient-purple);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .welcome-msg p { font-size: 0.82rem; color: var(--text-secondary); margin-bottom: var(--space-lg); line-height: 1.5; }

  .suggestions { display: flex; flex-direction: column; gap: var(--space-sm); }

  .suggestion {
    display: flex; align-items: center; gap: var(--space-sm);
    padding: 10px 14px;
    background: var(--bg-glass);
    border: 1px solid var(--border-glass);
    border-radius: var(--radius-full);
    color: var(--text-primary);
    font-family: var(--font-family);
    font-size: 0.8rem;
    cursor: pointer;
    transition: all var(--transition-fast);
    text-align: left;
  }
  .suggestion:hover { background: rgba(168, 85, 247, 0.1); border-color: var(--border-active); }

  .lang-tag {
    font-size: 0.6rem; font-weight: 700;
    padding: 2px 5px;
    border-radius: var(--radius-full);
    background: rgba(168, 85, 247, 0.2);
    color: var(--accent-purple);
    flex-shrink: 0;
  }

  .message { display: flex; animation: fadeIn 0.3s ease forwards; opacity: 0; }
  .message.user { justify-content: flex-end; }
  .message.bot { justify-content: flex-start; }

  .msg-bubble { max-width: 80%; padding: 10px 14px; border-radius: var(--radius-lg); font-size: 0.875rem; line-height: 1.5; }
  .user-bubble { background: var(--gradient-purple); color: white; border-bottom-right-radius: 4px; }
  .bot-bubble { background: var(--bg-card); border: 1px solid var(--border-subtle); color: var(--text-primary); border-bottom-left-radius: 4px; }
  .error-bubble { background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.3); color: var(--accent-red); border-bottom-left-radius: 4px; }
  .msg-bubble p { white-space: pre-wrap; word-wrap: break-word; margin: 0; }
  .msg-time { display: block; font-size: 0.6rem; opacity: 0.6; margin-top: 4px; text-align: right; }

  .typing-indicator { display: flex; gap: 4px; padding: 4px 2px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-muted); animation: bounce 1.4s infinite ease-in-out; }
  .dot:nth-child(1){animation-delay:0s}.dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}

  @keyframes bounce { 0%,80%,100%{transform:scale(.6);opacity:.4} 40%{transform:scale(1);opacity:1} }

  .phone-input {
    display: flex; align-items: flex-end; gap: var(--space-sm);
    padding: var(--space-md); border-top: 1px solid var(--border-subtle);
    background: rgba(10,10,15,.5);
  }

  .chat-input {
    flex: 1; padding: 10px 14px;
    background: var(--bg-input); border: 1px solid var(--border-subtle);
    border-radius: var(--radius-full); color: var(--text-primary);
    font-family: var(--font-family); font-size: 0.875rem; outline: none;
    resize: none; min-height: 40px; max-height: 100px;
    transition: border-color var(--transition-fast);
  }
  .chat-input:focus { border-color: var(--accent-purple); }
  .chat-input::placeholder { color: var(--text-muted); }

  .send-btn {
    width: 40px; height: 40px; border: none; border-radius: 50%;
    background: var(--gradient-purple); color: white; font-size: 1rem;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: all var(--transition-fast); flex-shrink: 0;
  }
  .send-btn:hover:not(:disabled) { transform: scale(1.05); box-shadow: var(--shadow-glow-purple); }
  .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .info-panel { width: 320px; padding: var(--space-lg); position: sticky; top: var(--space-xl); animation: fadeIn 0.5s ease 0.2s forwards; opacity: 0; }
  .info-panel h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: var(--space-sm); }
  .info-panel > p { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: var(--space-md); }
  .info-panel ol, .info-panel ul { padding-left: var(--space-lg); margin-bottom: var(--space-md); }
  .info-panel li { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6; }
  .info-section { margin-top: var(--space-lg); padding-top: var(--space-md); border-top: 1px solid var(--border-subtle); }
  .info-section h4 { font-size: 0.85rem; font-weight: 700; color: var(--text-primary); margin-bottom: var(--space-sm); }
  .info-section p { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; }

  @media (max-width: 900px) {
    .demo-layout { flex-direction: column; align-items: center; }
    .info-panel { width: 100%; max-width: 420px; position: static; }
    .phone-frame { min-width: 0; width: 100%; max-width: 420px; }
  }
</style>
