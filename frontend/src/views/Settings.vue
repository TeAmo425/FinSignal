<template>
  <div style="padding:24px; max-width:800px; margin:0 auto;">

    <!-- Header -->
    <div style="margin-bottom:24px;">
      <h1 style="font-size:22px; font-weight:700; color:var(--txt-1); margin-bottom:4px;">Settings</h1>
      <p style="font-size:13px; color:var(--txt-3);">Configure API keys, preferences, and notifications</p>
    </div>

    <!-- Tabs -->
    <div style="display:flex; gap:2px; margin-bottom:24px; background:var(--bg-elevated); border-radius:10px; padding:4px; width:fit-content;">
      <button
        v-for="tab in tabs"
        :key="tab"
        @click="activeTab = tab"
        :style="{
          padding:'7px 16px', borderRadius:'8px', border:'none', cursor:'pointer', fontSize:'13px', fontWeight:'500',
          background: activeTab === tab ? 'var(--bg-card)' : 'transparent',
          color: activeTab === tab ? 'var(--txt-1)' : 'var(--txt-3)',
          transition:'all 0.15s',
          boxShadow: activeTab === tab ? '0 1px 3px rgba(0,0,0,0.3)' : 'none',
        }"
      >{{ tab }}</button>
    </div>

    <!-- API Keys Tab -->
    <div v-if="activeTab === 'API Keys'">
      <div class="card" style="margin-bottom:16px; padding:20px;">
        <p style="font-size:13px; color:var(--txt-2); margin-bottom:16px; line-height:1.5;">
          API keys are saved to your account and synced across browsers. They are only used to forward requests to the respective AI provider.
        </p>

        <div v-for="key in apiKeys" :key="key.id" style="margin-bottom:20px; padding-bottom:20px; border-bottom:1px solid var(--border);">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <div :style="{ width:'8px', height:'8px', borderRadius:'50%', background: getKeyValue(key.id) ? 'var(--success)' : 'var(--txt-3)' }"></div>
              <span style="font-size:13px; font-weight:600; color:var(--txt-1);">{{ key.label }}</span>
              <span style="font-size:11px; color:var(--txt-3);">{{ key.hint }}</span>
            </div>
            <span v-if="getKeyValue(key.id)" style="font-size:11px; color:var(--success);">Configured</span>
          </div>
          <div style="display:flex; gap:8px;">
            <div style="position:relative; flex:1;">
              <input
                v-model="keyValues[key.id]"
                :type="showKey[key.id] ? 'text' : 'password'"
                :placeholder="key.placeholder"
                class="input-base"
                style="width:100%; padding-right:36px;"
              />
              <button
                @click="showKey[key.id] = !showKey[key.id]"
                style="position:absolute; right:8px; top:50%; transform:translateY(-50%); background:none; border:none; cursor:pointer; color:var(--txt-3);"
              >
                <EyeOffIcon v-if="showKey[key.id]" :size="14" />
                <EyeIcon v-else :size="14" />
              </button>
            </div>
            <button @click="saveKey(key.id)" class="btn-primary" style="padding:8px 14px;">Save</button>
            <button v-if="getKeyValue(key.id)" @click="deleteKey(key.id)" class="btn-ghost" style="padding:8px 10px; border-color:var(--error); color:var(--error);">
              <TrashIcon :size="14" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Preferences Tab -->
    <div v-else-if="activeTab === 'Preferences'">
      <div class="card" style="padding:20px;">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:16px;">Display Preferences</h3>
        <div style="display:flex; flex-direction:column; gap:14px;">

          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
              <p style="font-size:13px; color:var(--txt-1);">Default LLM Provider</p>
              <p style="font-size:11px; color:var(--txt-3);">Used for quick AI analysis</p>
            </div>
            <select v-model="prefs.defaultProvider" class="input-base" style="padding:6px 10px;">
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google</option>
              <option value="deepseek">DeepSeek</option>
              <option value="ollama">Ollama (local)</option>
            </select>
          </div>

          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
              <p style="font-size:13px; color:var(--txt-1);">Default Chart Period</p>
              <p style="font-size:11px; color:var(--txt-3);">Default timeframe for stock charts</p>
            </div>
            <select v-model="prefs.defaultPeriod" class="input-base" style="padding:6px 10px;">
              <option value="1mo">1 Month</option>
              <option value="3mo">3 Months</option>
              <option value="6mo">6 Months</option>
              <option value="1y">1 Year</option>
            </select>
          </div>

          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
              <p style="font-size:13px; color:var(--txt-1);">Auto-expand Results</p>
              <p style="font-size:11px; color:var(--txt-3);">Automatically expand AI analysis results</p>
            </div>
            <label style="position:relative; display:inline-block; width:40px; height:22px; cursor:pointer;">
              <input v-model="prefs.autoExpand" type="checkbox" style="opacity:0; width:0; height:0;" />
              <span :style="{
                position:'absolute', top:0, left:0, right:0, bottom:0, borderRadius:'11px',
                background: prefs.autoExpand ? 'var(--primary)' : 'var(--bg-elevated)',
                border:'1px solid ' + (prefs.autoExpand ? 'var(--primary)' : 'var(--border)'),
                transition:'background 0.2s',
              }">
                <span :style="{
                  position:'absolute', top:'2px', left: prefs.autoExpand ? '20px' : '2px',
                  width:'16px', height:'16px', borderRadius:'50%',
                  background: '#fff', transition:'left 0.2s',
                }"></span>
              </span>
            </label>
          </div>

        </div>
        <button @click="savePrefs" class="btn-primary" style="margin-top:20px;">Save Preferences</button>
      </div>
    </div>

    <!-- Notifications Tab -->
    <div v-else-if="activeTab === 'Notifications'">
      <div class="card" style="padding:20px;">
        <h3 style="font-size:14px; font-weight:600; color:var(--txt-1); margin-bottom:16px;">Notification Settings</h3>
        <div style="display:flex; flex-direction:column; gap:14px;">
          <div v-for="notif in notifications" :key="notif.key" style="display:flex; align-items:center; justify-content:space-between; padding:10px 0; border-bottom:1px solid var(--border);">
            <div>
              <p style="font-size:13px; color:var(--txt-1);">{{ notif.label }}</p>
              <p style="font-size:11px; color:var(--txt-3);">{{ notif.desc }}</p>
            </div>
            <label style="position:relative; display:inline-block; width:40px; height:22px; cursor:pointer;">
              <input v-model="notifValues[notif.key]" type="checkbox" style="opacity:0; width:0; height:0;" />
              <span :style="{
                position:'absolute', top:0, left:0, right:0, bottom:0, borderRadius:'11px',
                background: notifValues[notif.key] ? 'var(--primary)' : 'var(--bg-elevated)',
                border:'1px solid ' + (notifValues[notif.key] ? 'var(--primary)' : 'var(--border)'),
                transition:'background 0.2s',
              }">
                <span :style="{
                  position:'absolute', top:'2px', left: notifValues[notif.key] ? '20px' : '2px',
                  width:'16px', height:'16px', borderRadius:'50%', background:'#fff', transition:'left 0.2s',
                }"></span>
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- Save notification -->
    <transition name="fade">
      <div v-if="savedMsg" style="position:fixed; bottom:80px; right:24px; padding:10px 16px; background:var(--success-dim); border:1px solid var(--success); border-radius:8px; color:var(--success); font-size:13px; font-weight:500;">
        {{ savedMsg }}
      </div>
    </transition>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Eye as EyeIcon, EyeOff as EyeOffIcon, Trash as TrashIcon } from 'lucide-vue-next'
import api from '../api/index'

const tabs = ['API Keys', 'Preferences', 'Notifications']
const activeTab = ref('API Keys')
const savedMsg = ref('')
const keysLoading = ref(false)

const apiKeys = [
  { id: 'openai_api_key',    label: 'OpenAI',      hint: 'GPT-4o, GPT-4o-mini', placeholder: 'sk-...' },
  { id: 'anthropic_api_key', label: 'Anthropic',   hint: 'Claude Sonnet, Haiku', placeholder: 'sk-ant-...' },
  { id: 'google_api_key',    label: 'Google AI',   hint: 'Gemini Pro, Flash', placeholder: 'AIza...' },
  { id: 'deepseek_api_key',  label: 'DeepSeek',    hint: 'DeepSeek Reasoner, Chat', placeholder: 'sk-...' },
]

const keyValues = reactive<Record<string, string>>({})
const showKey = reactive<Record<string, boolean>>({})

function getKeyValue(id: string): string {
  return sessionStorage.getItem(id) || ''
}

async function saveKey(id: string) {
  const val = keyValues[id]?.trim()
  if (!val) return
  sessionStorage.setItem(id, val)
  try {
    await api.put('/api/auth/settings/keys', { keys: { [id]: val } })
    showSaved('API key saved!')
  } catch {
    showSaved('Saved locally (sync failed)')
  }
}

async function deleteKey(id: string) {
  sessionStorage.removeItem(id)
  keyValues[id] = ''
  try {
    await api.put('/api/auth/settings/keys', { keys: { [id]: '' } })
  } catch { /* ignore */ }
  showSaved('API key removed')
}

async function loadKeysFromServer() {
  keysLoading.value = true
  try {
    const res = await api.get('/api/auth/settings/keys/values')
    const data: Record<string, string> = res.data
    for (const [k, v] of Object.entries(data)) {
      if (v) {
        sessionStorage.setItem(k, v)
        keyValues[k] = v
      }
    }
  } catch { /* ignore, use local */ } finally {
    keysLoading.value = false
  }
}

const prefs = reactive({
  defaultProvider: localStorage.getItem('pref_provider') || 'openai',
  defaultPeriod: localStorage.getItem('pref_period') || '1y',
  autoExpand: localStorage.getItem('pref_auto_expand') === 'true',
})

function savePrefs() {
  localStorage.setItem('pref_provider', prefs.defaultProvider)
  localStorage.setItem('pref_period', prefs.defaultPeriod)
  localStorage.setItem('pref_auto_expand', String(prefs.autoExpand))
  showSaved('Preferences saved!')
}

const notifications = [
  { key: 'ai_complete',  label: 'Analysis Complete', desc: 'Notify when AI analysis finishes' },
  { key: 'price_alert',  label: 'Price Alerts', desc: 'Notify on significant price movements' },
  { key: 'news_alert',   label: 'News Alerts', desc: 'Notify on breaking financial news' },
  { key: 'anomaly_alert',label: 'Anomaly Detected', desc: 'Notify when anomalies are detected' },
]

const notifValues = reactive<Record<string, boolean>>({
  ai_complete: true, price_alert: false, news_alert: false, anomaly_alert: true,
})

function showSaved(msg: string) {
  savedMsg.value = msg
  setTimeout(() => { savedMsg.value = '' }, 2500)
}

onMounted(async () => {
  apiKeys.forEach(k => { keyValues[k.id] = getKeyValue(k.id) })
  await loadKeysFromServer()
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
