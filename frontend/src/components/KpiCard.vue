<template>
  <article class="kpi-card">
    <span class="kpi-card__label">{{ label }}</span>
    <strong class="kpi-card__value">{{ value }}</strong>
    <small class="kpi-card__hint">{{ hint }}</small>
  </article>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  hint: { type: String, default: '' }
})
</script>
