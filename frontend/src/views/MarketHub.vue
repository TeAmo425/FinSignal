<template>
  <div style="padding:24px; max-width:1400px; margin:0 auto;">

    <!-- Header -->
    <div style="margin-bottom:24px;">
      <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Market Hub</h1>
      <p style="font-size:13px; color:var(--txt-3);">Search and explore US equities</p>
    </div>

    <!-- Search Bar -->
    <div style="margin-bottom:24px; display:flex; gap:10px; max-width:500px;">
      <div style="position:relative; flex:1;">
        <SearchIcon :size="16" color="var(--txt-3)" style="position:absolute; left:10px; top:50%; transform:translateY(-50%);" />
        <input
          v-model="searchQuery"
          @input="onSearch"
          @keydown.enter="goToStock"
          type="text"
          placeholder="Search symbol or company (e.g. AAPL, Apple)"
          class="input-base"
          style="width:100%; padding-left:36px;"
        />
      </div>
      <button @click="goToStock" class="btn-primary" :disabled="!searchQuery.trim()">
        Search
      </button>
    </div>

    <!-- Search Results Dropdown -->
    <div v-if="searchResults.length" style="position:relative; z-index:10; margin-top:-18px; margin-bottom:16px; max-width:500px;">
      <div style="background:var(--bg-elevated); border:1px solid var(--border-s); border-radius:10px; overflow:hidden; box-shadow:0 8px 24px rgba(0,0,0,0.4);">
        <div
          v-for="result in searchResults.slice(0, 6)"
          :key="result.symbol"
          @click="selectResult(result)"
          style="padding:10px 14px; cursor:pointer; display:flex; align-items:center; gap:10px; border-bottom:1px solid var(--border);"
          @mouseenter="hoverRow($event, true)"
          @mouseleave="hoverRow($event, false)"
        >
          <span style="font-size:13px; font-weight:700; color:var(--primary); width:60px;">{{ result.symbol }}</span>
          <span style="font-size:12px; color:var(--txt-2);">{{ result.name }}</span>
          <span style="font-size:11px; color:var(--txt-3); margin-left:auto;">{{ result.exchange }}</span>
        </div>
      </div>
    </div>

    <!-- Featured Stocks -->
    <div>
      <p class="section-title" style="margin-bottom:12px;">Featured Stocks</p>
      <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:16px;">
        <div
          v-for="ticker in featured"
          :key="ticker"
          class="card"
          style="cursor:pointer; transition:border-color 0.15s, transform 0.1s;"
          @mouseenter="hoverCard($event, true)"
          @mouseleave="hoverCard($event, false)"
          @click="router.push(`/stock/${ticker}`)"
        >
          <div style="display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:12px;">
            <div>
              <p style="font-size:15px; font-weight:700; color:var(--txt-1);">{{ ticker }}</p>
              <p style="font-size:11px; color:var(--txt-3);">{{ companyNames[ticker] }}</p>
            </div>
            <div v-if="stockData[ticker]">
              <p :style="{ fontSize:'11px', color: stockData[ticker].change >= 0 ? 'var(--success)' : 'var(--error)', fontWeight:'600', textAlign:'right' }">
                {{ stockData[ticker].change >= 0 ? '+' : '' }}{{ stockData[ticker].change?.toFixed(2) }}%
              </p>
              <p style="font-size:11px; color:var(--txt-3); text-align:right;">Today</p>
            </div>
          </div>

          <div v-if="stockData[ticker]" style="margin-bottom:12px;">
            <p style="font-size:22px; font-weight:600; color:var(--txt-1);">${{ stockData[ticker].price?.toFixed(2) }}</p>
          </div>
          <div v-else style="margin-bottom:12px;">
            <div class="pulse-soft" style="height:22px; width:80px; background:var(--bg-elevated); border-radius:4px;"></div>
          </div>

          <!-- Sparkline -->
          <div v-if="sparkData[ticker]" style="height:40px;">
            <v-chart :option="getSparkOption(ticker)" style="width:100%; height:40px;" :autoresize="true" />
          </div>
          <div v-else style="height:40px; background:var(--bg-elevated); border-radius:6px;" class="pulse-soft"></div>

          <div style="display:flex; align-items:center; justify-content:space-between; margin-top:10px;">
            <span style="font-size:11px; color:var(--txt-3);">Vol: {{ stockData[ticker]?.volume ? formatVolume(stockData[ticker].volume) : '—' }}</span>
            <RouterLink :to="`/stock/${ticker}`" @click.stop style="font-size:11px; color:var(--primary-txt);">Details →</RouterLink>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { Search as SearchIcon } from 'lucide-vue-next'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { fetchStock, searchStocks } from '../api/index'

use([LineChart, GridComponent, CanvasRenderer])

const router = useRouter()

const featured = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL']
const companyNames: Record<string, string> = {
  AAPL: 'Apple Inc.', NVDA: 'NVIDIA Corp.', TSLA: 'Tesla Inc.', MSFT: 'Microsoft Corp.', GOOGL: 'Alphabet Inc.',
}

const searchQuery = ref('')
const searchResults = ref<{ symbol: string; name: string; exchange: string }[]>([])
const stockData = ref<Record<string, { price: number; change: number; volume: number }>>({})
const sparkData = ref<Record<string, number[]>>({})

let searchTimeout: ReturnType<typeof setTimeout>
function onSearch() {
  clearTimeout(searchTimeout)
  if (!searchQuery.value.trim()) { searchResults.value = []; return }
  searchTimeout = setTimeout(async () => {
    try {
      const res = await searchStocks(searchQuery.value)
      searchResults.value = res.results || res || []
    } catch { searchResults.value = [] }
  }, 300)
}

function goToStock() {
  const q = searchQuery.value.trim().toUpperCase()
  if (q) { searchResults.value = []; router.push(`/stock/${q}`) }
}

function selectResult(result: { symbol: string; name: string; exchange: string }) {
  searchResults.value = []
  searchQuery.value = ''
  router.push(`/stock/${result.symbol}`)
}

function formatVolume(v: number): string {
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`
  return String(v)
}

function normalize(arr: number[]): number[] {
  const min = Math.min(...arr), max = Math.max(...arr)
  if (max === min) return arr.map(() => 50)
  return arr.map(v => ((v - min) / (max - min)) * 100)
}

function getSparkOption(ticker: string) {
  const data = sparkData.value[ticker] || []
  const isUp = data.length >= 2 && data[data.length - 1] >= data[0]
  return {
    backgroundColor: 'transparent',
    grid: { top: 0, bottom: 0, left: 0, right: 0 },
    xAxis: { type: 'category', show: false, data: data.map((_, i) => i) },
    yAxis: { type: 'value', show: false, min: 0, max: 100 },
    series: [{
      type: 'line',
      data: normalize(data),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: isUp ? '#81c995' : '#f28b82', width: 1.5 },
      areaStyle: { color: isUp ? 'rgba(129,201,149,0.08)' : 'rgba(242,139,130,0.08)' },
    }],
  }
}

async function loadStock(ticker: string) {
  try {
    const data = await fetchStock(ticker, '1mo')
    const prices = data.data || data.prices || data.history || []
    if (prices.length >= 2) {
      const last = prices[prices.length - 1]
      const prev = prices[prices.length - 2]
      stockData.value[ticker] = {
        price: last.close || 0,
        change: prev.close ? ((last.close - prev.close) / prev.close) * 100 : 0,
        volume: last.volume || 0,
      }
      sparkData.value[ticker] = prices.slice(-30).map((p: any) => p.close || 0)
    }
  } catch { /* ignore */ }
}

function hoverRow(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.background = on ? 'var(--bg-hover)' : 'transparent'
}

function hoverCard(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.borderColor = on ? 'var(--border-s)' : 'var(--border)'
  el.style.transform = on ? 'translateY(-1px)' : 'translateY(0)'
}

onMounted(() => { featured.forEach(loadStock) })
</script>
