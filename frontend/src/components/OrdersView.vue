<template>
  <div class="view orders-view">
    <div class="view-header">
      <h2>Your Order</h2>
      <button class="clear-cart-btn" @click="store.clearCart" v-if="store.cart.length > 0">Clear Cart</button>
    </div>

    <div class="cart-items" id="cartItems">
      <div v-if="store.cart.length === 0" class="empty-state">
        <p>🛒 Your cart is empty</p>
        <p>Add items from the menu to get started!</p>
      </div>

      <div v-for="item in store.cart" :key="item.id" class="cart-item">
        <div class="cart-item-info">
          <div class="cart-item-name">{{ item.name }}</div>
          <div class="cart-item-price">${{ (item.price || 0).toFixed(2) }} each</div>
        </div>
        <div class="cart-item-controls">
          <button class="quantity-btn" @click="() => store.updateCartQuantity(item.id, -1)">−</button>
          <span class="quantity">{{ item.quantity }}</span>
          <button class="quantity-btn" @click="() => store.updateCartQuantity(item.id, 1)">+</button>
          <button class="remove-btn" @click="() => store.removeFromCart(item.id)">🗑️</button>
        </div>
      </div>
    </div>

    <div class="order-form" v-if="store.cart.length > 0" id="orderForm">
      <h3>Order Details</h3>
      <div class="form-group">
        <label>Name</label>
        <input v-model="store.orderForm.name" />
      </div>
      <div class="form-group">
        <label>Email</label>
        <input v-model="store.orderForm.email" />
      </div>
      <div class="form-group">
        <label>Phone</label>
        <input v-model="store.orderForm.phone" />
      </div>
      <div class="form-group">
        <label>Special requests</label>
        <textarea v-model="store.orderForm.special_requests"></textarea>
      </div>
      <div class="order-total">
        <h3>Total: <span>${{ store.cartTotal.toFixed(2) }}</span></h3>
      </div>
      <button class="btn btn-primary" @click="store.placeOrder">Place Order</button>
    </div>
  </div>
</template>

<script>
import { useMainStore } from '@/store'
export default { setup() { const store = useMainStore(); return { store } } }
</script>
