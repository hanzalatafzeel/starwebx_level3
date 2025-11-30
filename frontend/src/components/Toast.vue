<template>
  <div class="toast" v-show="store.showToast">
    <span id="toastMessage">{{ store.toastMessage }}</span>
  </div>
</template>

<script>
import { useMainStore } from '@/store'
export default { setup() { const store = useMainStore(); return { store } } }
</script>
