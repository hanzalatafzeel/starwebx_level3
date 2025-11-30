<template>
  <div class="modal" id="settingsModal" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Settings</h3>
        <button class="modal-close" @click="close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label>API Endpoint</label>
          <input v-model="endpoint" />
        </div>
        <div class="form-group">
          <label>Theme</label>
          <div class="theme-toggle">
            <button class="theme-btn" :class="{ active: theme==='auto' }" @click="setTheme('auto')">Auto</button>
            <button class="theme-btn" :class="{ active: theme==='light' }" @click="setTheme('light')">Light</button>
            <button class="theme-btn" :class="{ active: theme==='dark' }" @click="setTheme('dark')">Dark</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useMainStore } from '@/store'
export default {
  setup() {
    const store = useMainStore();
    const endpoint = ref(store.apiEndpoint);
    const theme = ref(store.appTheme);
    function close() { store.showSettings = false }
    function setTheme(t) { store.appTheme = t; theme.value = t; if (t==='dark') document.documentElement.setAttribute('data-color-scheme','dark'); else if (t==='light') document.documentElement.setAttribute('data-color-scheme','light'); else document.documentElement.removeAttribute('data-color-scheme'); store.showToast('Theme set to ' + t) }
    return { endpoint, theme, close, setTheme }
  }
}
</script>
