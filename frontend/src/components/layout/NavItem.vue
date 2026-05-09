<template>
  <RouterLink :to="to" style="text-decoration:none; display:block; margin-bottom:2px;">
    <div :style="itemStyle">
      <component :is="icon" :size="16" :color="active ? 'var(--primary)' : 'var(--txt-3)'" style="flex-shrink:0;" />
      <span :style="labelStyle">{{ label }}</span>
    </div>
  </RouterLink>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { Component } from 'vue'

const props = defineProps<{
  to: string
  icon: Component
  label: string
  active: boolean
}>()

const itemStyle = computed(() => ({
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  padding: '7px 10px',
  borderRadius: '8px',
  background: props.active ? 'var(--primary-dim)' : 'transparent',
  transition: 'background 0.15s',
  cursor: 'pointer',
}))

const labelStyle = computed(() => ({
  fontSize: '13px',
  fontWeight: props.active ? '500' : '400',
  color: props.active ? 'var(--primary-txt)' : 'var(--txt-2)',
}))
</script>
