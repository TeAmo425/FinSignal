<template>
  <div style="padding:24px; max-width:1100px; margin:0 auto;">

    <!-- Header -->
    <div style="margin-bottom:24px;">
      <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Forecast</h1>
      <p style="font-size:13px; color:var(--txt-3);">LSTM + fundamentals-based price forecasting</p>
    </div>

    <!-- Controls -->
    <div class="card" style="margin-bottom:20px; padding:16px;">
      <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
        <div>
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Symbol</label>
          <input v-model="symbol" type="text" placeholder="AAPL" class="input-base" style="width:120px; text-transform:uppercase;" @input="symbol = String(symbol).toUpperCase()" />
        </div>
        <div>
          <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Horizon (days)</label>
          <div style="display:flex; gap:6px;">
            <button
              v-for="h in [7, 14, 30, 90]"
              :key="h"
              @click="horizon = h"
              :style="{
                padding:'6px 12px', borderRadius:'6px', border:'1px solid', cursor:'pointer', fontSize:'12px',
                background: horizon === h ? 'var(--primary-dim)' : 'var(--bg-elevated)',
                borderColor: horizon === h ? 'var(--primary)' : 'var(--border)',
                color: horizon === h ? 'var(--primary-txt)' : 'var(--txt-2)',
              }"
            >{{ h }}d</button>
          </div>
        </div>
        <button @click="runForecast" class="btn-primary" :disabled="loading || !symbol" style="margin-top:16px;">
          <span style="display:flex; align-items:center; gap:6px;">
            <div v-if="loading" class="spinner" style="border-top-color:#fff;"></div>
            <TrendingUpIcon v-else :size="14" />
            {{ loading ? 'Forecasting...' : 'Run Forecast' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" style="padding:12px 16px; background:var(--error-dim); border:1px solid var(--error); border-radius:10px; color:var(--error); font-size:13px; margin-bottom:20px;">
      {{ error }}
    </div>

    <template v-if="forecastData">

      <!-- Stat Cards -->
      <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:20px;">
        <div class="card" style="padding:16px; text-align:center;">
          <p style="font-size:11px; color:var(--txt-3); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">Predicted Trend</p>
          <p style="font-size:18px; font-weight:700;" :style="{ color: trend === 'BULLISH' ? 'var(--success)' : trend === 'BEARISH' ? 'var(--error)' : 'var(--warning)' }">
            {{ trend }}
          </p>
        </div>
        <div class="card" style="padding:16px; text-align:center;">
          <p style="font-size:11px; color:var(--txt-3); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">Expected Range</p>
          <p style="font-size:15px; font-weight:600; color:var(--txt-1);">${{ forecastData.price_range?.[0]?.toFixed(2) }} – ${{ forecastData.price_range?.[1]?.toFixed(2) }}</p>
        </div>
        <div class="card" style="padding:16px; text-align:center;">
          <p style="font-size:11px; color:var(--txt-3); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">Model Confidence</p>
          <p style="font-size:18px; font-weight:700; color:var(--primary);">{{ forecastData.confidence ? `${forecastData.confidence.toFixed(0)}%` : '—' }}</p>
        </div>
      </div>

      <!-- Forecast Chart -->
      <div class="card" style="margin-bottom:20px;">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:16px;">
          {{ symbol }} – {{ horizon }}-Day Forecast
        </h3>
        <v-chart :option="chartOption" style="width:100%; height:340px;" :autoresize="true" />
      </div>

      <!-- Fundamentals Input Panel -->
      <div class="card">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:16px;">Fundamentals Input</h3>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
          <div v-for="metric in fundamentalMetrics" :key="metric.key">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
              <span style="font-size:12px; color:var(--txt-2);">{{ metric.label }}</span>
              <span style="font-size:12px; font-weight:500; color:var(--txt-1);">{{ forecastData.fundamentals_used?.[metric.key]?.toFixed(metric.decimals) ?? '—' }}</span>
            </div>
            <div style="height:4px; background:var(--bg-elevated); border-radius:2px; overflow:hidden;">
              <div :style="{ width: `${Math.min(100, (forecastData.fundamentals_used?.[metric.key] || 0) * metric.scale)}%`, height:'100%', background:'var(--primary)', borderRadius:'2px', transition:'width 0.3s' }"></div>
            </div>
          </div>
        </div>
      </div>

    </template>

    <!-- Empty State -->
    <div v-else-if="!loading" class="card" style="text-align:center; padding:80px 20px;">
      <TrendingUpIcon :size="40" color="var(--txt-3)" style="margin:0 auto 12px;" />
      <p style="font-size:14px; color:var(--txt-2); margin-bottom:6px;">Enter a symbol and run forecast</p>
      <p style="font-size:12px; color:var(--txt-3);">Uses LSTM neural network + fundamental data</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { TrendingUp as TrendingUpIcon } from 'lucide-vue-next'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { fetchForecast } from '../api/index'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const symbol = ref('AAPL')
const horizon = ref(30)
const loading = ref(false)
const error = ref('')
const forecastData = ref<any>(null)

const trend = computed(() => {
  if (!forecastData.value) return ''
  // API returns 'trend' field directly; fallback to computing from forecast prices
  if (forecastData.value.trend) {
    const t = forecastData.value.trend.toUpperCase()
    if (t === 'BULLISH' || t === 'BEARISH') return t
  }
  const last = forecastData.value.forecast?.slice(-1)[0]?.forecast
  const first = forecastData.value.forecast?.[0]?.forecast
  if (!last || !first) return 'NEUTRAL'
  const pct = (last - first) / first * 100
  if (pct > 2) return 'BULLISH'
  if (pct < -2) return 'BEARISH'
  return 'NEUTRAL'
})

// Keys match API response: fundamentals_used from LSTM model
const fundamentalMetrics = [
  { key: 'P/E',             label: 'P/E Ratio',      decimals: 2, scale: 100 },
  { key: 'Forward P/E',     label: 'Forward P/E',    decimals: 2, scale: 100 },
  { key: 'Revenue Growth',  label: 'Revenue Growth', decimals: 2, scale: 100 },
  { key: 'Profit Margin',   label: 'Profit Margin',  decimals: 2, scale: 100 },
  { key: 'ROE',             label: 'ROE',            decimals: 2, scale: 100 },
  { key: 'D/E',             label: 'Debt/Equity',    decimals: 2, scale: 100 },
  { key: 'EV/EBITDA',       label: 'EV/EBITDA',      decimals: 2, scale: 100 },
  { key: 'Beta',            label: 'Beta',           decimals: 2, scale: 100 },
]

// 3-point moving average to smooth jagged forecast data
function smoothPrices(prices: number[]): number[] {
  return prices.map((v, i, arr) => {
    if (i === 0) return v
    if (i === arr.length - 1) return v
    return (arr[i - 1] + v + arr[i + 1]) / 3
  })
}

const chartOption = computed(() => {
  if (!forecastData.value) return {}
  const hist = forecastData.value.historical || forecastData.value.history || []
  const fcast = forecastData.value.forecast || []
  const histDates = hist.map((p: any) => p.date)
  const histPrices = hist.map((p: any) => p.close || p.price)
  const fcastDates = fcast.map((p: any) => p.date)
  const rawFcast  = fcast.map((p: any) => p.forecast ?? p.price)
  const rawLow    = fcast.map((p: any) => p.lower  ?? (p.forecast ?? p.price) * 0.97)
  const rawHigh   = fcast.map((p: any) => p.upper  ?? (p.forecast ?? p.price) * 1.03)
  // Apply smoothing
  const fcastPrices = smoothPrices(rawFcast)
  const fcastLow    = smoothPrices(rawLow)
  const fcastHigh   = smoothPrices(rawHigh)
  // Band = lower base + (upper - lower) height, stacked
  const bandBase   = fcastLow
  const bandHeight = fcastHigh.map((h, i) => h - fcastLow[i])
  // Shift all forecast values so the line starts exactly at the last historical price
  const lastHistPrice = histPrices[histPrices.length - 1] ?? 0
  const offset = lastHistPrice - (fcastPrices[0] ?? lastHistPrice)
  const shiftedFcast  = fcastPrices.map(v => v + offset)
  const shiftedLow    = fcastLow.map(v => v + offset)
  const shiftedHigh   = fcastHigh.map(v => v + offset)
  const shiftedBase   = shiftedLow
  const shiftedHeight = shiftedHigh.map((h, i) => h - shiftedLow[i])

  const nullHistBridge = new Array(histDates.length - 1).fill(null)
  const nullFcast      = new Array(fcastDates.length).fill(null)

  return {
    backgroundColor: 'transparent',
    tooltip: { trigger:'axis', backgroundColor:'var(--bg-elevated)', borderColor:'var(--border-s)', textStyle:{color:'var(--txt-1)',fontSize:12} },
    legend: { data:['Historical','Forecast','Confidence Band'], textStyle:{color:'var(--txt-2)',fontSize:11}, top:0 },
    grid: { top:36, bottom:40, left:60, right:20 },
    xAxis: {
      type: 'category',
      data: [...histDates, ...fcastDates],
      axisLabel: { color:'var(--txt-3)', fontSize:11 },
      axisLine: { lineStyle:{ color:'var(--border)' } },
      splitLine: { show:false },
    },
    yAxis: {
      type: 'value', scale: true,
      axisLabel: { color:'var(--txt-3)', fontSize:11, formatter: (v: number) => `$${v.toFixed(0)}` },
      splitLine: { lineStyle:{ color:'var(--border)', type:'dashed' } },
    },
    series: [
      {
        name: 'Historical', type:'line',
        data:[...histPrices, ...nullFcast],
        smooth: 0.3, symbol:'none', lineStyle:{color:'#4f7ef8',width:2},
        areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(79,126,248,0.1)'},{offset:1,color:'rgba(79,126,248,0)'}]}},
      },
      {
        name: 'Forecast', type:'line',
        data:[...nullHistBridge, lastHistPrice, ...shiftedFcast],
        smooth: 0.5, symbol:'none', lineStyle:{color:'#81c995',width:2.5,type:'dashed'},
      },
      {
        name: 'Band Base', type:'line',
        data:[...nullHistBridge, lastHistPrice, ...shiftedBase],
        smooth: 0.5, symbol:'none', lineStyle:{opacity:0},
        areaStyle:{color:'transparent'},
        stack:'conf_band', legendHoverLink: false, tooltip:{show:false},
      },
      {
        name: 'Confidence Band', type:'line',
        data:[...nullHistBridge, 0, ...shiftedHeight],
        smooth: 0.5, symbol:'none', lineStyle:{opacity:0},
        areaStyle:{color:'rgba(129,201,149,0.13)'},
        stack:'conf_band',
      },
    ],
  }
})

async function runForecast() {
  if (!symbol.value.trim()) return
  loading.value = true
  error.value = ''
  forecastData.value = null
  try {
    forecastData.value = await fetchForecast(symbol.value.trim().toUpperCase(), horizon.value)
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Forecast failed'
  } finally {
    loading.value = false
  }
}
</script>
