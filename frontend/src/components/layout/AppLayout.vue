<template>
  <div style="display:flex; height:100vh; background:var(--bg-base); overflow:hidden;">
    <Sidebar />
    <div style="flex:1; margin-left:240px; display:flex; flex-direction:column; overflow:hidden;">
      <main style="flex:1; overflow-y:auto; padding-bottom:64px;">
        <RouterView />
      </main>
      <AIBar />
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import AIBar from './AIBar.vue'
</script>
