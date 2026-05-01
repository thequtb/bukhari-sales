<script>
  import { aiConfig, webhookInfo, addNotification as notify } from '../lib/stores.js';
  import { fetchSettings, updateSettings, fetchWebhookInfo } from '../lib/api.js';
  import { onMount } from 'svelte';

  let saving = false;
  let resetting = false;
  let localConfig = { system_prompt: '', temperature: 0.7, model_name: 'gpt-4o-mini', max_tokens: 500 };

  onMount(async () => {
    try {
      const [settings, wh] = await Promise.all([fetchSettings(), fetchWebhookInfo()]);
      aiConfig.set(settings);
      webhookInfo.set(wh);
      localConfig = { ...settings };
    } catch (e) { console.error(e); }
  });

  async function handleSave() {
    saving = true;
    try {
      const updated = await updateSettings({
        system_prompt: localConfig.system_prompt,
        temperature: localConfig.temperature,
        model_name: localConfig.model_name,
        max_tokens: localConfig.max_tokens,
      });
      aiConfig.set(updated);
      localConfig = { ...updated };
      notify('Настройки сохранены!', 'success');
    } catch (e) { notify('Ошибка сохранения: ' + e.message, 'error'); }
    finally { saving = false; }
  }

  async function handleResetPrompt() {
    if (!confirm('Сбросить системный промпт к значению по умолчанию?')) return;
    resetting = true;
    try {
      const res = await fetch('/api/settings/reset-prompt', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const updated = await res.json();
      aiConfig.set(updated);
      localConfig = { ...updated };
      notify('Промпт сброшен к значению по умолчанию!', 'success');
    } catch (e) { notify('Ошибка сброса: ' + e.message, 'error'); }
    finally { resetting = false; }
  }
</script>

<div class="settings-grid">
  <!-- Вебхук -->
  <div class="settings-section glass">
    <h3>🔗 Конфигурация вебхука</h3>
    <p class="section-desc">Укажите эти данные в Meta Developer Dashboard</p>
    {#if $webhookInfo}
      <div class="info-row"><span class="info-label">URL вебхука</span><code class="info-value">{$webhookInfo.webhook_url}</code></div>
      <div class="info-row"><span class="info-label">Токен верификации</span><code class="info-value">{$webhookInfo.verify_token}</code></div>
      <div class="info-row"><span class="info-label">ID страницы</span>
        <span class="info-value">{$webhookInfo.page_id_configured ? $webhookInfo.page_id : '⚠️ Не настроен'}</span>
      </div>
      <div class="info-row"><span class="info-label">Токен доступа</span>
        <span class="info-value">{$webhookInfo.token_configured ? '✅ Настроен' : '⚠️ Не настроен'}</span>
      </div>
    {/if}
  </div>

  <!-- AI Конфигурация -->
  <div class="settings-section glass">
    <h3>🤖 Настройки AI</h3>
    <p class="section-desc">Настройте поведение AI-ассистента по продажам</p>
    <div class="fg">
      <label class="label" for="model">Модель</label>
      <select id="model" class="input" bind:value={localConfig.model_name}>
        <option value="gpt-4o-mini">GPT-4o Mini (Быстрая)</option>
        <option value="gpt-4o">GPT-4o (Лучшая)</option>
        <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Экономная)</option>
      </select>
    </div>
    <div class="fg">
      <label class="label" for="temp-slider">Температура: {localConfig.temperature.toFixed(1)}</label>
      <input id="temp-slider" type="range" min="0" max="2" step="0.1" bind:value={localConfig.temperature} class="slider" />
      <div class="slider-labels"><span>Точно</span><span>Творчески</span></div>
    </div>
    <div class="fg">
      <label class="label" for="maxtokens">Макс. токенов</label>
      <input id="maxtokens" class="input" type="number" min="50" max="4096" bind:value={localConfig.max_tokens} />
    </div>
    <div class="fg">
      <label class="label" for="sysprompt">Системный промпт</label>
      <textarea id="sysprompt" class="input prompt-editor" bind:value={localConfig.system_prompt} rows="12"></textarea>
    </div>
    <div class="btn-row">
      <button class="btn btn-primary" on:click={handleSave} disabled={saving}>{saving ? 'Сохранение...' : '💾 Сохранить'}</button>
      <button class="btn btn-secondary" on:click={handleResetPrompt} disabled={resetting}>{resetting ? '...' : '↺ Сбросить промпт'}</button>
    </div>
  </div>
</div>

<style>
.settings-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-lg);padding:var(--space-xl);max-width:1200px}
.settings-section{padding:var(--space-lg)}
.settings-section h3{font-size:1.1rem;font-weight:700;margin-bottom:var(--space-xs)}
.section-desc{font-size:.8rem;color:var(--text-muted);margin-bottom:var(--space-lg)}
.info-row{display:flex;justify-content:space-between;align-items:center;padding:var(--space-sm) 0;border-bottom:1px solid var(--border-subtle)}
.info-label{font-size:.8rem;font-weight:600;color:var(--text-secondary)}
.info-value{font-size:.8rem;color:var(--text-primary);font-family:monospace;word-break:break-all}
code.info-value{background:var(--bg-input);padding:2px 8px;border-radius:var(--radius-sm)}
.fg{margin-bottom:var(--space-md)}
.slider{width:100%;height:6px;appearance:none;background:var(--bg-input);border-radius:var(--radius-full);outline:none;cursor:pointer}
.slider::-webkit-slider-thumb{appearance:none;width:18px;height:18px;border-radius:50%;background:var(--accent-purple);cursor:pointer;box-shadow:var(--shadow-glow-purple)}
.slider-labels{display:flex;justify-content:space-between;font-size:.7rem;color:var(--text-muted);margin-top:4px}
.prompt-editor{min-height:200px;font-family:monospace;font-size:.8rem;line-height:1.6}
.btn-row{display:flex;gap:var(--space-sm);flex-wrap:wrap}
@media(max-width:900px){.settings-grid{grid-template-columns:1fr}}
</style>
