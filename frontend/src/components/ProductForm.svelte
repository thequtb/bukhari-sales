<script>
  import { createEventDispatcher } from 'svelte';
  export let product = null;
  export let visible = false;
  export let defaultCategory = null;

  const dispatch = createEventDispatcher();

  let form = emptyForm();

  function emptyForm() {
    return {
      name: defaultCategory || '',
      variant_name: '',
      description: '',
      price: 0,
      currency: 'KZT',
      image_url: '',
      category: defaultCategory || '',
      in_stock: true,
    };
  }

  $: if (visible && product) {
    form = {
      name: product.name || '',
      variant_name: product.variant_name || '',
      description: product.description || '',
      price: product.price || 0,
      currency: product.currency || 'KZT',
      image_url: product.image_url || '',
      category: product.category || '',
      in_stock: product.in_stock ?? true,
    };
  }

  $: if (visible && !product) {
    form = {
      name: defaultCategory || '',
      variant_name: '',
      description: '',
      price: 0,
      currency: 'KZT',
      image_url: '',
      category: defaultCategory || '',
      in_stock: true,
    };
  }

  // Keep name and category in sync when both are empty
  function syncNameCategory() {
    if (!product && !defaultCategory) form.category = form.name;
  }

  function handleSubmit() {
    if (!form.name || form.price < 0) return;
    dispatch('save', { ...form });
  }

  function handleClose() { dispatch('close'); }
</script>

{#if visible}
<div class="modal-overlay" on:click|self={handleClose} role="dialog" aria-modal="true">
  <div class="modal">
    <h2>{product ? '✏️ Редактировать вариант' : '🛍️ Добавить товар / вариант'}</h2>
    <form on:submit|preventDefault={handleSubmit}>

      <div class="fr">
        <div class="fg">
          <label class="label" for="pcat">Категория (название товара) *</label>
          <input id="pcat" class="input" bind:value={form.name} on:input={syncNameCategory}
            placeholder="напр. Курсы Таджвида" required />
          <span class="hint">Товары с одинаковой категорией группируются</span>
        </div>
        <div class="fg">
          <label class="label" for="pvar">Название варианта</label>
          <input id="pvar" class="input" bind:value={form.variant_name}
            placeholder="напр. Полный курс" />
        </div>
      </div>

      <div class="fg">
        <label class="label" for="pd">Описание категории</label>
        <textarea id="pd" class="input" bind:value={form.description} rows="3"
          placeholder="Общее описание для всех вариантов этого товара..."></textarea>
        <span class="hint">Одно описание отображается для всей категории</span>
      </div>

      <div class="fr">
        <div class="fg">
          <label class="label" for="pp">Цена (₸) *</label>
          <input id="pp" class="input" type="number" step="1" min="0"
            bind:value={form.price} required />
        </div>
        <div class="fg">
          <label class="label" for="pc">Валюта</label>
          <select id="pc" class="input" bind:value={form.currency}>
            <option value="KZT">KZT (₸)</option>
          </select>
        </div>
      </div>

      <div class="fg">
        <label class="label" for="pi">URL изображения</label>
        <input id="pi" class="input" type="url" bind:value={form.image_url}
          placeholder="https://..." />
      </div>

      <div class="fg">
        <label class="tl">
          <input type="checkbox" bind:checked={form.in_stock} />
          <span>Есть в наличии</span>
        </label>
      </div>

      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" on:click={handleClose}>Отмена</button>
        <button type="submit" class="btn btn-primary">
          {product ? 'Сохранить' : 'Добавить'}
        </button>
      </div>
    </form>
  </div>
</div>
{/if}

<style>
  .fg { margin-bottom: var(--space-md); }
  .fr { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); }
  .hint { display: block; font-size: 0.72rem; color: var(--text-muted); margin-top: 3px; }
  select.input { appearance: none; cursor: pointer; }
  .tl { display: flex; align-items: center; gap: var(--space-sm); cursor: pointer; font-size: .875rem; }
  .tl input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent-purple); }
</style>
