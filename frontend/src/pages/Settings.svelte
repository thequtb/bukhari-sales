<script>
  import Header from '../components/Header.svelte';
  import SettingsPanel from '../components/SettingsPanel.svelte';
</script>

<div class="page">
  <Header title="Настройки" subtitle="Конфигурация AI-ассистента и вебхука Instagram" />
  <SettingsPanel />
</div>

<style>
.page{flex:1;display:flex;flex-direction:column;min-width:0}
</style>
