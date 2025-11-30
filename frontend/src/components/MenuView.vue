<template>
  <div class="view menu-view">
    <div class="view-header">
      <h2>Our Menu</h2>
      <div class="menu-search">
        <input placeholder="Search menu..." v-model="store.menuSearch" />
      </div>
    </div>

    <div class="menu-tabs">
      <button v-for="c in store.menuCategories" :key="c" class="menu-tab" :class="{ active: store.activeMenuCategory === c }" @click="() => store.activeMenuCategory = c">{{ formatCategoryName(c) }}</button>
    </div>

    <div class="menu-items" id="menuItems">
      <div v-if="store.filteredMenuItems.length === 0" class="empty-state">
        <p>No items found</p>
      </div>

      <div v-for="item in store.filteredMenuItems" :key="item.id" class="menu-item" :data-id="item.id">
        <div class="menu-item-header">
          <h3 class="menu-item-name">{{ item.name }}</h3>
          <span class="menu-item-price">${{ (item.price || 0).toFixed(2) }}</span>
        </div>
        <p class="menu-item-description">{{ item.description }}</p>
        <div class="menu-item-tags" v-if="getTags(item).length">
          <span v-for="t in getTags(item)" :key="t" class="tag">{{ t }}</span>
        </div>
        <button class="add-to-cart-btn" @click="() => store.addToCart(item)">Add to Cart</button>
      </div>
    </div>
  </div>
</template>

<script>
import { useMainStore } from '@/store'
export default {
  setup() {
    const store = useMainStore();
    function getTags(item) {
      const tags = [];
      if (item.vegan === true) tags.push('Vegan');
      else if (item.vegetarian === true) tags.push('Vegetarian');
      if (item.spicy === true) tags.push('Spicy');
      return tags;
    }
    function formatCategoryName(c) {
      const names = { 'all': 'All', 'appetizers': 'Appetizers', 'main_courses': 'Main Courses', 'desserts': 'Desserts', 'beverages': 'Beverages' };
      return names[c] || c;
    }
    return { store, getTags, formatCategoryName };
  }
}
</script>
