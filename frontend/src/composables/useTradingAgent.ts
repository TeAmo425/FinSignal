import { ref } from 'vue'
import { useTradingAgentStore } from '../stores/tradingAgent'
import type { LLMProvider } from '../stores/tradingAgent'

const API_URL = import.meta.env.VITE_API_URL ?? ''

export function useTradingAgent() {
  const store = useTradingAgentStore()
  const abortController = ref<AbortController | null>(null)

  async function start(opts: {
    ticker: string
    date: string
    analysts: string[]
    provider: LLMProvider
    deepModel: string
    quickModel: string
    maxDebateRounds?: number
  }) {
    const openaiKey    = sessionStorage.getItem('openai_api_key')    || ''
    const anthropicKey = sessionStorage.getItem('anthropic_api_key') || ''
    const googleKey    = sessionStorage.getItem('google_api_key')    || ''
    const deepseekKey  = sessionStorage.getItem('deepseek_api_key')  || ''

    if (opts.provider !== 'ollama') {
      const keyMap: Record<string, string> = {
        openai: openaiKey, anthropic: anthropicKey,
        google: googleKey, openrouter: openaiKey, deepseek: deepseekKey,
      }
      if (!keyMap[opts.provider]) {
        store.error = `${opts.provider} API key not configured — go to Settings`
        return
      }
    }

    abortController.value?.abort()
    abortController.value = new AbortController()
    store.running = true
    store.error = ''
    store.results = []
    store.statusMsg = 'Connecting...'
    store.ticker = opts.ticker
    store.tradeDate = opts.date

    try {
      const token = localStorage.getItem('token') || ''
      const res = await fetch(`${API_URL}/api/trading-agents/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          ticker: opts.ticker.toUpperCase(),
          trade_date: opts.date,
          analysts: opts.analysts,
          llm_provider: opts.provider,
          deep_model: opts.deepModel,
          quick_model: opts.quickModel,
          openai_api_key: openaiKey || undefined,
          anthropic_api_key: anthropicKey || undefined,
          google_api_key: googleKey || undefined,
          deepseek_api_key: deepseekKey || undefined,
          max_debate_rounds: opts.maxDebateRounds || 1,
        }),
        signal: abortController.value.signal,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Request failed')
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          let event: any
          try {
            event = JSON.parse(line.slice(6))
          } catch { continue /* skip malformed SSE lines */ }

          if (event.type === 'init') {
            store.statusMsg = event.message
          } else if (event.type === 'agent_update') {
            store.addResult({
              agent: event.agent,
              label: event.label,
              field: event.field,
              content: event.content,
            })
            store.statusMsg = `${event.agent} analyzing...`
          } else if (event.type === 'done') {
            store.running = false
            store.statusMsg = 'Analysis complete'
            // Cache result
            try {
              const cache = JSON.parse(sessionStorage.getItem('agentCache') || '{}')
              cache[opts.ticker.toUpperCase()] = {
                results: store.results,
                date: opts.date,
                timestamp: Date.now(),
                provider: opts.provider || store.provider,
              }
              sessionStorage.setItem('agentCache', JSON.stringify(cache))
            } catch { /* ignore cache errors */ }
          } else if (event.type === 'error') {
            throw new Error(event.message)
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        store.running = false
        store.error = e.message || 'Analysis failed'
      }
    }
  }

  function stop() {
    abortController.value?.abort()
    store.stop()
  }

  return { start, stop }
}
