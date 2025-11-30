import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/components/ChatView.vue'
import MenuView from '@/components/MenuView.vue'
import OrdersView from '@/components/OrdersView.vue'
import ReservationsView from '@/components/ReservationsView.vue'

const routes = [
  { path: '/', redirect: '/chat' },
  { path: '/chat', name: 'chat', component: ChatView },
  { path: '/menu', name: 'menu', component: MenuView },
  { path: '/orders', name: 'orders', component: OrdersView },
  { path: '/reservations', name: 'reservations', component: ReservationsView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
