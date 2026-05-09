<template>
  <div style="padding:24px; max-width:1400px; margin:0 auto;">

    <!-- Header -->
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
      <button @click="router.back()" style="background:none; border:none; cursor:pointer; color:var(--txt-3); padding:4px;">
        <ArrowLeftIcon :size="18" />
      </button>
      <div>
        <div style="display:flex; align-items:center; gap:10px;">
          <h1 style="font-size:22px; font-weight:700; color:var(--txt-1);">{{ ticker }}</h1>
          <span v-if="stockInfo" style="font-size:13px; color:var(--txt-3);">{{ stockInfo.company_name || stockInfo.longName }}</span>
        </div>
        <div v-if="stockInfo" style="display:flex; align-items:center; gap:8px; margin-top:2px;">
          <span style="font-size:24px; font-weight:600; color:var(--txt-1);">${{ currentPrice?.toFixed(2) }}</span>
          <span :style="{ color: priceChange >= 0 ? 'var(--success)' : 'var(--error)', fontSize:'14px', fontWeight:'500' }">
            {{ priceChange >= 0 ? '+' : '' }}{{ priceChange?.toFixed(2) }}%
          </span>
        </div>
      </div>
      <div style="margin-left:auto; display:flex; gap:8px;">
        <select v-model="period" @change="loadData" class="input-base" style="padding:6px 10px; font-size:12px;">
          <option value="1mo">1M</option>
          <option value="3mo">3M</option>
          <option value="6mo">6M</option>
          <option value="1y" selected>1Y</option>
          <option value="2y">2Y</option>
          <option value="5y">5Y</option>
        </select>
        <button @click="runAnalysis" class="btn-primary" :disabled="agentStore.running">
          <span style="display:flex; align-items:center; gap:6px;">
            <BotIcon :size="14" />
            AI Analysis
          </span>
        </button>
      </div>
    </div>

    <div v-if="loading" style="text-align:center; padding:80px 0;">
      <div class="spinner" style="margin:0 auto; width:24px; height:24px;"></div>
      <p style="margin-top:12px; color:var(--txt-3);">Loading {{ ticker }}...</p>
    </div>

    <template v-else-if="stockInfo">

      <!-- Stat Cards -->
      <div style="display:grid; grid-template-columns:repeat(6,1fr); gap:12px; margin-bottom:20px;">
        <div v-for="stat in statCards" :key="stat.label" class="card" style="padding:12px; text-align:center;">
          <p style="font-size:10px; color:var(--txt-3); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">{{ stat.label }}</p>
          <p style="font-size:15px; font-weight:600;" :style="{ color: stat.color || 'var(--txt-1)' }">{{ stat.value }}</p>
        </div>
      </div>

      <!-- 52W Range -->
      <div class="card" style="margin-bottom:20px; padding:14px 20px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
          <span style="font-size:12px; color:var(--txt-3);">52-Week Range</span>
          <span style="font-size:12px; font-weight:500; color:var(--txt-1);">{{ ((currentPrice - week52Low) / (week52High - week52Low) * 100).toFixed(0) }}% of range</span>
        </div>
        <div style="position:relative; height:6px; background:var(--bg-elevated); border-radius:3px;">
          <div style="position:absolute; left:0; top:0; height:100%; background:linear-gradient(90deg,var(--error),var(--warning),var(--success)); border-radius:3px; width:100%; opacity:0.3;"></div>
          <div
            :style="{
              position:'absolute', top:'-3px',
              left: `${Math.max(0, Math.min(100, (currentPrice - week52Low) / (week52High - week52Low) * 100))}%`,
              width:'12px', height:'12px', borderRadius:'50%', background:'var(--primary)',
              transform:'translateX(-50%)', boxShadow:'0 0 6px var(--primary)',
            }"
          ></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:6px;">
          <span style="font-size:11px; color:var(--error);">${{ week52Low.toFixed(2) }}</span>
          <span style="font-size:11px; color:var(--success);">${{ week52High.toFixed(2) }}</span>
        </div>
      </div>

      <!-- Price + Volume Chart -->
      <div class="card" style="margin-bottom:20px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
          <h3 style="font-size:14px; font-weight:600; color:var(--txt-1);">Price & Volume</h3>
          <div style="display:flex; gap:6px;">
            <button v-for="ma in ['MA20','MA50','MA200']" :key="ma"
              @click="toggleMA(ma)"
              :style="{
                padding:'3px 8px', borderRadius:'6px', border:'1px solid', cursor:'pointer', fontSize:'11px', fontWeight:'500',
                background: activeMA.includes(ma) ? 'var(--primary-dim)' : 'transparent',
                borderColor: activeMA.includes(ma) ? 'var(--primary)' : 'var(--border)',
                color: activeMA.includes(ma) ? 'var(--primary-txt)' : 'var(--txt-3)',
              }"
            >{{ ma }}</button>
          </div>
        </div>
        <v-chart :option="priceChartOption" style="width:100%; height:320px;" :autoresize="true" />
      </div>

      <!-- RSI + MACD -->
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px;">
        <div class="card">
          <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:12px;">RSI (14)</h3>
          <v-chart :option="rsiChartOption" style="width:100%; height:160px;" :autoresize="true" />
        </div>
        <div class="card">
          <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:12px;">MACD</h3>
          <v-chart :option="macdChartOption" style="width:100%; height:160px;" :autoresize="true" />
        </div>
      </div>

      <!-- Fundamentals + Peers -->
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
        <div class="card">
          <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:14px;">Fundamentals</h3>
          <table style="width:100%; border-collapse:collapse;">
            <tbody>
              <tr v-for="row in fundamentalRows" :key="row.label" style="border-bottom:1px solid var(--border);">
                <td style="padding:8px 0; font-size:12px; color:var(--txt-3);">{{ row.label }}</td>
                <td style="padding:8px 0; font-size:12px; font-weight:500; color:var(--txt-1); text-align:right;">{{ row.value }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card">
          <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:14px;">Peer Comparison</h3>
          <div v-if="peers.length">
            <table style="width:100%; border-collapse:collapse;">
              <thead>
                <tr>
                  <th style="text-align:left; padding:0 0 8px; font-size:11px; color:var(--txt-3); font-weight:500;">Symbol</th>
                  <th style="text-align:right; padding:0 0 8px; font-size:11px; color:var(--txt-3); font-weight:500;">Sector</th>
                  <th style="text-align:right; padding:0 0 8px; font-size:11px; color:var(--txt-3); font-weight:500;">1Y Return</th>
                  <th style="text-align:right; padding:0 0 8px; font-size:11px; color:var(--txt-3); font-weight:500;">Mkt Cap</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="peer in peers"
                  :key="peer.symbol"
                  style="border-top:1px solid var(--border); cursor:pointer;"
                  @click="router.push(`/stock/${peer.symbol}`)"
                  @mouseenter="hoverRow($event, true)"
                  @mouseleave="hoverRow($event, false)"
                >
                  <td style="padding:8px 0; font-size:12px; color:var(--primary-txt); font-weight:600;">{{ peer.symbol }}</td>
                  <td style="padding:8px 0; font-size:12px; color:var(--txt-2); text-align:right;">{{ peer.sector || '—' }}</td>
                  <td style="padding:8px 0; font-size:12px; text-align:right;" :style="{ color: (peer.ytd_return || 0) >= 0 ? 'var(--success)' : 'var(--error)' }">{{ (peer.ytd_return || 0) >= 0 ? '+' : '' }}{{ peer.ytd_return?.toFixed(2) ?? '—' }}%</td>
                  <td style="padding:8px 0; font-size:12px; color:var(--txt-2); text-align:right;">{{ peer.market_cap ? `$${(peer.market_cap/1e9).toFixed(0)}B` : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else style="text-align:center; padding:24px 0; color:var(--txt-3); font-size:13px;">No peer data available</div>
        </div>
      </div>

    </template>

    <div v-else-if="error" style="text-align:center; padding:80px 0;">
      <p style="color:var(--error); font-size:14px;">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft as ArrowLeftIcon, Bot as BotIcon } from 'lucide-vue-next'
import { use } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { fetchStock, fetchFundamentals, fetchPeers } from '../api/index'
import { useTradingAgentStore } from '../stores/tradingAgent'
import { useTradingAgent } from '../composables/useTradingAgent'

use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, CanvasRenderer])

const route = useRoute()
const router = useRouter()
const agentStore = useTradingAgentStore()
const { start } = useTradingAgent()

const ticker = computed(() => (route.params.ticker as string).toUpperCase())
const period = ref('1y')
const loading = ref(true)
const error = ref('')
const stockInfo = ref<any>(null)
const fundamentalsData = ref<any>(null)
const peers = ref<any[]>([])
const activeMA = ref<string[]>(['MA20'])

function calcMA(prices: number[], n: number): (number | null)[] {
  return prices.map((_, i) => {
    if (i < n - 1) return null
    return prices.slice(i - n + 1, i + 1).reduce((a, b) => a + b, 0) / n
  })
}

function calcRSI(prices: number[], period = 14): number[] {
  const rsi: number[] = new Array(prices.length).fill(50)
  for (let i = period; i < prices.length; i++) {
    let gains = 0, losses = 0
    for (let j = i - period + 1; j <= i; j++) {
      const diff = prices[j] - prices[j - 1]
      if (diff > 0) gains += diff
      else losses += Math.abs(diff)
    }
    const rs = losses === 0 ? 100 : gains / losses
    rsi[i] = 100 - 100 / (1 + rs)
  }
  return rsi
}

function calcMACD(prices: number[]) {
  function ema(data: number[], n: number): number[] {
    const k = 2 / (n + 1)
    const result: number[] = [data[0]]
    for (let i = 1; i < data.length; i++) result.push(data[i] * k + result[i - 1] * (1 - k))
    return result
  }
  const ema12 = ema(prices, 12)
  const ema26 = ema(prices, 26)
  const macd = ema12.map((v, i) => v - ema26[i])
  const signal = ema(macd, 9)
  const hist = macd.map((v, i) => v - signal[i])
  return { macd, signal, hist }
}

const priceData = computed(() => {
  const info = stockInfo.value
  if (!info) return []
  return (info.data || info.prices || info.history || []) as any[]
})

const dates = computed(() => priceData.value.map((p: any) => p.date || ''))
const closes = computed(() => priceData.value.map((p: any) => p.close || 0))
const volumes = computed(() => priceData.value.map((p: any) => p.volume || 0))

const currentPrice = computed(() => closes.value[closes.value.length - 1] || 0)
const priceChange = computed(() => {
  const c = closes.value
  if (c.length < 2) return 0
  return ((c[c.length - 1] - c[c.length - 2]) / c[c.length - 2]) * 100
})

const week52High = computed(() => {
  const f = fundamentalsData.value
  if (f?.week_52_high) return f.week_52_high
  return Math.max(...closes.value.slice(-252))
})
const week52Low = computed(() => {
  const f = fundamentalsData.value
  if (f?.week_52_low) return f.week_52_low
  return Math.min(...closes.value.slice(-252))
})

const statCards = computed(() => {
  const f = fundamentalsData.value || {}
  const rsi = calcRSI(closes.value)
  const lastRsi = rsi[rsi.length - 1]
  return [
    { label: 'Market Cap', value: f.market_cap ? `$${(f.market_cap / 1e9).toFixed(1)}B` : '—' },
    { label: 'P/E Ratio', value: f.pe_ratio?.toFixed(1) || '—' },
    { label: 'EV/EBITDA', value: f.ev_ebitda?.toFixed(1) || '—' },
    { label: 'EPS (TTM)', value: f.eps ? `$${f.eps.toFixed(2)}` : '—' },
    { label: 'Analyst Target', value: f.analyst_target ? `$${f.analyst_target.toFixed(2)}` : '—' },
    {
      label: 'RSI (14)', value: lastRsi.toFixed(1),
      color: lastRsi > 70 ? 'var(--error)' : lastRsi < 30 ? 'var(--success)' : 'var(--txt-1)',
    },
  ]
})

const fundamentalRows = computed(() => {
  const f = fundamentalsData.value || {}
  return [
    { label: 'Revenue', value: f.revenue ? `$${(f.revenue/1e9).toFixed(1)}B` : '—' },
    { label: 'Net Income', value: f.net_income ? `$${(f.net_income/1e9).toFixed(1)}B` : '—' },
    { label: 'Gross Margin', value: f.gross_margin ? `${(f.gross_margin*100).toFixed(1)}%` : '—' },
    { label: 'Op. Margin', value: f.operating_margin ? `${(f.operating_margin*100).toFixed(1)}%` : '—' },
    { label: 'ROE', value: f.roe ? `${(f.roe*100).toFixed(1)}%` : '—' },
    { label: 'Debt/Equity', value: f.debt_to_equity?.toFixed(2) || '—' },
    { label: 'P/B Ratio', value: (f.pb_ratio ?? f.price_to_book) ? ((f.pb_ratio ?? f.price_to_book).toFixed(2)) : '—' },
    { label: 'Dividend Yield', value: f.dividend_yield ? `${(f.dividend_yield*100).toFixed(2)}%` : '—' },
  ]
})

function toggleMA(ma: string) {
  if (activeMA.value.includes(ma)) activeMA.value = activeMA.value.filter(m => m !== ma)
  else activeMA.value.push(ma)
}

const priceChartOption = computed(() => {
  const d = dates.value
  const c = closes.value
  const v = volumes.value
  const series: any[] = [{
    name: ticker.value,
    type: 'line',
    data: c,
    smooth: false,
    symbol: 'none',
    lineStyle: { color: '#4f7ef8', width: 2 },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(79,126,248,0.15)' }, { offset: 1, color: 'rgba(79,126,248,0)' }] } },
    yAxisIndex: 0,
  }]
  if (activeMA.value.includes('MA20'))  series.push({ name:'MA20', type:'line', data: calcMA(c, 20), smooth:true, symbol:'none', lineStyle:{color:'#fdd663',width:1.5,opacity:0.8}, yAxisIndex:0 })
  if (activeMA.value.includes('MA50'))  series.push({ name:'MA50', type:'line', data: calcMA(c, 50), smooth:true, symbol:'none', lineStyle:{color:'#f28b82',width:1.5,opacity:0.8}, yAxisIndex:0 })
  if (activeMA.value.includes('MA200')) series.push({ name:'MA200',type:'line', data: calcMA(c,200), smooth:true, symbol:'none', lineStyle:{color:'#81c995',width:1.5,opacity:0.8}, yAxisIndex:0 })
  series.push({ name:'Volume', type:'bar', data:v, barWidth:'60%', itemStyle:{color:'rgba(79,126,248,0.2)',borderRadius:[2,2,0,0]}, yAxisIndex:1 })
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'var(--bg-elevated)', borderColor: 'var(--border-s)', textStyle:{color:'var(--txt-1)',fontSize:12} },
    legend: { data: ['MA20','MA50','MA200'].filter(m => activeMA.value.includes(m)), textStyle:{color:'var(--txt-2)',fontSize:11}, top:0 },
    grid: { top:32, bottom:40, left:60, right:60 },
    xAxis: { type:'category', data:d, axisLabel:{color:'var(--txt-3)',fontSize:11,rotate:0,interval:'auto'}, axisLine:{lineStyle:{color:'var(--border)'}}, splitLine:{show:false} },
    yAxis: [
      { type:'value', scale:true, axisLabel:{color:'var(--txt-3)',fontSize:11,formatter:(v:number)=>`$${v.toFixed(0)}`}, splitLine:{lineStyle:{color:'var(--border)',type:'dashed'}}, axisLine:{show:false} },
      { type:'value', scale:true, axisLabel:{show:false}, splitLine:{show:false}, axisLine:{show:false} },
    ],
    series,
  }
})

const rsiChartOption = computed(() => {
  const rsi = calcRSI(closes.value)
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger:'axis', backgroundColor:'var(--bg-elevated)', borderColor:'var(--border-s)', textStyle:{color:'var(--txt-1)',fontSize:12} },
    grid: { top:8, bottom:24, left:44, right:8 },
    xAxis: { type:'category', data:dates.value, show:false },
    yAxis: { type:'value', min:0, max:100, splitLine:{lineStyle:{color:'var(--border)',type:'dashed'}}, axisLabel:{color:'var(--txt-3)',fontSize:10} },
    series: [
      { type:'line', data:rsi, smooth:true, symbol:'none', lineStyle:{color:'#818cf8',width:1.5},
        markLine:{ silent:true, data:[{yAxis:70,lineStyle:{color:'var(--error)',type:'dashed',width:1}},{yAxis:30,lineStyle:{color:'var(--success)',type:'dashed',width:1}}], label:{show:false} } },
    ],
  }
})

const macdChartOption = computed(() => {
  if (!closes.value.length) return {}
  const { macd, signal, hist } = calcMACD(closes.value)
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger:'axis', backgroundColor:'var(--bg-elevated)', borderColor:'var(--border-s)', textStyle:{color:'var(--txt-1)',fontSize:12} },
    grid: { top:8, bottom:24, left:44, right:8 },
    xAxis: { type:'category', data:dates.value, show:false },
    yAxis: { type:'value', scale:true, splitLine:{lineStyle:{color:'var(--border)',type:'dashed'}}, axisLabel:{color:'var(--txt-3)',fontSize:10} },
    series: [
      { name:'MACD',   type:'line', data:macd,   smooth:true, symbol:'none', lineStyle:{color:'#4f7ef8',width:1.5} },
      { name:'Signal', type:'line', data:signal, smooth:true, symbol:'none', lineStyle:{color:'#fdd663',width:1.5} },
      { name:'Hist',   type:'bar',  data:hist,   itemStyle:{color:(params: any) => params.data >= 0 ? 'rgba(129,201,149,0.7)' : 'rgba(242,139,130,0.7)'}, barWidth:'60%' },
    ],
  }
})

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [stockRes, fundRes, peersRes] = await Promise.allSettled([
      fetchStock(ticker.value, period.value),
      fetchFundamentals(ticker.value),
      fetchPeers(ticker.value),
    ])
    if (stockRes.status === 'fulfilled') stockInfo.value = stockRes.value
    else throw new Error('Failed to load stock data')
    if (fundRes.status === 'fulfilled') fundamentalsData.value = fundRes.value
    if (peersRes.status === 'fulfilled') peers.value = peersRes.value?.peers || peersRes.value || []
  } catch (e: any) {
    error.value = e.message || 'Failed to load data'
  } finally {
    loading.value = false
  }
}

async function runAnalysis() {
  await start({
    ticker: ticker.value,
    date: new Date().toISOString().split('T')[0],
    analysts: ['market', 'social', 'news', 'fundamentals'],
    provider: agentStore.provider,
    deepModel: agentStore.deepModel,
    quickModel: agentStore.quickModel,
  })
}

function hoverRow(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.background = on ? 'var(--bg-hover)' : 'transparent'
}

watch(ticker, loadData)
onMounted(loadData)
</script>
