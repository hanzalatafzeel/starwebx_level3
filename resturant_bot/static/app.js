// Application State (using in-memory storage instead of localStorage)
let appState = {
  sessionId: null,
  conversationHistory: [],
  cart: [],
  apiEndpoint: 'http://:5000/api',
  theme: 'auto',
  menuItems: []
};

// Sample Menu Data (fallback if API is unavailable)
const sampleMenu = [
  { id: 1, name: 'Caesar Salad', category: 'appetizers', price: 8.99, description: 'Fresh romaine lettuce with parmesan and croutons', tags: ['Vegetarian'] },
  { id: 2, name: 'Bruschetta', category: 'appetizers', price: 7.99, description: 'Toasted bread with tomatoes and basil', tags: ['Vegan'] },
  { id: 3, name: 'Grilled Salmon', category: 'mains', price: 22.99, description: 'Fresh Atlantic salmon with seasonal vegetables', tags: [] },
  { id: 4, name: 'Chicken Tikka Masala', category: 'mains', price: 18.99, description: 'Tender chicken in creamy tomato sauce', tags: ['Spicy'] },
  { id: 5, name: 'Margherita Pizza', category: 'mains', price: 14.99, description: 'Classic tomato, mozzarella, and basil', tags: ['Vegetarian'] },
  { id: 6, name: 'Vegetable Stir Fry', category: 'mains', price: 15.99, description: 'Fresh vegetables in savory sauce', tags: ['Vegan', 'Spicy'] },
  { id: 7, name: 'Tiramisu', category: 'desserts', price: 6.99, description: 'Classic Italian coffee-flavored dessert', tags: [] },
  { id: 8, name: 'Chocolate Lava Cake', category: 'desserts', price: 7.99, description: 'Warm chocolate cake with molten center', tags: ['Vegetarian'] },
  { id: 9, name: 'Fresh Lemonade', category: 'beverages', price: 3.99, description: 'Freshly squeezed lemon juice', tags: ['Vegan'] },
  { id: 10, name: 'Cappuccino', category: 'beverages', price: 4.99, description: 'Espresso with steamed milk foam', tags: ['Vegetarian'] }
];

// Initialize Session ID
function initializeSession() {
  if (!appState.sessionId) {
    appState.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }
  document.getElementById('sessionId').textContent = appState.sessionId.substr(0, 20) + '...';
}

// API Functions
async function sendChatMessage(message) {
  try {
    const response = await fetch(`${appState.apiEndpoint}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        session_id: appState.sessionId
      })
    });
    
    if (!response.ok) throw new Error('Network response was not ok');
    const data = await response.json();
    return data.response || data.message || 'Sorry, I could not process that.';
  } catch (error) {
    console.error('Chat API error:', error);
    return 'I apologize, but I\'m having trouble connecting to the server. Please check if the Flask backend is running on ' + appState.apiEndpoint;
  }
}

async function fetchMenu() {
  try {
    const response = await fetch(`${appState.apiEndpoint}/menu`);
    if (!response.ok) throw new Error('Network response was not ok');
    const data = await response.json();
    appState.menuItems = data.menu || data.items || data;
  } catch (error) {
    console.error('Menu API error:', error);
    appState.menuItems = sampleMenu;
    showToast('Using sample menu data (server not available)');
  }
  renderMenu();
}

async function submitOrder(orderData) {
  try {
    const response = await fetch(`${appState.apiEndpoint}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData)
    });
    
    if (!response.ok) throw new Error('Network response was not ok');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Order API error:', error);
    return { success: true, message: 'Order received (demo mode)', order_id: 'DEMO_' + Date.now() };
  }
}

async function submitReservation(reservationData) {
  try {
    const response = await fetch(`${appState.apiEndpoint}/reservations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reservationData)
    });
    
    if (!response.ok) throw new Error('Network response was not ok');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Reservation API error:', error);
    return { success: true, message: 'Reservation confirmed (demo mode)', reservation_id: 'RES_' + Date.now() };
  }
}

// Chat Functions
function addMessage(content, isUser = false) {
  const messagesContainer = document.getElementById('chatMessages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
  
  messageDiv.innerHTML = `
    <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
    <div class="message-content">
      <p>${escapeHtml(content)}</p>
    </div>
  `;
  
  messagesContainer.appendChild(messageDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  // Store in conversation history
  appState.conversationHistory.push({ role: isUser ? 'user' : 'bot', content, timestamp: Date.now() });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function handleSendMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  
  if (!message) return;
  
  // Add user message
  addMessage(message, true);
  input.value = '';
  
  // Show typing indicator
  const typingIndicator = document.getElementById('typingIndicator');
  typingIndicator.style.display = 'flex';
  
  // Get bot response
  const response = await sendChatMessage(message);
  
  // Hide typing indicator
  typingIndicator.style.display = 'none';
  
  // Add bot response
  addMessage(response, false);
}

function clearChat() {
  const messagesContainer = document.getElementById('chatMessages');
  messagesContainer.innerHTML = `
    <div class="message bot-message">
      <div class="message-avatar">🤖</div>
      <div class="message-content">
        <p>Chat history cleared. How can I help you today?</p>
      </div>
    </div>
  `;
  appState.conversationHistory = [];
  showToast('Chat history cleared');
}

// Menu Functions
function renderMenu(filter = 'all', searchQuery = '') {
  const menuContainer = document.getElementById('menuItems');
  
  let filteredItems = appState.menuItems;
  
  // Apply category filter
  if (filter !== 'all') {
    filteredItems = filteredItems.filter(item => item.category === filter);
  }
  
  // Apply search filter
  if (searchQuery) {
    filteredItems = filteredItems.filter(item => 
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }
  
  if (filteredItems.length === 0) {
    menuContainer.innerHTML = '<div class="empty-state"><p>No items found</p></div>';
    return;
  }
  
  menuContainer.innerHTML = filteredItems.map(item => `
    <div class="menu-item" data-id="${item.id}">
      <div class="menu-item-header">
        <h3 class="menu-item-name">${escapeHtml(item.name)}</h3>
        <span class="menu-item-price">$${item.price.toFixed(2)}</span>
      </div>
      <p class="menu-item-description">${escapeHtml(item.description)}</p>
      ${item.tags && item.tags.length > 0 ? `
        <div class="menu-item-tags">
          ${item.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
        </div>
      ` : ''}
      <button class="add-to-cart-btn" onclick="addToCart(${item.id})">Add to Cart</button>
    </div>
  `).join('');
}

// Cart Functions
function addToCart(itemId) {
  const item = appState.menuItems.find(i => i.id === itemId);
  if (!item) return;
  
  const existingItem = appState.cart.find(i => i.id === itemId);
  
  if (existingItem) {
    existingItem.quantity++;
  } else {
    appState.cart.push({ ...item, quantity: 1 });
  }
  
  showToast(`${item.name} added to cart`);
  updateCartDisplay();
}

function updateCartQuantity(itemId, change) {
  const item = appState.cart.find(i => i.id === itemId);
  if (!item) return;
  
  item.quantity += change;
  
  if (item.quantity <= 0) {
    appState.cart = appState.cart.filter(i => i.id !== itemId);
  }
  
  updateCartDisplay();
}

function removeFromCart(itemId) {
  appState.cart = appState.cart.filter(i => i.id !== itemId);
  updateCartDisplay();
  showToast('Item removed from cart');
}

function updateCartDisplay() {
  const cartContainer = document.getElementById('cartItems');
  const orderForm = document.getElementById('orderForm');
  
  if (appState.cart.length === 0) {
    cartContainer.innerHTML = `
      <div class="empty-state">
        <p>🛒 Your cart is empty</p>
        <p>Add items from the menu to get started!</p>
      </div>
    `;
    orderForm.style.display = 'none';
    return;
  }
  
  const total = appState.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  
  cartContainer.innerHTML = appState.cart.map(item => `
    <div class="cart-item">
      <div class="cart-item-info">
        <div class="cart-item-name">${escapeHtml(item.name)}</div>
        <div class="cart-item-price">$${item.price.toFixed(2)} each</div>
      </div>
      <div class="cart-item-controls">
        <button class="quantity-btn" onclick="updateCartQuantity(${item.id}, -1)">−</button>
        <span class="quantity">${item.quantity}</span>
        <button class="quantity-btn" onclick="updateCartQuantity(${item.id}, 1)">+</button>
        <button class="remove-btn" onclick="removeFromCart(${item.id})" aria-label="Remove item">🗑️</button>
      </div>
    </div>
  `).join('');
  
  document.getElementById('orderTotal').textContent = `$${total.toFixed(2)}`;
  orderForm.style.display = 'block';
}

function clearCart() {
  appState.cart = [];
  updateCartDisplay();
  showToast('Cart cleared');
}

async function placeOrder() {
  const name = document.getElementById('customerName').value.trim();
  const email = document.getElementById('customerEmail').value.trim();
  const phone = document.getElementById('customerPhone').value.trim();
  const specialRequests = document.getElementById('specialRequests').value.trim();
  
  if (!name || !email || !phone) {
    showToast('Please fill in all required fields');
    return;
  }
  
  const orderData = {
    customer_name: name,
    customer_email: email,
    customer_phone: phone,
    items: appState.cart.map(item => ({ id: item.id, name: item.name, quantity: item.quantity, price: item.price })),
    special_requests: specialRequests,
    total: appState.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
    session_id: appState.sessionId
  };
  
  const result = await submitOrder(orderData);
  
  if (result.success !== false) {
    showToast('Order placed successfully!');
    appState.cart = [];
    updateCartDisplay();
    document.getElementById('customerName').value = '';
    document.getElementById('customerEmail').value = '';
    document.getElementById('customerPhone').value = '';
    document.getElementById('specialRequests').value = '';
    
    // Add confirmation to chat
    addMessage(`Order placed successfully! Order ID: ${result.order_id || 'N/A'}`, false);
    switchView('chat');
  } else {
    showToast('Error placing order. Please try again.');
  }
}

// Reservation Functions
async function handleReservationSubmit(event) {
  event.preventDefault();
  
  const formData = {
    name: document.getElementById('guestName').value.trim(),
    email: document.getElementById('guestEmail').value.trim(),
    phone: document.getElementById('guestPhone').value.trim(),
    party_size: parseInt(document.getElementById('partySize').value),
    date: document.getElementById('reservationDate').value,
    time: document.getElementById('reservationTime').value,
    special_requests: document.getElementById('reservationRequests').value.trim(),
    session_id: appState.sessionId
  };
  
  const result = await submitReservation(formData);
  
  if (result.success !== false) {
    const confirmationDiv = document.getElementById('reservationConfirmation');
    confirmationDiv.innerHTML = `
      <div class="confirmation-icon">✅</div>
      <div class="confirmation-message">
        <h3>Reservation Confirmed!</h3>
        <p>Your table has been reserved.</p>
      </div>
      <div class="confirmation-details">
        <p><strong>Name:</strong> ${escapeHtml(formData.name)}</p>
        <p><strong>Party Size:</strong> ${formData.party_size} guests</p>
        <p><strong>Date:</strong> ${formData.date}</p>
        <p><strong>Time:</strong> ${formData.time}</p>
        <p><strong>Confirmation:</strong> ${result.reservation_id || 'N/A'}</p>
      </div>
    `;
    confirmationDiv.style.display = 'block';
    document.getElementById('reservationForm').style.display = 'none';
    
    showToast('Reservation confirmed!');
    
    // Add confirmation to chat
    addMessage(`Reservation confirmed for ${formData.party_size} guests on ${formData.date} at ${formData.time}`, false);
  } else {
    showToast('Error making reservation. Please try again.');
  }
}

// Navigation Functions
function switchView(viewId) {
  // Update nav items
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    if (item.dataset.view === viewId) {
      item.classList.add('active');
    }
  });
  
  // Update views
  document.querySelectorAll('.view').forEach(view => {
    view.classList.remove('active');
  });
  document.getElementById(`${viewId}View`).classList.add('active');
  
  // Close mobile menu if open
  document.getElementById('sidebar').classList.remove('open');
}

// Settings Functions
function openSettings() {
  document.getElementById('settingsModal').style.display = 'flex';
  document.getElementById('apiEndpoint').value = appState.apiEndpoint;
}

function closeSettings() {
  document.getElementById('settingsModal').style.display = 'none';
}

function updateApiEndpoint() {
  const newEndpoint = document.getElementById('apiEndpoint').value.trim();
  if (newEndpoint) {
    appState.apiEndpoint = newEndpoint;
    showToast('API endpoint updated');
  }
}

function setTheme(theme) {
  appState.theme = theme;
  document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.theme === theme) {
      btn.classList.add('active');
    }
  });
  
  // Apply theme (this is a simplified version)
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-color-scheme', 'dark');
  } else if (theme === 'light') {
    document.documentElement.setAttribute('data-color-scheme', 'light');
  } else {
    document.documentElement.removeAttribute('data-color-scheme');
  }
  
  showToast(`Theme set to ${theme}`);
}

function resetSession() {
  appState.sessionId = null;
  initializeSession();
  showToast('Session reset');
}

// Toast Notification
function showToast(message) {
  const toast = document.getElementById('toast');
  const toastMessage = document.getElementById('toastMessage');
  
  toastMessage.textContent = message;
  toast.style.display = 'block';
  
  setTimeout(() => {
    toast.style.display = 'none';
  }, 3000);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  // Initialize
  initializeSession();
  fetchMenu();
  
  // Chat events
  document.getElementById('sendBtn').addEventListener('click', handleSendMessage);
  document.getElementById('chatInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSendMessage();
  });
  document.getElementById('clearChatBtn').addEventListener('click', clearChat);
  
  // Quick actions
  document.querySelectorAll('.quick-action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const message = btn.dataset.message;
      document.getElementById('chatInput').value = message;
      handleSendMessage();
    });
  });
  
  // Navigation
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      switchView(item.dataset.view);
    });
  });
  
  // Mobile menu
  document.getElementById('menuToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
  
  // Menu tabs
  document.querySelectorAll('.menu-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.menu-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderMenu(tab.dataset.category, document.getElementById('menuSearch').value);
    });
  });
  
  // Menu search
  document.getElementById('menuSearch').addEventListener('input', (e) => {
    const activeTab = document.querySelector('.menu-tab.active');
    renderMenu(activeTab.dataset.category, e.target.value);
  });
  
  // Orders
  document.getElementById('clearCartBtn').addEventListener('click', clearCart);
  document.getElementById('placeOrderBtn').addEventListener('click', placeOrder);
  
  // Reservations
  document.getElementById('reservationForm').addEventListener('submit', handleReservationSubmit);
  
  // Settings
  document.getElementById('settingsBtn').addEventListener('click', openSettings);
  document.getElementById('closeSettings').addEventListener('click', closeSettings);
  document.getElementById('apiEndpoint').addEventListener('change', updateApiEndpoint);
  document.getElementById('clearHistoryBtn').addEventListener('click', clearChat);
  document.getElementById('resetSessionBtn').addEventListener('click', resetSession);
  
  // Theme buttons
  document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      setTheme(btn.dataset.theme);
    });
  });
  
  // Close modal on outside click
  document.getElementById('settingsModal').addEventListener('click', (e) => {
    if (e.target.id === 'settingsModal') {
      closeSettings();
    }
  });
  
  // Set minimum date for reservations (today)
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('reservationDate').setAttribute('min', today);
});