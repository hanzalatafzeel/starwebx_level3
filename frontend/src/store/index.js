import { defineStore } from 'pinia'
import api from '../services/api'

export const useMainStore = defineStore('main', {
  state: () => ({
    sessionId: '',
    currentView: 'chat',
    sidebarOpen: false,
    isLoading: false,
    showSettings: false,
    showToast: false,
    toastMessage: '',
    apiEndpoint: 'http://127.0.0.1:5000/api',
    appTheme: 'auto',

    chatInput: '',
    conversationHistory: [],
    
    // Order collection state
    orderCollectionMode: false,
    orderCollectionStep: 0,
    orderCollectionData: {},
    
    // Reservation collection state
    reservationCollectionMode: false,
    reservationCollectionStep: 0,
    reservationCollectionData: {},

    menuItems: [],
    menuSearch: '',
    activeMenuCategory: 'all',
    menuCategories: ['all', 'appetizers', 'main_courses', 'desserts', 'beverages'],

    // Navigation and quick actions
    views: [
      { id: 'chat', label: 'Chat', icon: '💬' },
      { id: 'menu', label: 'Menu', icon: '🍽️' },
      { id: 'orders', label: 'Orders', icon: '🛒' },
      { id: 'reservations', label: 'Reservations', icon: '📅' }
    ],
    quickActions: [
      { id: 1, label: '🍽️ Show Menu', message: "I'd like to see your menu" },
      { id: 2, label: '🛒 Place Order', message: 'I want to place an order' },
      { id: 3, label: '📅 Book Table', message: "I'd like to make a reservation" },
      { id: 4, label: '⭐ Recommendations', message: 'What do you recommend for me?' }
    ],

    cart: [],
    orderForm: { name: '', email: '', phone: '', special_requests: '' },

    reservationForm: { name: '', email: '', phone: '', party_size: 2, date: '', time: '', special_requests: '' },
    reservationConfirmed: false,
    reservationConfirmationId: '',
  }),

  getters: {
    cartTotal: (state) => state.cart.reduce((s, i) => s + (i.price * i.quantity || 0), 0),
    filteredMenuItems: (state) => {
      let items = state.menuItems || [];
      if (state.activeMenuCategory && state.activeMenuCategory !== 'all') {
        items = items.filter(i => i.category === state.activeMenuCategory);
      }
      if (state.menuSearch) {
        const q = state.menuSearch.toLowerCase();
        items = items.filter(it => (it.name || '').toLowerCase().includes(q) || (it.description || '').toLowerCase().includes(q));
      }
      return items;
    }
  },

  actions: {
    initializeSession() {
      this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    showToast(message) {
      this.toastMessage = message;
      this.showToast = true;
      setTimeout(() => { this.showToast = false }, 3000);
    },

    async fetchMenu() {
      this.isLoading = true;
      try {
        const items = await api.fetchMenu();
        this.menuItems = items.length ? items : this.menuItems;
      } finally { this.isLoading = false }
    },

    addMessage(content, isUser = false) {
      this.conversationHistory.push({ id: Date.now(), content, isUser });
    },

    async sendChatMessage() {
      const message = (this.chatInput || '').trim();
      if (!message) return;
      this.addMessage(message, true);
      this.chatInput = '';
      this.isLoading = true;
      try {
        // Check for order collection mode
        if (this.orderCollectionMode) {
          const res = await fetch(`${this.apiEndpoint}/chat/order-intent`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message,
              session_id: this.sessionId,
              step: this.orderCollectionStep,
              collected_data: this.orderCollectionData
            })
          });
          if (res.ok) {
            const data = await res.json();
            this.addMessage(data.response, false);
            this.orderCollectionStep = data.step;
            this.orderCollectionData = data.collected_data;
            if (data.step === 0) {
              this.orderCollectionMode = false;
              this.orderCollectionData = {};
            }
          }
          return;
        }
        
        // Check for reservation collection mode
        if (this.reservationCollectionMode) {
          const res = await fetch(`${this.apiEndpoint}/chat/reservation-intent`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message,
              session_id: this.sessionId,
              step: this.reservationCollectionStep,
              collected_data: this.reservationCollectionData
            })
          });
          if (res.ok) {
            const data = await res.json();
            this.addMessage(data.response, false);
            this.reservationCollectionStep = data.step;
            this.reservationCollectionData = data.collected_data;
            if (data.step === 0) {
              this.reservationCollectionMode = false;
              this.reservationCollectionData = {};
            }
          }
          return;
        }
        
        // Check for order intent
        const orderKeywords = ['order', 'place an order', 'i want', 'can i have', 'give me', 'get me', 'buy', 'purchase'];
        if (orderKeywords.some(kw => message.toLowerCase().includes(kw))) {
          this.orderCollectionMode = true;
          this.orderCollectionStep = 0;
          this.orderCollectionData = {};
          this.addMessage("I'll help you place an order! Which items would you like?", false);
          return;
        }
        
        // Check for reservation intent
        const reservationKeywords = ['reservation', 'reserve', 'book', 'table', 'booking', 'dinner reservation', 'lunch reservation'];
        if (reservationKeywords.some(kw => message.toLowerCase().includes(kw))) {
          this.reservationCollectionMode = true;
          this.reservationCollectionStep = 0;
          this.reservationCollectionData = {};
          this.addMessage("I'll help you make a reservation! What's your name?", false);
          return;
        }
        
        // Normal chat
        const resp = await api.sendChatMessage(message, this.sessionId);
        this.addMessage(resp || 'Sorry, I could not process that.', false);
      } finally { this.isLoading = false }
    },

    addToCart(item) {
      const existing = this.cart.find(i => i.id === item.id);
      if (existing) existing.quantity++;
      else this.cart.push({ ...item, quantity: 1 });
      this.showToast(`${item.name} added to cart`);
    },

    updateCartQuantity(id, change) {
      const it = this.cart.find(i => i.id === id);
      if (!it) return;
      it.quantity += change;
      if (it.quantity <= 0) this.removeFromCart(id);
    },

    removeFromCart(id) {
      this.cart = this.cart.filter(i => i.id !== id);
      this.showToast('Item removed from cart');
    },

    clearCart() {
      this.cart = [];
      this.orderForm = { name: '', email: '', phone: '', special_requests: '' };
      this.showToast('Cart cleared');
    },

    async placeOrder() {
      const { name, email, phone, special_requests } = this.orderForm;
      if (!name || !email || !phone) { this.showToast('Please fill in all required fields'); return }
      const orderData = {
        customer_name: name,
        customer_email: email,
        customer_phone: phone,
        items: this.cart.map(i => ({ id: i.id, name: i.name, quantity: i.quantity, price: i.price })),
        special_requests,
        total: this.cartTotal,
        session_id: this.sessionId
      };
      this.isLoading = true;
      try {
        const res = await api.submitOrder(orderData);
        this.showToast('Order placed successfully!');
        this.addMessage(`Order placed successfully! Order ID: ${res.order_id || 'N/A'}`, false);
        this.clearCart();
        this.currentView = 'chat';
      } finally { this.isLoading = false }
    },

    async submitReservation() {
      const form = this.reservationForm;
      this.isLoading = true;
      try {
        const res = await api.submitReservation({
          name: form.name,
          email: form.email,
          phone: form.phone,
          party_size: form.party_size,
          date: form.date,
          time: form.time,
          special_requests: form.special_requests,
          session_id: this.sessionId
        });
        this.reservationConfirmationId = res.reservation_id || 'N/A';
        this.reservationConfirmed = true;
        this.showToast('Reservation confirmed!');
        this.addMessage(`Reservation confirmed for ${form.party_size} guests on ${form.date} at ${form.time}`, false);
      } finally { this.isLoading = false }
    }
  }
});
