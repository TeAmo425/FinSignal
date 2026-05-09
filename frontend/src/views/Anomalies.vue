<template>
  <div style="padding:24px; max-width:1100px; margin:0 auto;">

    <!-- Header -->
    <div style="margin-bottom:24px;">
      <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Anomaly Detection</h1>
      <p style="font-size:13px; color:var(--txt-3);">Detect unusual price and volume patterns in stocks</p>
    </div>

    <!-- Controls -->
    <div class="card" style="margin-bottom:20px; padding:16px;">
      <div style="display:flex; align-items:flex-end; gap:12px;">
        <div style="flex:1; max-width:240px;">
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Symbol</label>
          <input v-model="symbol" type="text" placeholder="AAPL" class="input-base" style="width:100%; text-transform:uppercase;" @input="symbol = String(symbol).toUpperCase()" @keydown.enter="runDetection" />
        </div>
        <button @click="runDetection" class="btn-primary" :disabled="loading || !symbol">
          <span style="display:flex; align-items:center; gap:6px;">
            <div v-if="loading" class="spinner" style="border-top-color:#fff;"></div>
            <AlertTriangleIcon v-else :size="14" />
            {{ loading ? 'Detecting...' : 'Detect Anomalies' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" style="padding:12px 16px; background:var(--error-dim); border:1px solid var(--error); border-radius:10px; color:var(--error); font-size:13px; margin-bottom:20px;">
      {{ error }}
    </div>

    <template v-if="anomalyData">
      <!-- Summary -->
      <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:20px;">
        <div class="card" style="padding:14px; text-align:center;">
          <p style="font-size:11px; color:var(--txt-3); margin-bottom:4px;">Total Anomalies</p>
          <p style="font-size:22px; font-weight:700; color:var(--warning);">{{ anomalies.length }}</p>
        </div>
        <div class="card" style="padding:14px; text-align:center;">
          <p style="font-size:11px; color:var(--txt-3); margin-bottom:4px;">High Severity</p>
          <p style="font-size:22px; font-weight:700; color:var(--error);">{{ highSeverity }}</p>
        </div>
        <div class="card" style="padding:14px; text-align:center;">
          <p style="font-size:11px; color:var(--txt-3); margin-bottom:4px;">Medium</p>
          <p style="font-size:22px; font-weight:700; color:var(--warning);">{{ mediumSeverity }}</p>
        </div>
        <div class="card" style="padding:14px; text-align:center;">
          <p style="font-size:11px; color:var(--txt-3); margin-bottom:4px;">Anomaly Score</p>
          <p style="font-size:22px; font-weight:700;" :style="{ color: (anomalyData.score || 0) > 0.7 ? 'var(--error)' : (anomalyData.score || 0) > 0.4 ? 'var(--warning)' : 'var(--success)' }">
            {{ anomalyData.score ? (anomalyData.score * 100).toFixed(0) : '—' }}
          </p>
        </div>
      </div>

      <!-- Anomalies Table -->
      <div class="card">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:14px;">Detected Anomalies</h3>
        <div v-if="anomalies.length" style="overflow-x:auto;">
          <table style="width:100%; border-collapse:collapse;">
            <thead>
              <tr style="border-bottom:1px solid var(--border);">
                <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Date</th>
                <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Type</th>
                <th style="text-align:right; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Score</th>
                <th style="text-align:right; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Price</th>
                <th style="text-align:right; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Change</th>
                <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Severity</th>
                <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Description</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="a in anomalies"
                :key="a.date + a.type"
                style="border-bottom:1px solid var(--border);"
                @mouseenter="hoverRow($event, true)"
                @mouseleave="hoverRow($event, false)"
              >
                <td style="padding:10px 12px; font-size:12px; color:var(--txt-2);">{{ a.date }}</td>
                <td style="padding:10px 12px; font-size:12px; color:var(--txt-1); font-weight:500;">{{ a.type }}</td>
                <td style="padding:10px 12px; font-size:12px; color:var(--txt-1); text-align:right;">{{ a.severity_score?.toFixed(3) }}</td>
                <td style="padding:10px 12px; font-size:12px; color:var(--txt-1); text-align:right;">${{ a.price?.toFixed(2) }}</td>
                <td style="padding:10px 12px; font-size:12px; text-align:right;" :style="{ color: Math.abs(a.pct_change || 0) > 5 ? 'var(--error)' : 'var(--warning)' }">
                  {{ a.pct_change != null ? (a.pct_change >= 0 ? '+' : '') + a.pct_change.toFixed(2) + '%' : '—' }}
                </td>
                <td style="padding:10px 12px;">
                  <span :style="{
                    padding:'2px 8px', borderRadius:'20px', fontSize:'10px', fontWeight:'600', textTransform:'uppercase',
                    background: a.severity?.toLowerCase() === 'high' ? 'var(--error-dim)' : a.severity?.toLowerCase() === 'medium' ? 'var(--warning-dim)' : 'var(--success-dim)',
                    color: a.severity?.toLowerCase() === 'high' ? 'var(--error)' : a.severity?.toLowerCase() === 'medium' ? 'var(--warning)' : 'var(--success)',
                  }">{{ a.severity }}</span>
                </td>
                <td style="padding:10px 12px; font-size:12px; color:var(--txt-3);">{{ a.description || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else style="text-align:center; padding:32px 0; color:var(--txt-3); font-size:13px;">
          No anomalies detected in the analysis period
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="card" style="text-align:center; padding:80px 20px;">
      <AlertTriangleIcon :size="40" color="var(--txt-3)" style="margin:0 auto 12px;" />
      <p style="font-size:14px; color:var(--txt-2); margin-bottom:6px;">Enter a symbol to detect anomalies</p>
      <p style="font-size:12px; color:var(--txt-3);">Analyzes price, volume, and volatility patterns</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { AlertTriangle as AlertTriangleIcon } from 'lucide-vue-next'
import { fetchAnomalies } from '../api/index'

const symbol = ref('AAPL')
const loading = ref(false)
const error = ref('')
const anomalyData = ref<any>(null)

// Sort by date descending (newest first)
const anomalies = computed(() =>
  [...(anomalyData.value?.anomalies || [])].sort((a: any, b: any) =>
    new Date(b.date).getTime() - new Date(a.date).getTime()
  )
)
const highSeverity = computed(() => anomalies.value.filter((a: any) => a.severity?.toLowerCase() === 'high').length)
const mediumSeverity = computed(() => anomalies.value.filter((a: any) => a.severity?.toLowerCase() === 'medium').length)

async function runDetection() {
  if (!symbol.value.trim()) return
  loading.value = true
  error.value = ''
  anomalyData.value = null
  try {
    anomalyData.value = await fetchAnomalies(symbol.value.trim().toUpperCase())
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Detection failed'
  } finally {
    loading.value = false
  }
}

function hoverRow(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.background = on ? 'var(--bg-hover)' : 'transparent'
}
</script>
