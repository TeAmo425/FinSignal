import { createRouter, createWebHashHistory } from 'vue-router'
import AppLayout from '../components/layout/AppLayout.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '',          name: 'Dashboard',     component: () => import('../views/Dashboard.vue') },
        { path: 'stocks',    name: 'MarketHub',     component: () => import('../views/MarketHub.vue') },
        { path: 'stock/:ticker', name: 'StockDetail', component: () => import('../views/StockDetail.vue') },
        { path: 'trading-agents', name: 'TradingAgents', component: () => import('../views/TradingAgents.vue') },
        { path: 'forecast',  name: 'Forecast',      component: () => import('../views/Forecast.vue') },
        { path: 'anomalies', name: 'Anomalies',     component: () => import('../views/Anomalies.vue') },
        { path: 'reports',   name: 'Reports',       component: () => import('../views/Reports.vue') },
        { path: 'datasets',  name: 'Datasets',      component: () => import('../views/Datasets.vue') },
        { path: 'settings',  name: 'Settings',      component: () => import('../views/Settings.vue') },
{ path: 'screener',  name: 'Screener',      component: () => import('../views/Screener.vue') },
        { path: 'paper-trading', name: 'PaperTrading', component: () => import('../views/PaperTrading.vue') },
      ],
    },
    { path: '/login',    name: 'Login',    component: () => import('../views/auth/Login.vue') },
    { path: '/register', name: 'Register', component: () => import('../views/auth/Register.vue') },
  ],
})

export default router
