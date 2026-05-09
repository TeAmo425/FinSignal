import { defineStore } from 'pinia'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

export type LLMProvider = 'openai' | 'anthropic' | 'google' | 'openrouter' | 'ollama' | 'deepseek'

export const PROVIDER_MODELS: Record<LLMProvider, { deep: string; quick: string; label: string }> = {
  openai:     { deep: 'gpt-4o',                       quick: 'gpt-4o-mini',               label: 'OpenAI' },
  anthropic:  { deep: 'claude-sonnet-4-6',            quick: 'claude-haiku-4-5-20251001', label: 'Anthropic' },
  google:     { deep: 'gemini-2.5-pro-preview-05-06', quick: 'gemini-2.0-flash',          label: 'Google' },
  openrouter: { deep: 'openai/gpt-4o',                quick: 'openai/gpt-4o-mini',        label: 'OpenRouter' },
  ollama:     { deep: 'llama3.1:70b',                 quick: 'llama3.1:8b',               label: 'Ollama (local)' },
  deepseek:   { deep: 'deepseek-reasoner',            quick: 'deepseek-chat',             label: 'DeepSeek' },
}

export const PROVIDER_MODEL_OPTIONS: Record<LLMProvider, { deep: string[]; quick: string[] }> = {
  openai: {
    deep:  ['gpt-4o', 'gpt-4.1', 'o3', 'o4-mini', 'gpt-4-turbo'],
    quick: ['gpt-4o-mini', 'gpt-4.1-mini', 'gpt-4o', 'gpt-3.5-turbo'],
  },
  anthropic: {
    deep:  ['claude-opus-4-6', 'claude-sonnet-4-6', 'claude-sonnet-4-5-20251001'],
    quick: ['claude-haiku-4-5-20251001', 'claude-haiku-3-5-20241022', 'claude-sonnet-4-6'],
  },
  google: {
    deep:  ['gemini-2.5-pro-preview-05-06', 'gemini-2.5-pro', 'gemini-2.0-pro'],
    quick: ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash'],
  },
  openrouter: {
    deep:  ['openai/gpt-4o', 'anthropic/claude-opus-4', 'google/gemini-2.5-pro', 'deepseek/deepseek-r1', 'meta-llama/llama-3.3-70b-instruct'],
    quick: ['openai/gpt-4o-mini', 'anthropic/claude-haiku-4-5', 'google/gemini-2.0-flash', 'meta-llama/llama-3.1-8b-instruct'],
  },
  ollama: {
    deep:  ['llama3.1:70b', 'llama3.3:70b', 'deepseek-r1:70b', 'qwen2.5:72b', 'mistral:7b'],
    quick: ['llama3.1:8b', 'llama3.2:3b', 'qwen2.5:7b', 'phi3:mini'],
  },
  deepseek: {
    deep:  ['deepseek-reasoner', 'deepseek-chat'],
    quick: ['deepseek-chat', 'deepseek-reasoner'],
  },
}

export interface AgentResult {
  agent: string
  label: string
  field: string
  content: string
}

export const useTradingAgentStore = defineStore('tradingAgent', {
  state: () => ({
    ticker: '',
    tradeDate: new Date().toISOString().split('T')[0],
    results: [] as AgentResult[],
    running: false,
    statusMsg: '',
    error: '',
    provider: 'openai' as LLMProvider,
    deepModel: PROVIDER_MODELS.openai.deep,
    quickModel: PROVIDER_MODELS.openai.quick,
  }),
  actions: {
    setTicker(t: string) { this.ticker = t },
    setTradeDate(d: string) { this.tradeDate = d },
    setProvider(p: LLMProvider) {
      this.provider = p
      this.deepModel = PROVIDER_MODELS[p].deep
      this.quickModel = PROVIDER_MODELS[p].quick
    },
    clearError() { this.error = '' },
    stop() {
      this.running = false
      this.statusMsg = 'Stopped'
    },
    addResult(result: AgentResult) {
      const idx = this.results.findIndex(r => r.field === result.field)
      if (idx >= 0) this.results[idx] = result
      else this.results.push(result)
    },
    reset() {
      this.results = []
      this.error = ''
      this.statusMsg = ''
      this.running = false
    },
  },
})

export { API_URL }
