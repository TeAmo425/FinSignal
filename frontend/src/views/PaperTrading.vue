<template>
  <div style="padding:24px; max-width:1200px; margin:0 auto;">

    <!-- Header -->
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:24px;">
      <div>
        <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Paper Trading</h1>
        <p style="font-size:13px; color:var(--txt-3);">Simulate trades based on AI analysis without real money</p>
      </div>
      <button @click="showTradeModal = true" class="btn-primary" style="display:flex; align-items:center; gap:6px;">
        <PlusIcon :size="14" />
        Execute Trade
      </button>
    </div>

    <!-- Portfolio Summary Cards -->
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:24px;">
      <div class="card" style="padding:16px;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px;">Total Portfolio</p>
        <p style="font-size:22px; font-weight:700; color:var(--txt-1);">${{ portfolio ? totalValue.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}) : '—' }}</p>
      </div>
      <div class="card" style="padding:16px;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px;">Cash</p>
        <p style="font-size:22px; font-weight:700; color:var(--primary);">${{ portfolio?.cash?.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}) || '0.00' }}</p>
      </div>
      <div class="card" style="padding:16px;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px;">Total P&L</p>
        <p style="font-size:22px; font-weight:700;" :style="{ color: totalPnL >= 0 ? 'var(--success)' : 'var(--error)' }">
          {{ totalPnL >= 0 ? '+' : '' }}${{ Math.abs(totalPnL).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}) }}
        </p>
        <p style="font-size:11px;" :style="{ color: totalPnLPct >= 0 ? 'var(--success)' : 'var(--error)' }">
          {{ totalPnLPct >= 0 ? '+' : '' }}{{ totalPnLPct.toFixed(2) }}%
        </p>
      </div>
      <div class="card" style="padding:16px;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px;">Positions</p>
        <p style="font-size:22px; font-weight:700; color:var(--txt-1);">{{ holdings.length }}</p>
      </div>
    </div>

    <!-- AI Recommendation Banner -->
    <div v-if="agentStore.ticker && lastDecision" :style="{
      padding:'14px 20px', borderRadius:'12px', border:'1px solid',
      background: lastDecision === 'BUY' ? 'var(--success-dim)' : lastDecision === 'SELL' ? 'var(--error-dim)' : 'var(--warning-dim)',
      borderColor: lastDecision === 'BUY' ? 'var(--success)' : lastDecision === 'SELL' ? 'var(--error)' : 'var(--warning)',
      marginBottom:'20px', display:'flex', alignItems:'center', justifyContent:'space-between',
    }">
      <div style="display:flex; align-items:center; gap:10px;">
        <BotIcon :size="16" :color="lastDecision === 'BUY' ? 'var(--success)' : lastDecision === 'SELL' ? 'var(--error)' : 'var(--warning)'" />
        <span style="font-size:13px; font-weight:500; color:var(--txt-1);">
          AI recommends <strong>{{ lastDecision }}</strong> for <strong>{{ agentStore.ticker }}</strong>
        </span>
      </div>
      <button @click="executeAITrade" class="btn-primary" style="padding:6px 14px; font-size:12px;">
        Execute
      </button>
    </div>

    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">

      <!-- Holdings Table -->
      <div class="card">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:14px;">Current Holdings</h3>
        <div v-if="holdings.length" style="overflow-x:auto;">
          <table style="width:100%; border-collapse:collapse;">
            <thead>
              <tr style="border-bottom:1px solid var(--border);">
                <th style="text-align:left; padding:6px 0; font-size:10px; color:var(--txt-3); font-weight:500;">Symbol</th>
                <th style="text-align:right; padding:6px 0; font-size:10px; color:var(--txt-3); font-weight:500;">Shares</th>
                <th style="text-align:right; padding:6px 0; font-size:10px; color:var(--txt-3); font-weight:500;">Cost</th>
                <th style="text-align:right; padding:6px 0; font-size:10px; color:var(--txt-3); font-weight:500;">Price</th>
                <th style="text-align:right; padding:6px 0; font-size:10px; color:var(--txt-3); font-weight:500;">P&L%</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="h in holdings"
                :key="h.symbol"
                style="border-bottom:1px solid var(--border);"
                @mouseenter="hoverRow($event, true)"
                @mouseleave="hoverRow($event, false)"
              >
                <td style="padding:9px 0; font-size:12px; font-weight:700; color:var(--primary-txt);">{{ h.symbol }}</td>
                <td style="padding:9px 0; font-size:12px; color:var(--txt-2); text-align:right;">{{ h.shares }}</td>
                <td style="padding:9px 0; font-size:12px; color:var(--txt-2); text-align:right;">${{ h.avg_cost?.toFixed(2) }}</td>
                <td style="padding:9px 0; font-size:12px; color:var(--txt-1); text-align:right;">${{ h.current_price?.toFixed(2) }}</td>
                <td style="padding:9px 0; font-size:12px; font-weight:600; text-align:right;" :style="{ color: h.pnl_pct >= 0 ? 'var(--success)' : 'var(--error)' }">
                  {{ h.pnl_pct >= 0 ? '+' : '' }}{{ h.pnl_pct?.toFixed(2) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else style="text-align:center; padding:32px 0; color:var(--txt-3); font-size:13px;">
          No holdings yet. Execute a trade to get started.
        </div>
      </div>

      <!-- Trade History -->
      <div class="card">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:14px;">Trade History</h3>
        <div v-if="tradeHistory.length" style="display:flex; flex-direction:column; gap:8px; max-height:300px; overflow-y:auto;">
          <div
            v-for="trade in tradeHistory"
            :key="trade.id"
            style="display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:var(--bg-elevated); border-radius:8px;"
          >
            <div style="display:flex; align-items:center; gap:10px;">
              <span :class="['badge', trade.action === 'BUY' ? 'badge-buy' : trade.action === 'SELL' ? 'badge-sell' : 'badge-hold']">{{ trade.action }}</span>
              <div>
                <p style="font-size:12px; font-weight:600; color:var(--txt-1);">{{ trade.symbol }}</p>
                <p style="font-size:11px; color:var(--txt-3);">{{ trade.shares }} shares @ ${{ trade.price?.toFixed(2) }}</p>
              </div>
            </div>
            <div style="text-align:right;">
              <p style="font-size:12px; color:var(--txt-1);">${{ (trade.shares * trade.price).toFixed(2) }}</p>
              <p style="font-size:11px; color:var(--txt-3);">{{ trade.date }}</p>
            </div>
          </div>
        </div>
        <div v-else style="text-align:center; padding:32px 0; color:var(--txt-3); font-size:13px;">No trade history</div>
      </div>

    </div>

    <!-- Trade Modal -->
    <div v-if="showTradeModal" style="position:fixed; inset:0; background:rgba(0,0,0,0.6); display:flex; align-items:center; justify-content:center; z-index:200;" @click.self="showTradeModal = false">
      <div class="card" style="width:400px; padding:24px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
          <h3 style="font-size:16px; font-weight:600; color:var(--txt-1);">Execute Trade</h3>
          <button @click="showTradeModal = false" style="background:none; border:none; cursor:pointer; color:var(--txt-3);"><XIcon :size="18" /></button>
        </div>

        <div style="display:flex; flex-direction:column; gap:14px;">
          <div>
            <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Symbol</label>
            <input v-model="trade.symbol" type="text" placeholder="AAPL" class="input-base" style="width:100%; text-transform:uppercase;" @input="trade.symbol = String(trade.symbol).toUpperCase()" />
          </div>
          <div>
            <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Action</label>
            <div style="display:flex; gap:8px;">
              <button
                v-for="a in ['BUY', 'SELL']"
                :key="a"
                @click="trade.action = a"
                :style="{
                  flex:1, padding:'8px', border:'1px solid', borderRadius:'8px', cursor:'pointer', fontSize:'13px', fontWeight:'600',
                  background: trade.action === a ? (a === 'BUY' ? 'var(--success-dim)' : a === 'SELL' ? 'var(--error-dim)' : 'var(--warning-dim)') : 'var(--bg-elevated)',
                  borderColor: trade.action === a ? (a === 'BUY' ? 'var(--success)' : a === 'SELL' ? 'var(--error)' : 'var(--warning)') : 'var(--border)',
                  color: trade.action === a ? (a === 'BUY' ? 'var(--success)' : a === 'SELL' ? 'var(--error)' : 'var(--warning)') : 'var(--txt-2)',
                }"
              >{{ a }}</button>
            </div>
          </div>
          <div>
            <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Shares</label>
            <input v-model.number="trade.shares" type="number" min="1" placeholder="100" class="input-base" style="width:100%;" />
          </div>
          <div>
            <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Price (leave blank for market price)</label>
            <input v-model.number="trade.price" type="number" step="0.01" placeholder="Market price" class="input-base" style="width:100%;" />
          </div>
        </div>

        <div v-if="tradeError" style="margin-top:12px; padding:10px; background:var(--error-dim); border:1px solid var(--error); border-radius:8px; color:var(--error); font-size:12px;">
          {{ tradeError }}
        </div>

        <div style="display:flex; gap:10px; margin-top:20px;">
          <button @click="showTradeModal = false" class="btn-ghost" style="flex:1;">Cancel</button>
          <button @click="submitTrade" class="btn-primary" :disabled="tradeLoading || !trade.symbol || !trade.shares" style="flex:1;">
            <span style="display:flex; align-items:center; justify-content:center; gap:6px;">
              <div v-if="tradeLoading" class="spinner" style="border-top-color:#fff; width:12px; height:12px;"></div>
              {{ tradeLoading ? 'Executing...' : 'Execute' }}
            </span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus as PlusIcon, X as XIcon, Bot as BotIcon } from 'lucide-vue-next'
import { getPaperPortfolio, executePaperTrade } from '../api/index'
import { useTradingAgentStore } from '../stores/tradingAgent'

const agentStore = useTradingAgentStore()

const portfolio = ref<any>(null)
const showTradeModal = ref(false)
const tradeLoading = ref(false)
const tradeError = ref('')

const trade = reactive({
  symbol: '',
  action: 'BUY',
  shares: 100,
  price: null as number | null,
})

const holdings = computed(() => {
  const h = portfolio.value?.holdings
  if (!h) return []
  if (Array.isArray(h)) return h
  // Convert object shape (fallback) to array
  return Object.entries(h).map(([symbol, data]: [string, any]) => ({ symbol, ...data }))
})
const tradeHistory = computed(() => portfolio.value?.trades || [])

const totalValue = computed(() => {
  if (!portfolio.value) return 0
  const holdingsValue = holdings.value.reduce((sum: number, h: any) => sum + (h.current_price || 0) * h.shares, 0)
  return (portfolio.value.cash || 0) + holdingsValue
})

const totalPnL = computed(() => {
  const initialCash = portfolio.value?.initial_cash || 100000
  return totalValue.value - initialCash
})

const totalPnLPct = computed(() => {
  const initialCash = portfolio.value?.initial_cash || 100000
  return initialCash ? (totalPnL.value / initialCash) * 100 : 0
})

const lastDecision = computed(() => {
  const r = agentStore.results.find(r => r.agent === 'portfolio_manager' || r.field === 'decision')
  if (!r) return null
  const m = r.content.match(/\b(BUY|SELL|HOLD)\b/i)
  return m ? m[0].toUpperCase() : null
})

async function loadPortfolio() {
  try {
    portfolio.value = await getPaperPortfolio()
  } catch {
    // Use mock data if API not available
    portfolio.value = {
      cash: 85000,
      initial_cash: 100000,
      holdings: [
        { symbol: 'AAPL', shares: 50,  cost_basis: 165.00, current_price: 175.50, pnl_pct: 6.36 },
        { symbol: 'NVDA', shares: 10,  cost_basis: 450.00, current_price: 495.00, pnl_pct: 10.00 },
        { symbol: 'MSFT', shares: 20,  cost_basis: 380.00, current_price: 402.00, pnl_pct: 5.79 },
      ],
      trades: [
        { id: 1, symbol: 'AAPL', action: 'BUY',  shares: 50,  price: 165.00, date: '2026-03-15' },
        { id: 2, symbol: 'NVDA', action: 'BUY',  shares: 10,  price: 450.00, date: '2026-03-18' },
        { id: 3, symbol: 'TSLA', action: 'SELL', shares: 30,  price: 280.00, date: '2026-03-20' },
        { id: 4, symbol: 'MSFT', action: 'BUY',  shares: 20,  price: 380.00, date: '2026-03-22' },
      ],
    }
  }
}

async function submitTrade() {
  tradeLoading.value = true
  tradeError.value = ''
  try {
    await executePaperTrade({
      symbol: trade.symbol,
      action: trade.action,
      shares: trade.shares,
      price: trade.price || undefined,
    })
    showTradeModal.value = false
    await loadPortfolio()
    Object.assign(trade, { symbol: '', action: 'BUY', shares: 100, price: null })
  } catch (e: any) {
    tradeError.value = e.response?.data?.detail || e.message || 'Trade failed'
  } finally {
    tradeLoading.value = false
  }
}

function executeAITrade() {
  trade.symbol = agentStore.ticker
  trade.action = lastDecision.value || 'BUY'
  trade.shares = 100
  showTradeModal.value = true
}

function hoverRow(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.background = on ? 'var(--bg-hover)' : 'transparent'
}

onMounted(loadPortfolio)
</script>
