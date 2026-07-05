<template>
  <section class="dashboard-panel">
    <header class="dashboard-panel__header">
      <h2 class="panel-title">{{ title }}</h2>
      <span v-if="meta" class="panel-meta">{{ meta }}</span>
    </header>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  meta: { type: String, default: '' }
})
</script>
