<template>
  <div style="padding:24px; max-width:1100px; margin:0 auto;">

    <!-- Header -->
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:24px;">
      <div>
        <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Datasets</h1>
        <p style="font-size:13px; color:var(--txt-3);">Manage financial data sources and exports</p>
      </div>
      <label class="btn-primary" style="display:flex; align-items:center; gap:6px; cursor:pointer;">
        <UploadIcon :size="14" />
        Import Dataset
        <input type="file" accept=".csv,.xlsx,.xls" style="display:none;" @change="handleImport" />
      </label>
    </div>

    <!-- Stats -->
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:24px;">
      <div class="card" style="padding:14px;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:4px;">Total Datasets</p>
        <p style="font-size:22px; font-weight:700; color:var(--txt-1);">{{ datasets.length }}</p>
      </div>
      <div class="card" style="padding:14px;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:4px;">Total Records</p>
        <p style="font-size:22px; font-weight:700; color:var(--primary);">{{ totalRecords.toLocaleString() }}</p>
      </div>
      <div class="card" style="padding:14px;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:4px;">Last Updated</p>
        <p style="font-size:15px; font-weight:600; color:var(--txt-1);">Today</p>
      </div>
      <div class="card" style="padding:14px;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:4px;">Data Sources</p>
        <p style="font-size:22px; font-weight:700; color:var(--success);">3</p>
      </div>
    </div>

    <!-- Dataset Table -->
    <div class="card">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1);">Available Datasets</h3>
        <div style="position:relative;">
          <SearchIcon :size="14" color="var(--txt-3)" style="position:absolute; left:10px; top:50%; transform:translateY(-50%);" />
          <input v-model="search" placeholder="Search..." class="input-base" style="padding-left:32px;" />
        </div>
      </div>
      <table style="width:100%; border-collapse:collapse;">
        <thead>
          <tr style="border-bottom:1px solid var(--border);">
            <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Name</th>
            <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Type</th>
            <th style="text-align:right; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Records</th>
            <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Source</th>
            <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Updated</th>
            <th style="text-align:left; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Status</th>
            <th style="text-align:right; padding:8px 12px; font-size:11px; color:var(--txt-3); font-weight:500;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="ds in filteredDatasets"
            :key="ds.id"
            style="border-bottom:1px solid var(--border);"
            @mouseenter="hoverRow($event, true)"
            @mouseleave="hoverRow($event, false)"
          >
            <td style="padding:12px; font-size:12px; font-weight:500; color:var(--txt-1);">{{ ds.name }}</td>
            <td style="padding:12px;">
              <span style="font-size:10px; padding:2px 8px; border-radius:4px; background:var(--primary-dim); color:var(--primary-txt);">{{ ds.type }}</span>
            </td>
            <td style="padding:12px; font-size:12px; color:var(--txt-2); text-align:right;">{{ ds.records.toLocaleString() }}</td>
            <td style="padding:12px; font-size:12px; color:var(--txt-2);">{{ ds.source }}</td>
            <td style="padding:12px; font-size:12px; color:var(--txt-3);">{{ ds.updated }}</td>
            <td style="padding:12px;">
              <span :style="{
                fontSize:'10px', padding:'2px 8px', borderRadius:'20px',
                background: ds.status === 'active' ? 'var(--success-dim)' : 'var(--warning-dim)',
                color: ds.status === 'active' ? 'var(--success)' : 'var(--warning)',
              }">{{ ds.status }}</span>
            </td>
            <td style="padding:12px; text-align:right;">
              <div style="display:flex; align-items:center; justify-content:flex-end; gap:6px;">
                <button style="background:none; border:none; cursor:pointer; color:var(--txt-3); padding:4px;" title="Download" @click="downloadDataset(ds)">
                  <DownloadIcon :size="14" />
                </button>
                <button style="background:none; border:none; cursor:pointer; color:var(--txt-3); padding:4px;" title="Refresh" @click="refreshDataset(ds)">
                  <RefreshCwIcon :size="14" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload as UploadIcon, Search as SearchIcon, Download as DownloadIcon, RefreshCw as RefreshCwIcon } from 'lucide-vue-next'
import api from '../api/index'

const search = ref('')

const datasets = ref([
  { id: 1, name: 'US Equities Daily (OHLCV)',   type: 'Price',        records: 2847320, source: 'Yahoo Finance', updated: '2026-03-24', status: 'active' },
  { id: 2, name: 'S&P 500 Fundamentals',         type: 'Fundamental',  records: 125000,  source: 'SEC EDGAR',    updated: '2026-03-22', status: 'active' },
  { id: 3, name: 'A-Share Market Data',           type: 'Price',        records: 980000,  source: 'AKShare',      updated: '2026-03-24', status: 'active' },
  { id: 4, name: 'Market Sentiment (Twitter)',    type: 'Sentiment',    records: 4500000, source: 'Twitter/X',    updated: '2026-03-20', status: 'stale' },
  { id: 5, name: 'Financial News Corpus',         type: 'News',         records: 250000,  source: 'NewsAPI',      updated: '2026-03-23', status: 'active' },
  { id: 6, name: 'Crypto Daily Prices',           type: 'Price',        records: 560000,  source: 'CoinGecko',    updated: '2026-03-24', status: 'active' },
])

// Load uploaded datasets from backend and merge
;(async () => {
  try {
    const res = await api.get('/api/datasets')
    const uploaded = res.data.map((d: any) => ({
      id: `db_${d.id}`, name: d.name, type: 'Uploaded', records: d.rows,
      source: 'User Upload', updated: d.updated || d.created, status: d.status === 'analyzed' ? 'active' : d.status
    }))
    datasets.value = [...datasets.value, ...uploaded]
  } catch {}
})()

const totalRecords = computed(() => datasets.value.reduce((sum, d) => sum + d.records, 0))

const filteredDatasets = computed(() =>
  datasets.value.filter(d => !search.value || d.name.toLowerCase().includes(search.value.toLowerCase()))
)

function hoverRow(e: Event, on: boolean) {
  const el = e.currentTarget as HTMLElement
  el.style.background = on ? 'var(--bg-hover)' : 'transparent'
}

async function handleImport(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  try {
    const res = await api.post('/api/datasets/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    const d = res.data
    const today = new Date().toISOString().split('T')[0]
    datasets.value.unshift({ id: `db_${d.id}`, name: d.name, type: 'Uploaded', records: Number(d.rows), source: 'User Upload', updated: today, status: 'active' })
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Upload failed')
  }
}

function downloadDataset(ds: any) {
  alert(`Download for "${ds.name}" is not yet implemented for external data sources.`)
}

function refreshDataset(ds: any) {
  const idx = datasets.value.findIndex(d => d.id === ds.id)
  if (idx >= 0) {
    const today = new Date().toISOString().split('T')[0]
    datasets.value[idx] = { ...datasets.value[idx], updated: today }
  }
}
</script>
