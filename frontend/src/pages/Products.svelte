<script>
  import { onMount } from 'svelte';
  import Header from '../components/Header.svelte';
  import ProductForm from '../components/ProductForm.svelte';
  import { products } from '../lib/stores.js';
  import { addNotification } from '../lib/stores.js';
  import { fetchProducts, createProduct, updateProduct, deleteProduct } from '../lib/api.js';

  let showForm = false;
  let editProduct = null;
  let prefillCategory = null;  // for adding variant to existing category

  onMount(async () => {
    try { const p = await fetchProducts(); products.set(p); }
    catch (e) { console.error(e); }
  });

  // Group by category
  $: groups = (() => {
    const g = {};
    for (const p of $products) {
      const key = p.category || p.name;
      if (!g[key]) g[key] = { description: p.description, items: [] };
      g[key].items.push(p);
    }
    return g;
  })();

  function openAdd(category = null) {
    editProduct = null;
    prefillCategory = category;
    showForm = true;
  }

  function openEdit(p) { editProduct = p; prefillCategory = null; showForm = true; }

  async function handleSave(e) {
    const data = e.detail;
    try {
      if (editProduct) {
        const updated = await updateProduct(editProduct.id, data);
        products.update(list => list.map(p => p.id === updated.id ? updated : p));
        addNotification('Товар обновлён!', 'success');
      } else {
        const created = await createProduct(data);
        products.update(list => [created, ...list]);
        addNotification('Товар добавлен!', 'success');
      }
      showForm = false;
    } catch (e) { addNotification('Ошибка: ' + e.message, 'error'); }
  }

  async function handleDelete(p) {
    if (!confirm(`Удалить вариант "${p.variant_name || p.name}"?`)) return;
    try {
      await deleteProduct(p.id);
      products.update(list => list.filter(x => x.id !== p.id));
      addNotification('Вариант удалён', 'success');
    } catch (e) { addNotification('Ошибка: ' + e.message, 'error'); }
  }
</script>

<div class="page">
  <Header title="Товары" subtitle="Каталог товаров и вариантов для AI-ассистента">
    <button class="btn btn-primary" on:click={() => openAdd()}>➕ Добавить товар</button>
  </Header>

  <div class="products-content">
    {#if $products.length === 0}
      <div class="empty-state">
        <span class="icon">🛍️</span>
        <p>Товаров пока нет. Добавьте первый товар, чтобы начать!</p>
        <button class="btn btn-primary" style="margin-top:var(--space-md)" on:click={() => openAdd()}>Добавить товар</button>
      </div>
    {:else}
      {#each Object.entries(groups) as [catName, group]}
        <div class="category-block glass">
          <div class="category-header">
            <div class="category-info">
              <h3 class="category-name">{catName}</h3>
              {#if group.description}
                <p class="category-desc">{group.description}</p>
              {/if}
            </div>
            <button class="btn btn-secondary btn-sm" on:click={() => openAdd(catName)}>
              ➕ Вариант
            </button>
          </div>

          <div class="variants-table">
            <div class="variants-header">
              <span>Вариант</span>
              <span>Цена</span>
              <span>Наличие</span>
              <span>ID</span>
              <span></span>
            </div>
            {#each group.items as v}
              <div class="variant-row">
                <span class="variant-name">{v.variant_name || v.name}</span>
                <span class="variant-price">{v.price.toLocaleString('ru-RU')} ₸</span>
                <span class="badge {v.in_stock ? 'badge-stock' : 'badge-out'} badge-sm">
                  {v.in_stock ? 'В наличии' : 'Нет'}
                </span>
                <span class="variant-id">#{v.id}</span>
                <span class="variant-actions">
                  <button class="btn btn-ghost btn-sm" on:click={() => openEdit(v)}>✏️</button>
                  <button class="btn btn-ghost btn-sm" on:click={() => handleDelete(v)}>🗑️</button>
                </span>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <ProductForm
    visible={showForm}
    product={editProduct}
    defaultCategory={prefillCategory}
    on:save={handleSave}
    on:close={() => showForm = false}
  />
</div>

<style>
  .page { flex: 1; display: flex; flex-direction: column; min-width: 0; }
  .products-content { flex: 1; padding: var(--space-xl); overflow-y: auto; display: flex; flex-direction: column; gap: var(--space-lg); }

  .category-block { padding: var(--space-lg); animation: fadeIn 0.4s ease forwards; }

  .category-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--space-md);
    margin-bottom: var(--space-md);
    padding-bottom: var(--space-md);
    border-bottom: 1px solid var(--border-subtle);
  }

  .category-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 4px;
  }

  .category-desc {
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.5;
    max-width: 600px;
  }

  .variants-table { display: flex; flex-direction: column; gap: 2px; }

  .variants-header {
    display: grid;
    grid-template-columns: 1fr 140px 110px 60px 80px;
    padding: 6px 10px;
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .variant-row {
    display: grid;
    grid-template-columns: 1fr 140px 110px 60px 80px;
    align-items: center;
    padding: 10px;
    border-radius: var(--radius-md);
    transition: background var(--transition-fast);
  }

  .variant-row:hover { background: var(--bg-glass); }

  .variant-name { font-weight: 500; font-size: 0.875rem; }

  .variant-price {
    font-weight: 700;
    background: var(--gradient-warm);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .variant-id { font-size: 0.75rem; color: var(--text-muted); font-family: monospace; }

  .variant-actions { display: flex; gap: 4px; justify-content: flex-end; }

  .badge-sm { font-size: 0.7rem !important; padding: 2px 8px !important; }
</style>
