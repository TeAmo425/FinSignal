<template>
  <div style="padding:24px; max-width:1100px; margin:0 auto;">

    <!-- Header -->
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:24px;">
      <div>
        <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Reports</h1>
        <p style="font-size:13px; color:var(--txt-3);">AI-generated trading analysis reports</p>
      </div>
      <div style="display:flex; gap:8px;">
        <button v-if="allReports.length" @click="clearAll" style="background:var(--error-dim); border:1px solid var(--error); color:var(--error); padding:7px 12px; border-radius:8px; cursor:pointer; font-size:12px;">
          Clear All
        </button>
        <button class="btn-primary" style="display:flex; align-items:center; gap:6px;" @click="router.push('/trading-agents')">
          <PlusIcon :size="14" />
          New Report
        </button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
      <div style="position:relative; flex:1; max-width:300px;">
        <SearchIcon :size="14" color="var(--txt-3)" style="position:absolute; left:10px; top:50%; transform:translateY(-50%);" />
        <input v-model="searchQuery" placeholder="Search by ticker..." class="input-base" style="width:100%; padding-left:32px;" />
      </div>
      <select v-model="filterDecision" class="input-base" style="padding:8px 10px;">
        <option value="">All Decisions</option>
        <option value="BUY">BUY</option>
        <option value="SELL">SELL</option>
        <option value="HOLD">HOLD</option>
      </select>
    </div>

    <!-- Stats Row -->
    <div v-if="allReports.length" style="display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:20px;">
      <div class="card" style="padding:12px; text-align:center;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:2px;">Total Reports</p>
        <p style="font-size:20px; font-weight:700; color:var(--txt-1);">{{ allReports.length }}</p>
      </div>
      <div class="card" style="padding:12px; text-align:center;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:2px;">BUY</p>
        <p style="font-size:20px; font-weight:700; color:var(--success);">{{ countDecision('BUY') }}</p>
      </div>
      <div class="card" style="padding:12px; text-align:center;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:2px;">SELL</p>
        <p style="font-size:20px; font-weight:700; color:var(--error);">{{ countDecision('SELL') }}</p>
      </div>
      <div class="card" style="padding:12px; text-align:center;">
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:2px;">HOLD</p>
        <p style="font-size:20px; font-weight:700; color:var(--warning);">{{ countDecision('HOLD') }}</p>
      </div>
    </div>

    <!-- Reports Grid -->
    <div v-if="filteredReports.length" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:16px;">
      <div
        v-for="report in filteredReports"
        :key="report.id"
        class="card"
        style="cursor:pointer; transition:border-color 0.15s; position:relative;"
        @click="openReport(report)"
        @mouseenter="hoverBorder($event, 'var(--border-s)')"
        @mouseleave="hoverBorder($event, 'var(--border)')"
      >
        <!-- Delete button -->
        <button
          @click.stop="deleteReport(report.id)"
          style="position:absolute; top:10px; right:10px; background:none; border:none; cursor:pointer; color:var(--txt-3); padding:2px; line-height:1; border-radius:4px; opacity:0.6;"
          @mouseenter="(e: Event) => (e.currentTarget as HTMLElement).style.opacity='1'"
          @mouseleave="(e: Event) => (e.currentTarget as HTMLElement).style.opacity='0.6'"
          title="Delete"
        >
          <XIcon :size="14" />
        </button>

        <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:10px; padding-right:20px;">
          <div style="width:36px; height:36px; border-radius:8px; background:var(--primary-dim); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
            <BotIcon :size="18" color="var(--primary)" />
          </div>
          <div style="flex:1; min-width:0;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;">
              <p style="font-size:14px; font-weight:700; color:var(--txt-1);">{{ report.ticker }}</p>
              <span :class="['badge', report.decision === 'BUY' ? 'badge-buy' : report.decision === 'SELL' ? 'badge-sell' : report.decision === 'HOLD' ? 'badge-hold' : 'badge-neutral']">
                {{ report.decision || '—' }}
              </span>
            </div>
            <p style="font-size:11px; color:var(--txt-3);">{{ report.provider }} · {{ report.date }}</p>
          </div>
        </div>
        <p style="font-size:12px; color:var(--txt-2); line-height:1.6; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;">
          {{ report.summary }}
        </p>
        <div style="display:flex; align-items:center; gap:6px; margin-top:10px; padding-top:10px; border-top:1px solid var(--border);">
          <span style="font-size:10px; color:var(--txt-3); background:var(--bg-elevated); padding:2px 8px; border-radius:20px;">{{ report.analysts }} analysts</span>
          <span style="font-size:10px; color:var(--txt-3);">{{ report.tradeDate }}</span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card" style="text-align:center; padding:80px 20px; margin-top:8px;">
      <FileTextIcon :size="40" color="var(--txt-3)" style="margin:0 auto 16px;" />
      <p style="font-size:15px; font-weight:600; color:var(--txt-2); margin-bottom:6px;">
        {{ searchQuery || filterDecision ? 'No matching reports' : 'No reports yet' }}
      </p>
      <p style="font-size:12px; color:var(--txt-3); margin-bottom:16px;">
        {{ searchQuery || filterDecision ? 'Try adjusting your filters' : 'Run a Trading Agents analysis to generate your first report' }}
      </p>
      <button v-if="!searchQuery && !filterDecision" class="btn-primary" @click="router.push('/trading-agents')" style="display:inline-flex; align-items:center; gap:6px;">
        <BotIcon :size="14" />
        Start Analysis
      </button>
    </div>

    <!-- Report Detail Modal -->
    <div v-if="selectedReport" style="position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:200; display:flex; align-items:center; justify-content:center; padding:24px;" @click.self="selectedReport = null">
      <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:14px; max-width:720px; width:100%; max-height:80vh; overflow-y:auto; padding:24px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <p style="font-size:18px; font-weight:700; color:var(--txt-1);">{{ selectedReport.ticker }}</p>
            <span :class="['badge', selectedReport.decision === 'BUY' ? 'badge-buy' : selectedReport.decision === 'SELL' ? 'badge-sell' : selectedReport.decision === 'HOLD' ? 'badge-hold' : 'badge-neutral']" style="font-size:12px;">
              {{ selectedReport.decision || '—' }}
            </span>
          </div>
          <button @click="selectedReport = null" style="background:none; border:none; cursor:pointer; color:var(--txt-3);">
            <XIcon :size="18" />
          </button>
        </div>
        <p style="font-size:11px; color:var(--txt-3); margin-bottom:16px;">{{ selectedReport.provider }} · {{ selectedReport.date }} · Trade date: {{ selectedReport.tradeDate }}</p>
        <div v-for="section in selectedReport.sections" :key="section.agent" style="margin-bottom:14px; padding:12px 14px; background:var(--bg-elevated); border-radius:8px;">
          <p style="font-size:12px; font-weight:600; color:var(--txt-1); margin-bottom:6px;">{{ section.label }}</p>
          <pre style="font-size:11px; color:var(--txt-2); white-space:pre-wrap; line-height:1.6; font-family:inherit;">{{ section.content }}</pre>
        </div>
        <div style="display:flex; gap:8px; margin-top:16px;">
          <button @click="router.push('/trading-agents'); selectedReport = null" class="btn-primary" style="flex:1; padding:10px; font-size:13px; display:flex; align-items:center; justify-content:center; gap:6px;">
            <BotIcon :size="14" />
            Re-run Analysis
          </button>
          <button @click="deleteReport(selectedReport!.id); selectedReport = null" style="padding:10px 16px; background:var(--error-dim); border:1px solid var(--error); color:var(--error); border-radius:8px; cursor:pointer; font-size:13px;">
            Delete
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus as PlusIcon, Search as SearchIcon, FileText as FileTextIcon, Bot as BotIcon, X as XIcon } from 'lucide-vue-next'

const router = useRouter()
const searchQuery = ref('')
const filterDecision = ref('')
const selectedReport = ref<any>(null)

interface Report {
  id: string
  ticker: string
  decision: string | null
  summary: string
  date: string
  tradeDate: string
  provider: string
  analysts: number
  sections: { agent: string; label: string; content: string }[]
}

const reports = ref<Report[]>([])

function loadReports() {
  try {
    // Load manually saved reports
    const saved = JSON.parse(localStorage.getItem('finagent_reports') || '[]')
    // Load from agent cache
    const cache = JSON.parse(localStorage.getItem('agentCache') || '{}')
    const cacheReports: Report[] = Object.entries(cache).map(([sym, data]: [string, any]) => {
      const results: any[] = data.results || []
      const pmResult = results.find((r: any) => r.agent === 'portfolio_manager' || r.field === 'final_trade_decision')
      const decisionMatch = pmResult?.content?.match(/\b(BUY|SELL|HOLD)\b/i)
      const summary = pmResult?.content?.slice(0, 300) || results[0]?.content?.slice(0, 300) || 'No summary available'
      return {
        id: `cache_${sym}`,
        ticker: sym,
        decision: decisionMatch ? decisionMatch[0].toUpperCase() : null,
        summary,
        date: new Date(data.timestamp || Date.now()).toLocaleDateString(),
        tradeDate: data.date || '—',
        provider: data.provider || 'AI',
        analysts: results.length,
        sections: results.map((r: any) => ({ agent: r.agent || r.field, label: r.label || r.agent, content: r.content })),
      }
    })
    reports.value = [...saved, ...cacheReports].sort((a, b) => b.date.localeCompare(a.date))
  } catch {
    reports.value = []
  }
}

onMounted(loadReports)

const allReports = computed(() => reports.value)

const filteredReports = computed(() =>
  reports.value.filter(r => {
    const matchSearch = !searchQuery.value || r.ticker.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchDecision = !filterDecision.value || r.decision === filterDecision.value
    return matchSearch && matchDecision
  })
)

function countDecision(d: string) {
  return reports.value.filter(r => r.decision === d).length
}

function openReport(report: Report) {
  selectedReport.value = report
}

function deleteReport(id: string) {
  if (id.startsWith('cache_')) {
    const sym = id.replace('cache_', '')
    try {
      const cache = JSON.parse(localStorage.getItem('agentCache') || '{}')
      delete cache[sym]
      localStorage.setItem('agentCache', JSON.stringify(cache))
    } catch {}
  } else {
    try {
      const saved = JSON.parse(localStorage.getItem('finagent_reports') || '[]')
      localStorage.setItem('finagent_reports', JSON.stringify(saved.filter((r: any) => r.id !== id)))
    } catch {}
  }
  loadReports()
}

function clearAll() {
  if (!confirm('Delete all reports?')) return
  localStorage.removeItem('finagent_reports')
  localStorage.removeItem('agentCache')
  loadReports()
}

function hoverBorder(e: Event, color: string) {
  const el = e.currentTarget as HTMLElement
  el.style.borderColor = color
}
</script>
