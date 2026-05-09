<template>
  <div style="padding:24px; max-width:1300px; margin:0 auto;">

    <!-- Header -->
    <div style="margin-bottom:24px;">
      <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Stock Screener</h1>
      <p style="font-size:13px; color:var(--txt-3);">Filter US and A-share stocks by fundamental and technical criteria</p>
    </div>

    <div style="display:grid; grid-template-columns:280px 1fr; gap:20px; align-items:start;">

      <!-- Filters Panel -->
      <div class="card" style="padding:16px; position:sticky; top:16px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
          <h3 style="font-size:14px; font-weight:600; color:var(--txt-1);">Filters</h3>
          <button @click="resetFilters" style="background:none; border:none; cursor:pointer; font-size:11px; color:var(--txt-3);">Reset</button>
        </div>

        <!-- Market Selector -->
        <div style="margin-bottom:16px;">
          <p class="section-title" style="margin-bottom:8px;">Market</p>
          <div style="display:flex; gap:6px;">
            <button
              v-for="m in ['US']"
              :key="m"
              @click="filters.market = m"
              :style="{
                flex:1, padding:'6px', border:'1px solid', borderRadius:'6px', cursor:'pointer', fontSize:'12px', fontWeight:'500',
                background: filters.market === m ? 'var(--primary-dim)' : 'var(--bg-elevated)',
                borderColor: filters.market === m ? 'var(--primary)' : 'var(--border)',
                color: filters.market === m ? 'var(--primary-txt)' : 'var(--txt-2)',
              }"
            >{{ m }}</button>
          </div>
        </div>

        <!-- P/E Range -->
        <div style="margin-bottom:14px;">
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:6px;">P/E Ratio</label>
          <div style="display:flex; gap:8px; align-items:center;">
            <input v-model.number="filters.peMin" type="number" placeholder="Min" class="input-base" style="flex:1; min-width:0; padding:6px 8px;" />
            <span style="color:var(--txt-3); font-size:12px; flex-shrink:0;">—</span>
            <input v-model.number="filters.peMax" type="number" placeholder="Max" class="input-base" style="flex:1; min-width:0; padding:6px 8px;" />
          </div>
        </div>

        <!-- Market Cap -->
        <div style="margin-bottom:14px;">
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:6px;">Market Cap</label>
          <select v-model="filters.marketCap" class="input-base" style="width:100%; padding:7px 10px;">
            <option value="">Any</option>
            <option value="mega">Mega Cap (>$200B)</option>
            <option value="large">Large Cap ($10B–$200B)</option>
            <option value="mid">Mid Cap ($2B–$10B)</option>
            <option value="small">Small Cap (<$2B)</option>
          </select>
        </div>

        <!-- Beta -->
        <div style="margin-bottom:14px;">
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:6px;">Beta Range</label>
          <div style="display:flex; gap:8px; align-items:center;">
            <input v-model.number="filters.betaMin" type="number" step="0.1" placeholder="Min" class="input-base" style="flex:1; min-width:0; padding:6px 8px;" />
            <span style="color:var(--txt-3); font-size:12px; flex-shrink:0;">—</span>
            <input v-model.number="filters.betaMax" type="number" step="0.1" placeholder="Max" class="input-base" style="flex:1; min-width:0; padding:6px 8px;" />
          </div>
        </div>

        <!-- Sector -->
        <div style="margin-bottom:14px;">
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:6px;">Sector</label>
          <select v-model="filters.sector" class="input-base" style="width:100%; padding:7px 10px;">
            <option value="">All Sectors</option>
            <option value="technology">Technology</option>
            <option value="healthcare">Healthcare</option>
            <option value="financials">Financials</option>
            <option value="consumer">Consumer</option>
            <option value="energy">Energy</option>
            <option value="industrials">Industrials</option>
            <option value="utilities">Utilities</option>
            <option value="materials">Materials</option>
          </select>
        </div>

        <!-- 52W Return -->
        <div style="margin-bottom:20px;">
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:6px;">52-Week Return (%)</label>
          <div style="display:flex; gap:8px; align-items:center;">
            <input v-model.number="filters.returnMin" type="number" placeholder="Min" class="input-base" style="flex:1; min-width:0; padding:6px 8px;" />
            <span style="color:var(--txt-3); font-size:12px; flex-shrink:0;">—</span>
            <input v-model.number="filters.returnMax" type="number" placeholder="Max" class="input-base" style="flex:1; min-width:0; padding:6px 8px;" />
          </div>
        </div>

        <button @click="runScreener" class="btn-primary" :disabled="loading" style="width:100%; padding:10px; font-size:13px;">
          <span style="display:flex; align-items:center; justify-content:center; gap:6px;">
            <div v-if="loading" class="spinner" style="border-top-color:#fff;"></div>
            <FilterIcon v-else :size="14" />
            {{ loading ? 'Screening...' : 'Screen Stocks' }}
          </span>
        </button>
      </div>

      <!-- Results -->
      <div>
        <!-- Summary Bar -->
        <div v-if="results.length" style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;">
          <p style="font-size:13px; color:var(--txt-2);"><span style="font-weight:600; color:var(--txt-1);">{{ results.length }}</span> stocks match your criteria</p>
          <div style="display:flex; gap:8px;">
            <button
              v-for="col in ['Symbol', 'Price', 'Change', 'Market Cap', 'P/E', 'Beta', 'Sector', '52W Return']"
              :key="col"
            ></button>
          </div>
        </div>

        <!-- Error -->
        <div v-if="error" style="padding:12px 16px; background:var(--error-dim); border:1px solid var(--error); border-radius:10px; color:var(--error); font-size:13px; margin-bottom:14px;">
          {{ error }}
        </div>

        <!-- Results Table -->
        <div v-if="results.length" class="card" style="padding:0; overflow:hidden;">
          <table style="width:100%; border-collapse:collapse;">
            <thead>
              <tr style="border-bottom:1px solid var(--border); background:var(--bg-elevated);">
                <th style="text-align:left; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">Symbol</th>
                <th style="text-align:left; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">Name</th>
                <th style="text-align:right; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">Price</th>
                <th style="text-align:right; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">Change</th>
                <th style="text-align:right; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">Market Cap</th>
                <th style="text-align:right; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">P/E</th>
                <th style="text-align:right; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">Beta</th>
                <th style="text-align:left; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">Sector</th>
                <th style="text-align:right; padding:12px 14px; font-size:11px; color:var(--txt-3); font-weight:500;">52W Ret.</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="stock in results"
                :key="stock.symbol"
                style="border-bottom:1px solid var(--border); cursor:pointer;"
                @click="router.push(`/stock/${stock.symbol}`)"
                @mouseenter="hoverRow($event, true)"
                @mouseleave="hoverRow($event, false)"
              >
                <td style="padding:11px 14px; font-size:12px; font-weight:700; color:var(--primary-txt);">{{ stock.symbol }}</td>
                <td style="padding:11px 14px; font-size:12px; color:var(--txt-2);">{{ stock.name }}</td>
                <td style="padding:11px 14px; font-size:12px; color:var(--txt-1); text-align:right;">${{ stock.price?.toFixed(2) }}</td>
                <td style="padding:11px 14px; font-size:12px; color:var(--txt-3); text-align:right;">—</td>
                <td style="padding:11px 14px; font-size:12px; color:var(--txt-2); text-align:right;">{{ stock.market_cap_b ? `$${stock.market_cap_b.toFixed(1)}B` : '—' }}</td>
                <td style="padding:11px 14px; font-size:12px; color:var(--txt-1); text-align:right;">{{ stock.pe_ratio?.toFixed(1) || '—' }}</td>
                <td style="padding:11px 14px; font-size:12px; color:var(--txt-2); text-align:right;">{{ stock.beta?.toFixed(2) || '—' }}</td>
                <td style="padding:11px 14px; font-size:11px; color:var(--txt-3);">{{ stock.sector || '—' }}</td>
                <td style="padding:11px 14px; font-size:12px; text-align:right;" :style="{ color: (stock.ytd_return || 0) >= 0 ? 'var(--success)' : 'var(--error)' }">
                  {{ (stock.ytd_return || 0) >= 0 ? '+' : '' }}{{ stock.ytd_return?.toFixed(1) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Empty State -->
        <div v-else-if="!loading" class="card" style="text-align:center; padding:80px 20px;">
          <FilterIcon :size="40" color="var(--txt-3)" style="margin:0 auto 12px;" />
          <p style="font-size:14px; color:var(--txt-2); margin-bottom:6px;">Configure filters and screen stocks</p>
          <p style="font-size:12px; color:var(--txt-3);">Click "Screen Stocks" to find matching equities</p>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Filter as FilterIcon } from 'lucide-vue-next'
import { screenStocks } from '../api/index'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const results = ref<any[]>([])

const filters = reactive({
  market: 'US',
  peMin: null as number | null,
  peMax: null as number | null,
  marketCap: '',
  betaMin: null as number | null,
  betaMax: null as number | null,
  sector: '',
  returnMin: null as number | null,
  returnMax: null as number | null,
})

function resetFilters() {
  Object.assign(filters, {
    market: 'US', peMin: null, peMax: null, marketCap: '',
    betaMin: null, betaMax: null, sector: '', returnMin: null, returnMax: null,
  })
  results.value = []
}

async function runScreener() {
  loading.value = true
  error.value = ''
  results.value = []
  try {
    // Map "A-Share" UI label to backend "CN" market value
    const marketValue = filters.market === 'A-Share' ? 'CN' : filters.market
    const params: Record<string, unknown> = { market: marketValue }
    if (filters.peMin !== null) params.min_pe = filters.peMin
    if (filters.peMax !== null) params.max_pe = filters.peMax
    // Convert market cap tier to min/max values (in billions)
    if (filters.marketCap === 'mega')  { params.min_market_cap = 200 }
    if (filters.marketCap === 'large') { params.min_market_cap = 10;  params.max_market_cap = 200 }
    if (filters.marketCap === 'mid')   { params.min_market_cap = 2;   params.max_market_cap = 10 }
    if (filters.marketCap === 'small') { params.max_market_cap = 2 }
    if (filters.betaMin !== null) params.min_beta = filters.betaMin
    if (filters.betaMax !== null) params.max_beta = filters.betaMax
    if (filters.sector) params.sector = filters.sector
    if (filters.returnMin !== null) params.min_ytd_return = filters.returnMin
    if (filters.returnMax !== null) params.max_ytd_return = filters.returnMax
    const res = await screenStocks(params)
    results.value = res.results || res || []
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Screening failed'
  } finally {
    loading.value = false
  }
}

function hoverRow(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.background = on ? 'var(--bg-hover)' : 'transparent'
}
</script>
