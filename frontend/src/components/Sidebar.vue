<template>
  <aside class="sidebar" :class="{ open: store.sidebarOpen }" id="sidebar">
    <div class="sidebar-header">
      <div class="restaurant-brand">
        <div class="brand-icon">🍽️</div>
        <h1 class="brand-name">Taste Haven</h1>
      </div>
      <div class="restaurant-info">
        <p>📞 (555) 123-4567</p>
        <p>📧 info@tastehaven.com</p>
        <p>📍 123 Food Street, Downtown</p>
      </div>
    </div>

    <nav class="sidebar-nav">
      <button v-for="view in store.views" :key="view.id" class="nav-item" :class="{ active: $route.name === view.id }" @click="() => navigateTo(view.id)">
        <span class="nav-icon">{{ view.icon }}</span>
        <span class="nav-label">{{ view.label }}</span>
      </button>
    </nav>

    <div class="sidebar-footer">
      <button class="settings-btn" @click="openSettings" aria-label="Open settings">
        <span>⚙️</span> Settings
      </button>
      <div class="session-info">
        <small>Session ID:</small>
        <code>{{ store.sessionId ? store.sessionId.substring(0,20) + '...' : '' }}</code>
      </div>
    </div>
  </aside>
</template>

<script>
import { useMainStore } from '@/store'
import { useRouter } from 'vue-router'
export default {
  setup() {
    const store = useMainStore();
    const router = useRouter();
    function navigateTo(id) { router.push({ name: id }); store.sidebarOpen = false }
    function openSettings() { store.showSettings = true }
    return { store, navigateTo, openSettings }
  }
}
</script>
