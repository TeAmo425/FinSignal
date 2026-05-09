<template>
  <div :style="barStyle">
    <div style="display:flex; align-items:center; gap:12px; flex:1; min-width:0;">
      <div style="width:8px; height:8px; border-radius:50%; flex-shrink:0;" :style="{ background: store.running ? 'var(--warning)' : store.ticker ? 'var(--success)' : 'var(--txt-3)', boxShadow: store.running ? '0 0 6px var(--warning)' : 'none', animation: store.running ? 'pulse-soft 1.5s ease-in-out infinite' : 'none' }"></div>

      <span style="font-size:12px; font-weight:600; color:var(--txt-2); flex-shrink:0;">AI Analysis</span>

      <template v-if="store.ticker">
        <span style="font-size:12px; font-weight:700; color:var(--primary); flex-shrink:0;">{{ store.ticker }}</span>
        <span v-if="decision" :class="['badge', decisionBadgeClass]" style="flex-shrink:0;">{{ decision }}</span>
      </template>

      <span v-if="store.statusMsg" style="font-size:11px; color:var(--txt-3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
        {{ store.statusMsg }}
      </span>

      <span v-if="store.error" style="font-size:11px; color:var(--error); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
        {{ store.error }}
      </span>
    </div>

    <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
      <template v-if="store.running">
        <div class="spinner"></div>
        <button @click="() => stop()" style="background:var(--error-dim); border:1px solid var(--error); color:var(--error); padding:4px 10px; border-radius:6px; cursor:pointer; font-size:11px; font-weight:500;">Stop</button>
      </template>
      <RouterLink v-if="store.ticker" to="/trading-agents" style="font-size:11px; color:var(--primary-txt); text-decoration:none; padding:4px 10px; background:var(--primary-dim); border-radius:6px;">View Results</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useTradingAgentStore } from '../../stores/tradingAgent'
import { useTradingAgent } from '../../composables/useTradingAgent'

const store = useTradingAgentStore()
const { stop } = useTradingAgent()

const barStyle = {
  position: 'fixed' as const,
  bottom: '0',
  right: '0',
  left: '240px',
  height: '52px',
  background: 'var(--bg-surface)',
  borderTop: '1px solid var(--border)',
  display: 'flex',
  alignItems: 'center',
  padding: '0 20px',
  gap: '12px',
  zIndex: '90',
}

const decision = computed(() => {
  const r = store.results.find(r => r.field === 'decision' || r.agent === 'portfolio_manager')
  if (!r) return null
  const m = r.content.match(/\b(BUY|SELL|HOLD)\b/i)
  return m ? m[0].toUpperCase() : null
})

const decisionBadgeClass = computed(() => {
  switch (decision.value) {
    case 'BUY':  return 'badge-buy'
    case 'SELL': return 'badge-sell'
    case 'HOLD': return 'badge-hold'
    default:     return 'badge-neutral'
  }
})
</script>
