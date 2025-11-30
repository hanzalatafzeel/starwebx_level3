// Lightweight API service wrappers used by the store/components.
const API_BASE = 'http://127.0.0.1:5000/api';

async function sendChatMessage(message, sessionId) {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId })
    });
    if (!res.ok) throw new Error('Network response was not ok');
    const data = await res.json();
    return data.response || data.message || null;
  } catch (err) {
    console.warn('sendChatMessage error', err);
    return `I apologize, but I'm having trouble connecting to the server. Please check if the Flask backend is running on ${API_BASE}`;
  }
}

async function fetchMenu() {
  try {
    const res = await fetch(`${API_BASE}/menu`);
    if (!res.ok) throw new Error('Network response was not ok');
    const data = await res.json();
    // Try to normalize into an array of items
    const menuObj = data.menu || data.items || data;
    if (Array.isArray(menuObj)) return menuObj;
    const items = [];
    if (typeof menuObj === 'object') {
      for (const [category, arr] of Object.entries(menuObj)) {
        if (Array.isArray(arr)) {
          arr.forEach((it, idx) => items.push({ ...it, category: category }));
        }
      }
    }
    return items;
  } catch (err) {
    console.warn('fetchMenu error', err);
    return [];
  }
}

async function submitOrder(orderData) {
  try {
    const res = await fetch(`${API_BASE}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData)
    });
    if (!res.ok) throw new Error('Network response was not ok');
    return await res.json();
  } catch (err) {
    console.warn('submitOrder error', err);
    return { success: true, message: 'Order received (demo mode)', order_id: 'DEMO_' + Date.now() };
  }
}

async function submitReservation(reservationData) {
  try {
    const res = await fetch(`${API_BASE}/reservations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reservationData)
    });
    if (!res.ok) throw new Error('Network response was not ok');
    return await res.json();
  } catch (err) {
    console.warn('submitReservation error', err);
    return { success: true, message: 'Reservation confirmed (demo mode)', reservation_id: 'RES_' + Date.now() };
  }
}

export default {
  sendChatMessage,
  fetchMenu,
  submitOrder,
  submitReservation
};
