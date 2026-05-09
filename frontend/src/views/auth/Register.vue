<template>
  <div style="min-height:100vh; background:var(--bg-base); display:flex; align-items:center; justify-content:center; padding:24px;">
    <div style="width:100%; max-width:400px;">

      <!-- Logo -->
      <div style="text-align:center; margin-bottom:32px;">
        <div style="width:48px; height:48px; background:var(--primary-dim); border-radius:12px; display:flex; align-items:center; justify-content:center; margin:0 auto 12px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <polygon points="12,2 22,7 22,17 12,22 2,17 2,7" stroke="#4f7ef8" stroke-width="2" fill="rgba(79,126,248,0.2)"/>
          </svg>
        </div>
        <h1 style="font-size:24px; font-weight:700; background:linear-gradient(90deg,#4f7ef8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">FinAgent</h1>
        <p style="font-size:13px; color:var(--txt-3); margin-top:4px;">Financial Analysis Platform</p>
      </div>

      <!-- Card -->
      <div class="card" style="padding:28px;">
        <h2 style="font-size:18px; font-weight:600; color:var(--txt-1); margin-bottom:6px;">Create Account</h2>
        <p style="font-size:13px; color:var(--txt-3); margin-bottom:24px;">Get started with FinAgent today.</p>

        <form @submit.prevent="handleRegister">
          <div style="display:flex; flex-direction:column; gap:14px;">
            <div>
              <label style="font-size:12px; color:var(--txt-2); display:block; margin-bottom:6px;">Full Name</label>
              <input v-model="name" type="text" placeholder="John Doe" class="input-base" style="width:100%;" required />
            </div>
            <div>
              <label style="font-size:12px; color:var(--txt-2); display:block; margin-bottom:6px;">Email</label>
              <input v-model="email" type="email" placeholder="you@example.com" class="input-base" style="width:100%;" required />
            </div>
            <div>
              <label style="font-size:12px; color:var(--txt-2); display:block; margin-bottom:6px;">Password</label>
              <div style="position:relative;">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Min. 8 characters"
                  class="input-base"
                  style="width:100%; padding-right:36px;"
                  minlength="8"
                  required
                />
                <button type="button" @click="showPassword = !showPassword" style="position:absolute; right:10px; top:50%; transform:translateY(-50%); background:none; border:none; cursor:pointer; color:var(--txt-3);">
                  <EyeOffIcon v-if="showPassword" :size="14" />
                  <EyeIcon v-else :size="14" />
                </button>
              </div>
            </div>
            <div>
              <label style="font-size:12px; color:var(--txt-2); display:block; margin-bottom:6px;">Confirm Password</label>
              <input
                v-model="confirmPassword"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Repeat password"
                class="input-base"
                style="width:100%;"
                required
              />
            </div>
          </div>

          <div v-if="error" style="margin-top:14px; padding:10px 12px; background:var(--error-dim); border:1px solid var(--error); border-radius:8px; font-size:12px; color:var(--error);">
            {{ error }}
          </div>

          <button
            type="submit"
            class="btn-primary"
            :disabled="loading"
            style="width:100%; margin-top:20px; padding:11px; font-size:14px; font-weight:600; display:flex; align-items:center; justify-content:center; gap:8px;"
          >
            <div v-if="loading" class="spinner" style="border-top-color:#fff;"></div>
            {{ loading ? 'Creating account...' : 'Create Account' }}
          </button>
        </form>

        <div style="margin-top:20px; text-align:center; padding-top:20px; border-top:1px solid var(--border);">
          <p style="font-size:13px; color:var(--txt-3);">
            Already have an account?
            <RouterLink to="/login" style="color:var(--primary-txt); text-decoration:none; font-weight:500;">Sign In</RouterLink>
          </p>
        </div>

        <div style="margin-top:12px; text-align:center;">
          <RouterLink to="/" style="font-size:12px; color:var(--txt-3); text-decoration:none;">Continue without account →</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { Eye as EyeIcon, EyeOff as EyeOffIcon } from 'lucide-vue-next'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  error.value = ''
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters'
    return
  }
  loading.value = true
  try {
    await authStore.register(email.value, password.value, name.value)
    router.push('/')
  } catch (e: any) {
    error.value = authStore.error || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
