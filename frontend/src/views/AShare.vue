<template>
  <div style="padding:24px; max-width:1100px; margin:0 auto;">

    <!-- Header -->
    <div style="margin-bottom:24px;">
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
        <h1 style="font-size:22px; font-weight:700; color:var(--txt-1);">A股分析</h1>
        <span style="font-size:11px; padding:2px 8px; background:var(--warning-dim); color:var(--warning); border-radius:4px; font-weight:500;">中国市场</span>
      </div>
      <p style="font-size:13px; color:var(--txt-3);">Analyze A-share stocks from Shanghai and Shenzhen exchanges via AKShare</p>
    </div>

    <!-- Search Bar -->
    <div class="card" style="margin-bottom:20px; padding:16px;">
      <div style="display:flex; align-items:flex-end; gap:12px; flex-wrap:wrap;">
        <div>
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">股票代码 (Stock Code)</label>
          <input
            v-model="symbol"
            type="text"
            placeholder="e.g. 600519, 000858, 300750"
            class="input-base"
            style="width:220px;"
            @keydown.enter="loadStock"
          />
        </div>
        <div>
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Period</label>
          <select v-model="period" class="input-base" style="padding:8px 10px;">
            <option value="1mo">1个月</option>
            <option value="3mo">3个月</option>
            <option value="6mo">6个月</option>
            <option value="1y" selected>1年</option>
          </select>
        </div>
        <button @click="loadStock" class="btn-primary" :disabled="loading || !symbol">
          <span style="display:flex; align-items:center; gap:6px;">
            <div v-if="loading" class="spinner" style="border-top-color:#fff;"></div>
            <SearchIcon v-else :size="14" />
            {{ loading ? '加载中...' : '查询' }}
          </span>
        </button>
      </div>

      <!-- Quick Select Popular Stocks -->
      <div style="margin-top:12px; display:flex; flex-wrap:wrap; gap:6px;">
        <span style="font-size:11px; color:var(--txt-3); align-self:center;">热门股票:</span>
        <button
          v-for="s in popularStocks"
          :key="s.code"
          @click="symbol = s.code; loadStock()"
          style="padding:3px 10px; border-radius:6px; border:1px solid var(--border); background:var(--bg-elevated); cursor:pointer; font-size:11px; color:var(--txt-2); transition:all 0.15s;"
          @mouseenter="hoverBorder($event, true)"
          @mouseleave="hoverBorder($event, false)"
        >{{ s.code }} {{ s.name }}</button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" style="padding:12px 16px; background:var(--error-dim); border:1px solid var(--error); border-radius:10px; color:var(--error); font-size:13px; margin-bottom:20px;">
      {{ error }}
    </div>

    <template v-if="stockData">
      <!-- Stock Info Header -->
      <div class="card" style="margin-bottom:16px; padding:16px;">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:12px;">
          <div>
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
              <h2 style="font-size:18px; font-weight:700; color:var(--txt-1);">{{ stockData.name || symbol }}</h2>
              <span style="font-size:12px; color:var(--txt-3);">{{ symbol }}</span>
              <span v-if="stockData.exchange" style="font-size:10px; padding:2px 6px; background:var(--bg-elevated); border-radius:4px; color:var(--txt-3);">{{ stockData.exchange }}</span>
            </div>
            <div style="display:flex; align-items:center; gap:12px;">
              <span style="font-size:24px; font-weight:600; color:var(--txt-1);">¥{{ currentPrice?.toFixed(2) }}</span>
              <span :style="{ color: priceChange >= 0 ? 'var(--success)' : 'var(--error)', fontSize:'14px', fontWeight:'500' }">
                {{ priceChange >= 0 ? '+' : '' }}{{ priceChange?.toFixed(2) }}%
              </span>
            </div>
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button @click="runAIAnalysis" class="btn-primary" :disabled="agentStore.running" style="display:flex; align-items:center; gap:6px;">
              <BotIcon :size="14" />
              AI分析 (DeepSeek推荐)
            </button>
          </div>
        </div>
      </div>

      <!-- Key Metrics -->
      <div style="display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:16px;">
        <div class="card" style="padding:12px; text-align:center;">
          <p style="font-size:10px; color:var(--txt-3); text-transform:uppercase; margin-bottom:4px;">市值</p>
          <p style="font-size:14px; font-weight:600; color:var(--txt-1);">{{ marketCapDisplay }}</p>
        </div>
        <div class="card" style="padding:12px; text-align:center;">
          <p style="font-size:10px; color:var(--txt-3); text-transform:uppercase; margin-bottom:4px;">市盈率(PE)</p>
          <p style="font-size:14px; font-weight:600; color:var(--txt-1);">{{ peRatioDisplay }}</p>
        </div>
        <div class="card" style="padding:12px; text-align:center;">
          <p style="font-size:10px; color:var(--txt-3); text-transform:uppercase; margin-bottom:4px;">成交量</p>
          <p style="font-size:14px; font-weight:600; color:var(--txt-1);">{{ lastVolume ? formatVolume(lastVolume) : '—' }}</p>
        </div>
        <div class="card" style="padding:12px; text-align:center;">
          <p style="font-size:10px; color:var(--txt-3); text-transform:uppercase; margin-bottom:4px;">52周高</p>
          <p style="font-size:14px; font-weight:600; color:var(--success);">¥{{ week52High ? week52High.toFixed(2) : '—' }}</p>
        </div>
        <div class="card" style="padding:12px; text-align:center;">
          <p style="font-size:10px; color:var(--txt-3); text-transform:uppercase; margin-bottom:4px;">52周低</p>
          <p style="font-size:14px; font-weight:600; color:var(--error);">¥{{ week52Low ? week52Low.toFixed(2) : '—' }}</p>
        </div>
      </div>

      <!-- Price Chart -->
      <div class="card" style="margin-bottom:16px;">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:14px;">价格走势</h3>
        <v-chart :option="chartOption" style="width:100%; height:280px;" :autoresize="true" />
      </div>

      <!-- Fundamentals Table -->
      <div class="card">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:14px;">基本面数据</h3>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0;">
          <div v-for="row in fundamentalRows" :key="row.label" style="display:flex; justify-content:space-between; padding:8px 12px; border-bottom:1px solid var(--border); border-right:1px solid var(--border);">
            <span style="font-size:12px; color:var(--txt-3);">{{ row.label }}</span>
            <span style="font-size:12px; font-weight:500; color:var(--txt-1);">{{ row.value }}</span>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="card" style="text-align:center; padding:80px 20px;">
      <FlagIcon :size="40" color="var(--txt-3)" style="margin:0 auto 12px;" />
      <p style="font-size:14px; color:var(--txt-2); margin-bottom:6px;">输入股票代码开始分析</p>
      <p style="font-size:12px; color:var(--txt-3);">支持上证 (600xxx, 601xxx) 和深证 (000xxx, 300xxx) 股票</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search as SearchIcon, Bot as BotIcon, Flag as FlagIcon } from 'lucide-vue-next'
import { use } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { fetchAshareStock } from '../api/index'
import { useTradingAgentStore } from '../stores/tradingAgent'
import { useTradingAgent } from '../composables/useTradingAgent'

use([LineChart, BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const agentStore = useTradingAgentStore()
const { start } = useTradingAgent()

const symbol = ref('')
const period = ref('1y')
const loading = ref(false)
const error = ref('')
const stockData = ref<any>(null)

const popularStocks = [
  { code: '600519', name: '茅台' },
  { code: '000858', name: '五粮液' },
  { code: '300750', name: '宁德时代' },
  { code: '601318', name: '中国平安' },
  { code: '000333', name: '美的集团' },
  { code: '600036', name: '招商银行' },
]

const priceHistory = computed(() => stockData.value?.data || stockData.value?.prices || stockData.value?.history || [])
const currentPrice = computed(() => {
  if (stockData.value?.current_price) return stockData.value.current_price
  const h = priceHistory.value
  return h.length ? (h[h.length - 1].close || h[h.length - 1].price || 0) : 0
})
const priceChange = computed(() => {
  if (stockData.value?.change_pct != null) return stockData.value.change_pct
  const h = priceHistory.value
  if (h.length < 2) return 0
  const last = h[h.length - 1].close
  const prev = h[h.length - 2].close
  return prev ? ((last - prev) / prev) * 100 : 0
})
const lastVolume = computed(() => {
  const h = priceHistory.value
  return h.length ? h[h.length - 1].volume : 0
})
const week52High = computed(() => {
  const h = priceHistory.value
  return h.length ? Math.max(...h.map((p: any) => p.high || p.close || 0)) : 0
})
const week52Low = computed(() => {
  const h = priceHistory.value
  return h.length ? Math.min(...h.map((p: any) => p.low || p.close || Infinity)) : 0
})

function formatVolume(v: number): string {
  if (v >= 1e8) return `${(v / 1e8).toFixed(1)}亿`
  if (v >= 1e4) return `${(v / 1e4).toFixed(0)}万`
  return String(v)
}

const chartOption = computed(() => {
  const prices = priceHistory.value
  if (!prices.length) return {}
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger:'axis', backgroundColor:'var(--bg-elevated)', borderColor:'var(--border-s)', textStyle:{color:'var(--txt-1)',fontSize:12} },
    grid: { top:8, bottom:36, left:60, right:16 },
    xAxis: { type:'category', data: prices.map((p: any) => p.date), axisLabel:{color:'var(--txt-3)',fontSize:10}, axisLine:{lineStyle:{color:'var(--border)'}}, splitLine:{show:false} },
    yAxis: { type:'value', scale:true, axisLabel:{color:'var(--txt-3)',fontSize:10,formatter:(v:number)=>`¥${v.toFixed(0)}`}, splitLine:{lineStyle:{color:'var(--border)',type:'dashed'}} },
    series: [{
      type:'line', data: prices.map((p: any) => p.close || p.price),
      smooth:false, symbol:'none', lineStyle:{color:'#fdd663',width:2},
      areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(253,214,99,0.12)'},{offset:1,color:'rgba(253,214,99,0)'}]}},
    }],
  }
})

// Safe number helpers
function safeNum(v: any): number | null {
  const n = parseFloat(String(v))
  return isFinite(n) ? n : null
}
function fmtShares(v: any): string {
  const n = safeNum(v)
  if (n === null) return '—'
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿股`
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)}万股`
  return String(n)
}

const marketCapDisplay = computed(() => {
  const n = safeNum(stockData.value?.market_cap)
  if (n === null) return '—'
  if (n >= 1e12) return `¥${(n / 1e12).toFixed(2)}万亿`
  if (n >= 1e8)  return `¥${(n / 1e8).toFixed(0)}亿`
  return `¥${n.toFixed(0)}`
})

const peRatioDisplay = computed(() => {
  const n = safeNum(stockData.value?.pe_ratio)
  return n !== null ? n.toFixed(1) : '—'
})

const fundamentalRows = computed(() => {
  const d = stockData.value || {}
  const pb  = safeNum(d.pb_ratio)
  const roe = safeNum(d.roe)
  const eps = safeNum(d.eps)
  return [
    { label: '行业',       value: d.sector || '—' },
    { label: '上市交易所',  value: d.exchange_name || d.exchange || '—' },
    { label: '上市时间',    value: d.listing_date || '—' },
    { label: '市净率(PB)', value: pb !== null ? pb.toFixed(2) : '—' },
    { label: 'ROE',        value: roe !== null ? `${(Math.abs(roe) < 2 ? roe * 100 : roe).toFixed(1)}%` : '—' },
    { label: '每股收益',    value: eps !== null ? `¥${eps.toFixed(2)}` : '—' },
    { label: '流通股本',    value: fmtShares(d.float_shares) },
    { label: '总股本',      value: fmtShares(d.total_shares) },
  ]
})

async function loadStock() {
  if (!symbol.value.trim()) return
  loading.value = true
  error.value = ''
  stockData.value = null
  try {
    stockData.value = await fetchAshareStock(symbol.value.trim(), period.value)
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function runAIAnalysis() {
  await start({
    ticker: symbol.value.trim(),
    date: new Date().toISOString().split('T')[0],
    analysts: ['market', 'fundamentals'],
    provider: 'deepseek',
    deepModel: 'deepseek-reasoner',
    quickModel: 'deepseek-chat',
  })
}

function hoverBorder(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.borderColor = on ? 'var(--border-s)' : 'var(--border)'
}
</script>
