<template>
  <div class="view chat-view">
    <div class="chat-header">
      <h2>Chat Assistant</h2>
      <button class="clear-chat-btn" @click="store.clearChat">🗑️ Clear</button>
    </div>

    <div class="chat-messages" id="chatMessages" role="log" aria-live="polite">
      <div v-for="msg in store.conversationHistory" :key="msg.id" class="message" :class="{ 'user-message': msg.isUser, 'bot-message': !msg.isUser }">
        <div class="message-avatar">{{ msg.isUser ? '👤' : '🤖' }}</div>
        <div class="message-content"><p>{{ msg.content }}</p></div>
      </div>
    </div>

    <div class="chat-input-container">
      <input class="chat-input" v-model="store.chatInput" @keyup.enter="handleSend" placeholder="Type a message..." aria-label="Chat message input" />
      <button class="send-btn" @click="handleSend">➤</button>
    </div>

    <div class="typing-indicator" v-if="store.isLoading" style="display:flex;"><span></span><span></span><span></span></div>
  </div>
</template>

<script>
import { useMainStore } from '@/store'
export default {
  setup() {
    const store = useMainStore();
    function handleSend() { store.sendChatMessage() }
    return { store, handleSend }
  }
}
</script>
