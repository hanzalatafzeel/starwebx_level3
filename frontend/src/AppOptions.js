// This file exports the Vue options object that was previously created inline
// in the original `index.html`. It uses the Options API so minimal changes
// were required when switching from a CDN-mounted global `Vue` to the
// npm-installed package and a module entry point.

export default {
    data() {
        return {
            // Session & UI
            sessionId: '',
            currentView: 'chat',
            sidebarOpen: false,
            isLoading: false,
            showSettings: false,
            showToast: false,
            toastMessage: '',

            // API & Config
            apiEndpoint: 'http://127.0.0.1:5000/api',
            appTheme: 'auto',

            // Chat
            chatInput: '',
            conversationHistory: [],

            // Menu
            menuItems: [],
            menuSearch: '',
            activeMenuCategory: 'all',
            menuCategories: ['all', 'appetizers', 'main_courses', 'desserts', 'beverages'],

            // Cart & Orders
            cart: [],
            orderForm: {
                /* Lines 364-367 omitted */
                special_requests: ''
            },

            // Chat-based order collection
            chatOrderData: {
                /* Lines 372-376 omitted */
                special_requests: ''
            },
            collectingOrderDetails: false,
            orderDetailStep: 0, // 0: items, 1: name, 2: email, 3: phone

            // Reservations
            reservationForm: {
                /* Lines 383-389 omitted */
                special_requests: ''
            },
            reservationConfirmed: false,
            reservationConfirmationId: '',

            // Navigation
            views: [
                /* Lines 396-399 omitted */
                { id: 'reservations', label: 'Reservations', icon: '📅' }
            ],

            // Quick Actions
            quickActions: [
                /* Lines 404-408 omitted */
            ]
        }
    },

    computed: {
        filteredMenuItems() {
            let items = this.menuItems;

            // Filter by category
            if (this.activeMenuCategory !== 'all') {/* Lines 417-418 omitted */}

            // Filter by search
            if (this.menuSearch) {/* Lines 422-427 omitted */}

            return items;
        },

        cartTotal() {
            return this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        },

        minDate() {
            const today = new Date();
            return today.toISOString().split('T')[0];
        }
    },

    methods: {
        // Initialize
        initializeSession() {
            this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        },

        // Chat methods
        async sendChatMessage() {
            const message = this.chatInput.trim();
            if (!message) return;

            // If we're collecting order details, handle it separately
            if (this.collectingOrderDetails) {/* Lines 455-459 omitted */}

            this.addMessage(message, true);
            this.chatInput = '';
            this.isLoading = true;

            try {
                /* Lines 466-477 omitted */
                this.addMessage(data.response || 'Sorry, I could not process that.', false);
            } catch (error) {
                /* Lines 479-480 omitted */
                this.addMessage(`I apologize, but I'm having trouble connecting to the server. Please check if the Flask backend is running on ${this.apiEndpoint}`, false);
            } finally {/* Lines 482-483 omitted */}
        },

        sendQuickMessage(message) {
            this.chatInput = message;
            this.sendChatMessage();
        },

        addMessage(content, isUser) {
            this.conversationHistory.push({
                /* Lines 493-495 omitted */
                isUser
            });
            this.$nextTick(() => {
            });
        },

        clearChat() {
            this.conversationHistory = [];
            this.addMessage('Chat history cleared. How can I help you today?', false);
            this.showToastMessage('Chat history cleared');
        },

        // Menu methods
        async fetchMenu() {
            try {
            } catch (error) {/* Lines 538-540 omitted */}
        },

        getTags(item) {
            const tags = [];
            if (item.vegan === true) tags.push('Vegan');
            else if (item.vegetarian === true) tags.push('Vegetarian');
            if (item.spicy === true) tags.push('Spicy');
            return tags;
        },

        formatCategoryName(category) {
            const names = {/* Lines 553-558 omitted */};
            return names[category] || category;
        },

        // Cart methods
        addToCart(item) {
            const existingItem = this.cart.find(i => i.id === item.id);

            if (existingItem) {
                existingItem.quantity++;
            } else {/* Lines 569-570 omitted */}

            this.showToastMessage(`${item.name} added to cart`);
        },

        updateCartQuantity(itemId, change) {
            const item = this.cart.find(i => i.id === itemId);
            if (!item) return;

            item.quantity += change;

            if (item.quantity <= 0) {/* Lines 582-583 omitted */}
        },

        removeFromCart(itemId) {
            this.cart = this.cart.filter(i => i.id !== itemId);
            this.showToastMessage('Item removed from cart');
        },

        clearCart() {
            this.cart = [];
            this.orderForm = {/* Lines 594-598 omitted */};
            this.showToastMessage('Cart cleared');
        },

        async placeOrder() {
            const { name, email, phone, special_requests } = this.orderForm;

            if (!name || !email || !phone) {/* Lines 606-608 omitted */}

            try {
                /* Lines 611-636 omitted */
                this.switchView('chat');
            } catch (error) {/* Lines 638-640 omitted */}
        },

        // Reservation methods
        async submitReservation() {
            try {
                /* Lines 646-667 omitted */
                this.addMessage(`Reservation confirmed for ${this.reservationForm.party_size} guests on ${this.reservationForm.date} at ${this.reservationForm.time}`, false);
            } catch (error) {/* Lines 669-671 omitted */}
        },

        // Chat-based Order Placement
        startChatOrderCollection(items) {
            if (!items || items.length === 0) {/* Lines 677-679 omitted */}

            this.chatOrderData.items = items;
            this.collectingOrderDetails = true;
            this.orderDetailStep = 1;

            this.addMessage('Great! To complete your order, I\'ll need some information. What\'s your full name?', false);
        },

        async processChatOrderInput(input) {
            if (!this.collectingOrderDetails) return;

            const step = this.orderDetailStep;

            if (step === 1) {
                /* Lines 694-696 omitted */
                this.addMessage(`Nice to meet you, ${input}! What's your email address?`, false);
            } else if (step === 2) {
                /* Lines 698-700 omitted */
                this.addMessage(`Thanks! And what's your phone number?`, false);
            } else if (step === 3) {
                /* Lines 702-706 omitted */
                this.addMessage(`Perfect! Here's your order summary:\n\n${summary}\n\nTotal: $${total.toFixed(2)}\n\nDo you have any special requests? (or just say "no"/"confirm")`, false);
            } else if (step === 4) {/* Lines 708-716 omitted */}
        },

        async confirmChatOrder() {
            this.isLoading = true;
            try {
                /* Lines 722-741 omitted */
                this.chatOrderData = { items: [], name: '', email: '', phone: '', special_requests: '' };
            } catch (error) {
                /* Lines 743-745 omitted */
                this.collectingOrderDetails = false;
            } finally {/* Lines 747-748 omitted */}
        },

        // UI methods
        switchView(viewId) {
            this.currentView = viewId;
            this.sidebarOpen = false;
        },

        openSettings() {
            this.showSettings = true;
        },

        setTheme(theme) {
            this.appTheme = theme;
            if (theme === 'dark') {
                document.documentElement.setAttribute('data-color-scheme', 'dark');
            } else if (theme === 'light') {
                document.documentElement.setAttribute('data-color-scheme', 'light');
            } else {/* Lines 768-769 omitted */}
            this.showToastMessage(`Theme set to ${theme}`);
        },

        resetSession() {
            this.initializeSession();
            this.showToastMessage('Session reset');
        },

        showToastMessage(message) {
            this.toastMessage = message;
            this.showToast = true;
            setTimeout(() => {
                this.showToast = false;
            }, 3000);
        }
    },

    mounted() {
        this.initializeSession();
        this.fetchMenu();
        this.addMessage('Welcome to Taste Haven! I\'m your AI assistant. How can I help you today?', false);
    }
}
