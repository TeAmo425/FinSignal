<template>
  <div style="padding:24px; max-width:1400px; margin:0 auto;">

    <!-- Header -->
    <div style="margin-bottom:24px;">
      <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Market Intelligence Hub</h1>
      <p style="font-size:13px; color:var(--txt-3);">Real-time market data and AI-powered insights</p>
    </div>

    <!-- Market Mood Strip -->
    <div style="margin-bottom:24px;">
      <p class="section-title">Watchlist</p>
      <div style="display:grid; grid-template-columns:repeat(5,1fr); gap:12px;">
        <div
          v-for="ticker in watchlist"
          :key="ticker"
          class="card"
          style="padding:14px; cursor:pointer; transition:border-color 0.15s; position:relative; overflow:hidden;"
          @mouseenter="hoverCard($event, true)"
          @mouseleave="hoverCard($event, false)"
          @click="router.push(`/stock/${ticker}`)"
        >
          <div style="display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:8px;">
            <span style="font-size:14px; font-weight:700; color:var(--txt-1);">{{ ticker }}</span>
            <button
              @click.stop="runQuickAnalysis(ticker)"
              style="background:var(--primary-dim); border:none; border-radius:6px; padding:3px 8px; cursor:pointer; color:var(--primary-txt); font-size:10px; font-weight:500;"
              :disabled="agentStore.running"
            >AI</button>
          </div>
          <template v-if="stockData[ticker]">
            <p style="font-size:18px; font-weight:600; color:var(--txt-1);">${{ stockData[ticker].price?.toFixed(2) }}</p>
            <p :style="{ fontSize:'12px', color: stockData[ticker].change >= 0 ? 'var(--success)' : 'var(--error)', marginTop:'2px' }">
              {{ stockData[ticker].change >= 0 ? '+' : '' }}{{ stockData[ticker].change?.toFixed(2) }}%
            </p>
          </template>
          <template v-else>
            <div class="pulse-soft" style="height:18px; width:70px; background:var(--bg-elevated); border-radius:4px; margin-bottom:4px;"></div>
            <div class="pulse-soft" style="height:12px; width:50px; background:var(--bg-elevated); border-radius:4px;"></div>
          </template>

          <!-- Cached AI result badge -->
          <div v-if="getCachedDecision(ticker)" style="position:absolute; top:8px; right:8px;">
            <span :class="['badge', getCachedDecisionClass(ticker)]" style="font-size:9px;">{{ getCachedDecision(ticker) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">

      <!-- Last AI Analysis -->
      <div class="card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
          <h3 style="font-size:14px; font-weight:600; color:var(--txt-1);">Last AI Analysis</h3>
          <RouterLink to="/trading-agents" style="font-size:12px; color:var(--primary-txt); text-decoration:none;">Run New →</RouterLink>
        </div>
        <template v-if="agentStore.ticker && agentStore.results.length">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
            <span style="font-size:16px; font-weight:700; color:var(--primary);">{{ agentStore.ticker }}</span>
            <span v-if="lastDecision" :class="['badge', lastDecisionClass]">{{ lastDecision }}</span>
            <span style="font-size:11px; color:var(--txt-3);">{{ agentStore.tradeDate }}</span>
          </div>
          <div style="display:flex; flex-direction:column; gap:8px;">
            <div
              v-for="result in agentStore.results.slice(0, 4)"
              :key="result.field"
              style="padding:10px; background:var(--bg-elevated); border-radius:8px;"
            >
              <p style="font-size:11px; font-weight:600; color:var(--txt-3); margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px;">{{ result.label }}</p>
              <p style="font-size:12px; color:var(--txt-2); line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">{{ result.content }}</p>
            </div>
          </div>
        </template>
        <div v-else style="text-align:center; padding:32px 0; color:var(--txt-3);">
          <p style="font-size:13px; margin-bottom:8px;">No analysis yet</p>
          <RouterLink to="/trading-agents" style="color:var(--primary-txt); font-size:12px;">Start analysis →</RouterLink>
        </div>
      </div>

      <!-- Fundamentals Snapshot -->
      <div class="card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
          <h3 style="font-size:14px; font-weight:600; color:var(--txt-1);">Quick Fundamentals</h3>
          <select
            v-model="selectedFundTicker"
            class="input-base"
            style="padding:4px 8px; font-size:12px; width:auto;"
            @change="loadFundamentals"
          >
            <option v-for="t in watchlist" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <template v-if="fundamentals">
          <table style="width:100%; border-collapse:collapse;">
            <tbody>
              <tr v-for="row in fundRows" :key="row.label" style="border-bottom:1px solid var(--border);">
                <td style="padding:8px 0; font-size:12px; color:var(--txt-3);">{{ row.label }}</td>
                <td style="padding:8px 0; font-size:12px; color:var(--txt-1); text-align:right; font-weight:500;">{{ row.value }}</td>
              </tr>
            </tbody>
          </table>
        </template>
        <div v-else style="text-align:center; padding:32px 0;">
          <div v-if="loadingFund" class="spinner" style="margin:0 auto;"></div>
          <p v-else style="font-size:13px; color:var(--txt-3);">Select a stock to view fundamentals</p>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useTradingAgentStore } from '../stores/tradingAgent'
import { useTradingAgent } from '../composables/useTradingAgent'
import { fetchStock, fetchFundamentals } from '../api/index'

const router = useRouter()
const agentStore = useTradingAgentStore()
const { start } = useTradingAgent()

const watchlist = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL']
const stockData = ref<Record<string, { price: number; change: number }>>({})
const fundamentals = ref<Record<string, unknown> | null>(null)
const loadingFund = ref(false)
const selectedFundTicker = ref('AAPL')

const lastDecision = computed(() => {
  const r = agentStore.results.find(r => r.field === 'decision' || r.agent === 'portfolio_manager')
  if (!r) return null
  const m = r.content.match(/\b(BUY|SELL|HOLD)\b/i)
  return m ? m[0].toUpperCase() : null
})

const lastDecisionClass = computed(() => {
  switch (lastDecision.value) {
    case 'BUY':  return 'badge-buy'
    case 'SELL': return 'badge-sell'
    case 'HOLD': return 'badge-hold'
    default:     return 'badge-neutral'
  }
})

function getCachedDecision(ticker: string): string | null {
  try {
    const cache = JSON.parse(sessionStorage.getItem('agentCache') || '{}')
    if (!cache[ticker]) return null
    const results = cache[ticker].results || []
    const r = results.find((x: any) => x.field === 'decision' || x.agent === 'portfolio_manager')
    if (!r) return null
    const m = r.content.match(/\b(BUY|SELL|HOLD)\b/i)
    return m ? m[0].toUpperCase() : null
  } catch { return null }
}

function getCachedDecisionClass(ticker: string): string {
  switch (getCachedDecision(ticker)) {
    case 'BUY':  return 'badge-buy'
    case 'SELL': return 'badge-sell'
    case 'HOLD': return 'badge-hold'
    default:     return 'badge-neutral'
  }
}

async function loadStockPrice(ticker: string) {
  // Check sessionStorage cache first (5-minute TTL)
  const cacheKey = `price_cache_${ticker}`
  try {
    const cached = JSON.parse(sessionStorage.getItem(cacheKey) || 'null')
    if (cached && Date.now() - cached.ts < 5 * 60 * 1000) {
      stockData.value[ticker] = cached.data
      return
    }
  } catch { /* ignore */ }

  try {
    const data = await fetchStock(ticker, '5d')
    const prices = data.data || data.prices || data.history || []
    let entry = null
    if (prices.length >= 2) {
      const last = prices[prices.length - 1]
      const prev = prices[prices.length - 2]
      entry = {
        price: last.close || last.price || 0,
        change: prev.close ? ((last.close - prev.close) / prev.close) * 100 : 0,
      }
    } else if (prices.length === 1) {
      entry = { price: prices[0].close || 0, change: 0 }
    }
    if (entry) {
      stockData.value[ticker] = entry
      sessionStorage.setItem(cacheKey, JSON.stringify({ data: entry, ts: Date.now() }))
    }
  } catch { /* ignore */ }
}

async function loadFundamentals() {
  loadingFund.value = true
  fundamentals.value = null
  try {
    fundamentals.value = await fetchFundamentals(selectedFundTicker.value)
  } catch { /* ignore */ } finally {
    loadingFund.value = false
  }
}

const fundRows = computed(() => {
  if (!fundamentals.value) return []
  const f = fundamentals.value as any
  return [
    { label: 'Market Cap',   value: f.market_cap   ? `$${(f.market_cap / 1e9).toFixed(1)}B` : '—' },
    { label: 'P/E Ratio',    value: f.pe_ratio      ? f.pe_ratio.toFixed(2) : '—' },
    { label: 'EPS (TTM)',    value: f.eps           ? `$${f.eps.toFixed(2)}` : '—' },
    { label: 'Revenue',      value: f.revenue       ? `$${(f.revenue / 1e9).toFixed(1)}B` : '—' },
    { label: 'Gross Margin', value: f.gross_margin  ? `${(f.gross_margin * 100).toFixed(1)}%` : '—' },
    { label: 'Debt/Equity',  value: f.debt_to_equity ? f.debt_to_equity.toFixed(2) : '—' },
    { label: '52W High',     value: f.week_52_high   ? `$${f.week_52_high.toFixed(2)}` : '—' },
    { label: '52W Low',      value: f.week_52_low    ? `$${f.week_52_low.toFixed(2)}` : '—' },
  ]
})

async function runQuickAnalysis(ticker: string) {
  await start({
    ticker,
    date: new Date().toISOString().split('T')[0],
    analysts: ['market', 'social', 'fundamentals'],
    provider: agentStore.provider,
    deepModel: agentStore.deepModel,
    quickModel: agentStore.quickModel,
  })
}

function hoverCard(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.borderColor = on ? 'var(--border-s)' : 'var(--border)'
}

onMounted(() => {
  watchlist.forEach(loadStockPrice)
  loadFundamentals()
})
</script>
