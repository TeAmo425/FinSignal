<template>
  <nav :style="sidebarStyle">
    <!-- Logo -->
    <div style="padding:20px 16px 16px; border-bottom:1px solid var(--border);">
      <RouterLink to="/" style="display:flex; align-items:center; gap:10px; text-decoration:none;">
        <div :style="hexStyle">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <polygon points="12,2 22,7 22,17 12,22 2,17 2,7" stroke="#4f7ef8" stroke-width="2" fill="rgba(79,126,248,0.15)"/>
            <polyline points="12,2 12,22" stroke="#4f7ef8" stroke-width="1.5" opacity="0.5"/>
            <polyline points="2,7 22,7" stroke="#4f7ef8" stroke-width="1.5" opacity="0.5"/>
            <polyline points="2,17 22,17" stroke="#4f7ef8" stroke-width="1.5" opacity="0.5"/>
          </svg>
        </div>
        <span style="font-size:18px; font-weight:700; background:linear-gradient(90deg,#4f7ef8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">FinAgent</span>
      </RouterLink>
    </div>

    <!-- Trading Agents Feature Card -->
    <div style="padding:12px 12px 8px;">
      <RouterLink to="/trading-agents" style="text-decoration:none; display:block;">
        <div :style="featureCardStyle">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <BotIcon :size="16" color="#fff" />
            <span style="font-size:13px; font-weight:600; color:#fff;">Trading Agents</span>
          </div>
          <p style="font-size:11px; color:rgba(255,255,255,0.75); line-height:1.4;">
            Multi-agent AI analysis with SSE streaming
          </p>
        </div>
      </RouterLink>
    </div>

    <!-- Navigation -->
    <div style="flex:1; overflow-y:auto; padding:4px 12px;">

      <!-- Markets Section -->
      <div style="margin-bottom:16px;">
        <p class="section-title" style="padding:0 4px;">Markets</p>
        <NavItem to="/" :icon="LayoutDashboardIcon" label="Dashboard" :active="route.path === '/'" />
        <NavItem to="/stocks" :icon="BarChart2Icon" label="Market Hub" :active="route.path === '/stocks'" />
        <NavItem to="/forecast" :icon="TrendingUpIcon" label="Forecast" :active="route.path === '/forecast'" />
        <NavItem to="/anomalies" :icon="AlertTriangleIcon" label="Anomalies" :active="route.path === '/anomalies'" />
      </div>

      <!-- Intelligence Section -->
      <div style="margin-bottom:16px;">
        <p class="section-title" style="padding:0 4px;">Intelligence</p>
        <NavItem to="/reports" :icon="FileTextIcon" label="Reports" :active="route.path === '/reports'" />
      </div>

      <!-- Data Section -->
      <div style="margin-bottom:16px;">
        <p class="section-title" style="padding:0 4px;">Data</p>
        <NavItem to="/datasets" :icon="DatabaseIcon" label="Datasets" :active="route.path === '/datasets'" />
      </div>

<!-- Tools Section -->
      <div style="margin-bottom:16px;">
        <p class="section-title" style="padding:0 4px;">Tools</p>
        <NavItem to="/screener" :icon="FilterIcon" label="Screener" :active="route.path === '/screener'" />
        <NavItem to="/paper-trading" :icon="WalletIcon" label="Paper Trading" :active="route.path === '/paper-trading'" />
      </div>

    </div>

    <!-- Footer -->
    <div style="padding:8px 12px 12px; border-top:1px solid var(--border);">
      <NavItem to="/settings" :icon="SettingsIcon" label="Settings" :active="route.path === '/settings'" />
      <div v-if="authStore.user" :style="userCardStyle">
        <div style="width:28px; height:28px; border-radius:50%; background:var(--primary-dim); display:flex; align-items:center; justify-content:center;">
          <UserIcon :size="14" color="var(--primary)" />
        </div>
        <div style="flex:1; min-width:0;">
          <p style="font-size:12px; font-weight:500; color:var(--txt-1); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{{ authStore.user.name }}</p>
          <p style="font-size:11px; color:var(--txt-3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{{ authStore.user.email }}</p>
        </div>
        <button @click="authStore.logout()" style="background:none; border:none; cursor:pointer; padding:4px; border-radius:4px; color:var(--txt-3); transition:color 0.15s;" title="Logout">
          <LogOutIcon :size="14" />
        </button>
      </div>
      <div v-else style="margin-top:8px;">
        <RouterLink to="/login" style="display:block; text-align:center; padding:6px; background:var(--primary-dim); border-radius:8px; color:var(--primary-txt); font-size:12px; text-decoration:none;">Sign In</RouterLink>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import {
  LayoutDashboard as LayoutDashboardIcon,
  BarChart2 as BarChart2Icon,
  TrendingUp as TrendingUpIcon,
  AlertTriangle as AlertTriangleIcon,
  FileText as FileTextIcon,
  Database as DatabaseIcon,
Filter as FilterIcon,
  Wallet as WalletIcon,
  Settings as SettingsIcon,
  User as UserIcon,
  LogOut as LogOutIcon,
  Bot as BotIcon,
} from 'lucide-vue-next'
import NavItem from './NavItem.vue'

const route = useRoute()
const authStore = useAuthStore()

const sidebarStyle = computed(() => ({
  position: 'fixed' as const,
  top: '0',
  left: '0',
  width: '240px',
  height: '100vh',
  background: 'var(--bg-surface)',
  borderRight: '1px solid var(--border)',
  display: 'flex',
  flexDirection: 'column' as const,
  zIndex: '100',
}))

const hexStyle = {
  width: '32px',
  height: '32px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: 'var(--primary-dim)',
  borderRadius: '8px',
}

const featureCardStyle = {
  padding: '10px 12px',
  borderRadius: '10px',
  background: 'linear-gradient(135deg, rgba(79,126,248,0.25) 0%, rgba(129,140,248,0.15) 100%)',
  border: '1px solid rgba(79,126,248,0.3)',
  cursor: 'pointer',
  transition: 'border-color 0.15s',
}

const userCardStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  padding: '8px',
  borderRadius: '8px',
  background: 'var(--bg-elevated)',
  marginTop: '8px',
}
</script>
