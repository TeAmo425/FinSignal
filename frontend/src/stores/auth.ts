import { defineStore } from 'pinia'
import api from '../api/index'

interface User {
  id: number
  email: string
  name: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: localStorage.getItem('token') || '',
    loading: false,
    error: '',
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(email: string, password: string) {
      this.loading = true
      this.error = ''
      try {
        const res = await api.post('/api/auth/login', { email, password })
        this.token = res.data.token
        this.user = res.data.user
        localStorage.setItem('token', this.token)
      } catch (e: any) {
        this.error = e.response?.data?.detail || 'Login failed'
        throw e
      } finally {
        this.loading = false
      }
    },
    async register(email: string, password: string, name: string) {
      this.loading = true
      this.error = ''
      try {
        const res = await api.post('/api/auth/register', { email, password, name })
        this.token = res.data.token
        this.user = res.data.user
        localStorage.setItem('token', this.token)
      } catch (e: any) {
        this.error = e.response?.data?.detail || 'Registration failed'
        throw e
      } finally {
        this.loading = false
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    },
    async fetchUser() {
      if (!this.token) return
      try {
        const res = await api.get('/api/auth/me')
        this.user = res.data
      } catch {
        this.logout()
      }
    },
  },
})
