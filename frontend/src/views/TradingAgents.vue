<template>
  <div style="padding:24px; max-width:1200px; margin:0 auto;">

    <!-- Header -->
    <div style="margin-bottom:24px;">
      <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Trading Agents</h1>
      <p style="font-size:13px; color:var(--txt-3);">Multi-agent AI analysis with real-time SSE streaming</p>
    </div>

    <div style="display:grid; grid-template-columns:340px 1fr; gap:20px; align-items:start;">

      <!-- Config Panel -->
      <div style="display:flex; flex-direction:column; gap:14px;">

        <!-- Provider Selector -->
        <div class="card" style="padding:16px;">
          <p class="section-title" style="margin-bottom:10px;">LLM Provider</p>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
            <button
              v-for="(info, key) in PROVIDER_MODELS"
              :key="key"
              @click="selectProvider(key as LLMProvider)"
              :style="{
                padding:'8px 10px', borderRadius:'8px', border:'1px solid', cursor:'pointer', fontSize:'12px', fontWeight:'500', textAlign:'left',
                background: store.provider === key ? providerColors[key as LLMProvider].bg : 'var(--bg-elevated)',
                borderColor: store.provider === key ? providerColors[key as LLMProvider].border : 'var(--border)',
                color: store.provider === key ? providerColors[key as LLMProvider].text : 'var(--txt-2)',
              }"
            >{{ info.label }}</button>
          </div>
        </div>

        <!-- Ticker + Date -->
        <div class="card" style="padding:16px;">
          <p class="section-title" style="margin-bottom:10px;">Target</p>
          <div style="display:flex; flex-direction:column; gap:10px;">
            <div>
              <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Ticker Symbol</label>
              <input v-model="ticker" type="text" placeholder="AAPL" class="input-base" style="width:100%; text-transform:uppercase;" @input="ticker = String(ticker).toUpperCase()" />
            </div>
            <div>
              <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Trade Date</label>
              <input v-model="tradeDate" type="date" class="input-base" style="width:100%;" />
            </div>
          </div>
        </div>

        <!-- Analysts -->
        <div class="card" style="padding:16px;">
          <p class="section-title" style="margin-bottom:10px;">Analysts</p>
          <div style="display:flex; flex-direction:column; gap:8px;">
            <label
              v-for="analyst in analystOptions"
              :key="analyst.key"
              style="display:flex; align-items:center; gap:10px; cursor:pointer; padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg-elevated);"
            >
              <input type="checkbox" v-model="selectedAnalysts" :value="analyst.key" style="accent-color:var(--primary); width:14px; height:14px;" />
              <span style="font-size:13px; color:var(--txt-1);">{{ analyst.label }}</span>
              <span style="font-size:10px; color:var(--txt-3); margin-left:auto;">{{ analyst.desc }}</span>
            </label>
          </div>
        </div>

        <!-- Models -->
        <div class="card" style="padding:16px;">
          <p class="section-title" style="margin-bottom:10px;">Models</p>
          <div style="display:flex; flex-direction:column; gap:10px;">
            <div>
              <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Deep Model</label>
              <select v-model="deepModel" class="input-base" style="width:100%;">
                <option v-for="m in PROVIDER_MODEL_OPTIONS[store.provider].deep" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
            <div>
              <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Quick Model</label>
              <select v-model="quickModel" class="input-base" style="width:100%;">
                <option v-for="m in PROVIDER_MODEL_OPTIONS[store.provider].quick" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Advanced -->
        <div class="card" style="padding:16px;">
          <button @click="showAdvanced = !showAdvanced" style="background:none; border:none; cursor:pointer; display:flex; align-items:center; justify-content:space-between; width:100%; padding:0;">
            <p class="section-title" style="margin:0;">Advanced</p>
            <ChevronDownIcon :size="14" color="var(--txt-3)" :style="{ transform: showAdvanced ? 'rotate(180deg)' : 'none', transition:'transform 0.2s' }" />
          </button>
          <div v-if="showAdvanced" style="margin-top:12px; display:flex; flex-direction:column; gap:10px;">
            <div>
              <label style="font-size:11px; color:var(--txt-3); display:block; margin-bottom:4px;">Debate Rounds</label>
              <input v-model.number="debateRounds" type="number" min="1" max="5" class="input-base" style="width:100%;" />
            </div>
          </div>
        </div>

        <!-- Run Button -->
        <button
          @click="store.running ? stop() : runAnalysis()"
          :class="store.running ? 'btn-ghost' : 'btn-primary'"
          style="width:100%; padding:12px; font-size:14px; font-weight:600; display:flex; align-items:center; justify-content:center; gap:8px;"
          :disabled="!ticker || !selectedAnalysts.length"
        >
          <div v-if="store.running" class="spinner" style="border-top-color:#fff;"></div>
          <PlayIcon v-else :size="16" />
          {{ store.running ? 'Stop Analysis' : 'Run Analysis' }}
        </button>

        <!-- Error -->
        <div v-if="store.error" style="padding:10px 12px; background:var(--error-dim); border:1px solid var(--error); border-radius:8px; font-size:12px; color:var(--error);">
          {{ store.error }}
        </div>
      </div>

      <!-- Results Panel -->
      <div>

        <!-- Pipeline Progress -->
        <div class="card" style="margin-bottom:16px; padding:16px;">
          <p style="font-size:12px; font-weight:600; color:var(--txt-2); margin-bottom:14px;">Analysis Pipeline</p>
          <div style="display:flex; align-items:center; gap:0; overflow-x:auto; padding-bottom:4px;">
            <div
              v-for="(step, idx) in pipelineSteps"
              :key="step.key"
              style="display:flex; align-items:center; flex-shrink:0;"
            >
              <div style="display:flex; flex-direction:column; align-items:center; gap:4px;">
                <div
                  :style="{
                    width:'36px', height:'36px', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center',
                    background: isStepComplete(step.key) ? 'var(--success-dim)' : step.key === activeStep ? 'var(--primary-dim)' : 'var(--bg-elevated)',
                    border: `2px solid ${isStepComplete(step.key) ? 'var(--success)' : step.key === activeStep ? 'var(--primary)' : 'var(--border)'}`,
                    transition: 'all 0.3s',
                    boxShadow: step.key === activeStep && store.running ? '0 0 8px var(--primary)' : 'none',
                  }"
                >
                  <CheckIcon v-if="isStepComplete(step.key)" :size="14" color="var(--success)" />
                  <div v-else-if="step.key === activeStep && store.running" class="spinner" style="width:12px; height:12px; border-width:1.5px;"></div>
                  <component v-else :is="step.icon" :size="14" :color="step.key === activeStep ? 'var(--primary)' : 'var(--txt-3)'" />
                </div>
                <span style="font-size:9px; color:var(--txt-3); text-align:center; max-width:48px; line-height:1.2; white-space:nowrap;">{{ step.label }}</span>
              </div>
              <div v-if="idx < pipelineSteps.length - 1" :style="{ width:'20px', height:'2px', background: isStepComplete(step.key) ? 'var(--success)' : 'var(--border)', transition:'background 0.3s', flexShrink:0, margin:'0 2px', marginTop:'-14px' }"></div>
            </div>
          </div>
        </div>

        <!-- Status -->
        <div v-if="store.statusMsg || store.running" style="padding:10px 14px; background:var(--primary-dim); border:1px solid rgba(79,126,248,0.3); border-radius:8px; margin-bottom:14px; font-size:12px; color:var(--primary-txt); display:flex; align-items:center; gap:8px;">
          <div v-if="store.running" class="spinner" style="border-top-color:var(--primary);"></div>
          {{ store.statusMsg }}
        </div>

        <!-- Results -->
        <div v-if="store.results.length" style="display:flex; flex-direction:column; gap:10px;">

          <!-- Decision Banner -->
          <div v-if="finalDecision" :style="{ padding:'16px 20px', borderRadius:'12px', border:'1px solid', background: decisionColors[finalDecision]?.bg || 'var(--bg-elevated)', borderColor: decisionColors[finalDecision]?.border || 'var(--border)' }">
            <div style="display:flex; align-items:center; gap:10px;">
              <TrendingUpIcon :size="20" :color="decisionColors[finalDecision]?.text || 'var(--txt-2)'" />
              <span style="font-size:16px; font-weight:700;" :style="{ color: decisionColors[finalDecision]?.text || 'var(--txt-1)' }">Final Decision: {{ finalDecision }}</span>
            </div>
            <p style="font-size:12px; color:var(--txt-2); margin-top:6px; line-height:1.5;">
              {{ decisionSummary }}
            </p>
          </div>

          <!-- Agent Results -->
          <div
            v-for="result in store.results"
            :key="result.field"
            style="border-radius:10px; overflow:hidden;"
          >
            <button
              @click="toggleResult(result.field)"
              style="width:100%; background:var(--bg-card); border:1px solid var(--border); border-radius:10px; padding:12px 16px; cursor:pointer; display:flex; align-items:center; justify-content:space-between; text-align:left; transition:border-color 0.15s;"
              @mouseenter="hoverBorder($event, 'var(--border-s)')"
              @mouseleave="hoverBorder($event, 'var(--border)')"
            >
              <div style="display:flex; align-items:center; gap:10px;">
                <div style="width:8px; height:8px; border-radius:50%; background:var(--success); flex-shrink:0;"></div>
                <span style="font-size:13px; font-weight:600; color:var(--txt-1);">{{ result.label }}</span>
                <span style="font-size:11px; color:var(--txt-3);">{{ result.agent }}</span>
              </div>
              <ChevronDownIcon :size="14" color="var(--txt-3)" :style="{ transform: expandedResults.includes(result.field) ? 'rotate(180deg)' : 'none', transition:'transform 0.2s' }" />
            </button>
            <div v-if="expandedResults.includes(result.field)"
              style="background:var(--bg-elevated); border:1px solid var(--border); border-top:none; border-radius:0 0 10px 10px; padding:14px 16px;"
            >
              <pre style="font-size:12px; color:var(--txt-2); white-space:pre-wrap; line-height:1.6; font-family:inherit;">{{ result.content }}</pre>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!store.running" class="card" style="text-align:center; padding:60px 20px;">
          <BotIcon :size="40" color="var(--txt-3)" style="margin:0 auto 12px;" />
          <p style="font-size:14px; color:var(--txt-2); margin-bottom:6px;">Ready to analyze</p>
          <p style="font-size:12px; color:var(--txt-3);">Configure options and click Run Analysis</p>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Play as PlayIcon, ChevronDown as ChevronDownIcon, Check as CheckIcon,
  Bot as BotIcon, TrendingUp as TrendingUpIcon,
  BarChart2, MessageSquare, Newspaper, LineChart, Users, Briefcase, ShieldCheck, UserCheck,
} from 'lucide-vue-next'
import { useTradingAgentStore, PROVIDER_MODELS, PROVIDER_MODEL_OPTIONS, type LLMProvider } from '../stores/tradingAgent'
import { useTradingAgent } from '../composables/useTradingAgent'

const store = useTradingAgentStore()
const { start, stop } = useTradingAgent()

const ticker = ref(store.ticker || '')
const tradeDate = ref(store.tradeDate)
const deepModel = ref(store.deepModel)
const quickModel = ref(store.quickModel)
const debateRounds = ref(1)
const showAdvanced = ref(false)
const expandedResults = ref<string[]>([])

const selectedAnalysts = ref(['market', 'social', 'news', 'fundamentals'])

const analystOptions = [
  { key: 'market',       label: 'Market Analyst',       desc: 'Technical' },
  { key: 'social',       label: 'Social Media Analyst', desc: 'Social' },
  { key: 'news',         label: 'News Analyst',         desc: 'Events' },
  { key: 'fundamentals', label: 'Fundamentals Analyst', desc: 'Financials' },
]

const providerColors: Record<LLMProvider, { bg: string; border: string; text: string }> = {
  openai:     { bg:'rgba(16,163,127,0.12)', border:'rgba(16,163,127,0.4)', text:'#10a37f' },
  anthropic:  { bg:'rgba(204,89,52,0.12)',  border:'rgba(204,89,52,0.4)',  text:'#cc5934' },
  google:     { bg:'rgba(66,133,244,0.12)', border:'rgba(66,133,244,0.4)', text:'#4285f4' },
  openrouter: { bg:'rgba(124,77,255,0.12)', border:'rgba(124,77,255,0.4)', text:'#7c4dff' },
  ollama:     { bg:'rgba(100,100,100,0.12)',border:'rgba(100,100,100,0.4)',text:'#aaaaaa' },
  deepseek:   { bg:'rgba(255,149,0,0.12)',  border:'rgba(255,149,0,0.4)',  text:'#ff9500' },
}

const pipelineSteps = [
  { key: 'market',        label: 'Market',    icon: BarChart2 },
  { key: 'sentiment',     label: 'Sentiment', icon: MessageSquare },
  { key: 'news',          label: 'News',      icon: Newspaper },
  { key: 'fundamentals',  label: 'Fundament.',icon: LineChart },
  { key: 'debate',        label: 'Debate',    icon: Users },
  { key: 'trader',        label: 'Trader',    icon: Briefcase },
  { key: 'risk',          label: 'Risk',      icon: ShieldCheck },
  { key: 'portfolio',     label: 'Portfolio', icon: UserCheck },
]

// Collect all field and agent name tokens (lowercase) from completed results
const completedTokens = computed(() =>
  store.results.flatMap(r => [
    (r.field  || '').toLowerCase(),
    (r.agent  || '').toLowerCase(),
    (r.label  || '').toLowerCase(),
  ])
)

function isStepComplete(key: string): boolean {
  return completedTokens.value.some(t => t.includes(key))
}

const activeStep = computed(() => {
  if (!store.running) return ''
  const done = completedTokens.value
  for (const step of pipelineSteps) {
    if (!done.some((f: string) => f.includes(step.key))) return step.key
  }
  return ''
})

const decisionColors: Record<string, { bg: string; border: string; text: string }> = {
  BUY:  { bg:'var(--success-dim)', border:'var(--success)', text:'var(--success)' },
  SELL: { bg:'var(--error-dim)',   border:'var(--error)',   text:'var(--error)' },
  HOLD: { bg:'var(--warning-dim)', border:'var(--warning)', text:'var(--warning)' },
}

const finalDecision = computed(() => {
  const r = store.results.find(r => r.agent === 'portfolio_manager' || r.field === 'decision')
  if (!r) return null
  const m = r.content.match(/\b(BUY|SELL|HOLD)\b/i)
  return m ? m[0].toUpperCase() : null
})

const decisionSummary = computed(() => {
  const r = store.results.find(r => r.agent === 'portfolio_manager' || r.field === 'decision')
  return r?.content?.slice(0, 200) + (r && r.content.length > 200 ? '...' : '') || ''
})

function selectProvider(p: LLMProvider) {
  store.setProvider(p)
  deepModel.value = PROVIDER_MODELS[p].deep
  quickModel.value = PROVIDER_MODELS[p].quick
}

function toggleResult(field: string) {
  if (expandedResults.value.includes(field)) expandedResults.value = expandedResults.value.filter(f => f !== field)
  else expandedResults.value.push(field)
}

// Auto-expand new results
watch(() => store.results.length, () => {
  const last = store.results[store.results.length - 1]
  if (last && !expandedResults.value.includes(last.field)) expandedResults.value.push(last.field)
})

async function runAnalysis() {
  if (!ticker.value.trim()) return
  expandedResults.value = []
  await start({
    ticker: ticker.value.trim().toUpperCase(),
    date: tradeDate.value,
    analysts: selectedAnalysts.value,
    provider: store.provider,
    deepModel: deepModel.value,
    quickModel: quickModel.value,
    maxDebateRounds: debateRounds.value,
  })
}

function hoverBorder(e: Event, color: string) {
  const el = e.currentTarget as HTMLElement
  el.style.borderColor = color
}
</script>
