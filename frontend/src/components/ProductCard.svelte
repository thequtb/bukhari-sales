<script>
  export let product = {};
  export let onEdit = null;
  export let onDelete = null;
</script>

<div class="product-card glass">
  <div class="product-image">
    {#if product.image_url}
      <img src={product.image_url} alt={product.name} />
    {:else}
      <div class="image-placeholder"><span>🛍️</span></div>
    {/if}
    <span class="badge {product.in_stock ? 'badge-stock' : 'badge-out'}">
      {product.in_stock ? 'В наличии' : 'Нет в наличии'}
    </span>
  </div>

  <div class="product-body">
    {#if product.category}
      <span class="product-category">{product.category}</span>
    {/if}
    <h3 class="product-name">{product.name}</h3>
    {#if product.description}
      <p class="product-desc">{product.description}</p>
    {/if}
    <div class="product-footer">
      <span class="product-price">{product.price?.toLocaleString('ru-RU')} ₸</span>
      <div class="product-actions">
        {#if onEdit}
          <button class="btn btn-ghost btn-sm" on:click={() => onEdit(product)}>✏️ Изменить</button>
        {/if}
        {#if onDelete}
          <button class="btn btn-ghost btn-sm" on:click={() => onDelete(product)}>🗑️</button>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  .product-card{display:flex;flex-direction:column;overflow:hidden;transition:all var(--transition-smooth);animation:fadeIn .5s ease forwards}
  .product-card:hover{transform:translateY(-3px);box-shadow:var(--shadow-lg);border-color:var(--border-active)}
  .product-image{position:relative;width:100%;height:180px;overflow:hidden;background:var(--bg-input)}
  .product-image img{width:100%;height:100%;object-fit:cover;transition:transform var(--transition-smooth)}
  .product-card:hover .product-image img{transform:scale(1.05)}
  .image-placeholder{width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:3rem;opacity:.3;background:var(--gradient-glass)}
  .product-image .badge{position:absolute;top:var(--space-sm);right:var(--space-sm)}
  .product-body{padding:var(--space-md);display:flex;flex-direction:column;flex:1}
  .product-category{font-size:.7rem;font-weight:600;color:var(--accent-purple);text-transform:uppercase;letter-spacing:.5px;margin-bottom:var(--space-xs)}
  .product-name{font-size:1rem;font-weight:700;color:var(--text-primary);margin-bottom:var(--space-xs)}
  .product-desc{font-size:.8rem;color:var(--text-secondary);line-height:1.4;flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .product-footer{display:flex;align-items:center;justify-content:space-between;margin-top:var(--space-md);padding-top:var(--space-md);border-top:1px solid var(--border-subtle)}
  .product-price{font-size:1.1rem;font-weight:800;background:var(--gradient-warm);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
  .product-actions{display:flex;gap:var(--space-xs)}
</style>
