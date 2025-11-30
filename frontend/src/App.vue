<template>
  <div id="app">
    <div class="app-container">
      <Sidebar />

      <main class="main-content">
        <header class="mobile-header">
          <button class="menu-toggle" @click="store.sidebarOpen = !store.sidebarOpen">☰</button>
          <h2 class="mobile-title">Taste Haven</h2>
        </header>

        <router-view />
      </main>
    </div>

    <SettingsModal v-if="store.showSettings" />
    <Toast />
  </div>
</template>

<script>
import { useMainStore } from './store'
import Sidebar from './components/Sidebar.vue'
import SettingsModal from './components/SettingsModal.vue'
import Toast from './components/Toast.vue'

export default {
  name: 'App',
  components: { Sidebar, SettingsModal, Toast },
  setup() {
    const store = useMainStore();
    // initialize once
    if (!store.sessionId) store.initializeSession();
    store.fetchMenu();
    store.addMessage('Welcome to Taste Haven! I\'m your AI assistant. How can I help you today?', false);
    return { store };
  }
}
</script>
