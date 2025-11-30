<template>
  <div class="view reservations-view">
    <div class="view-header">
      <h2>Reservations</h2>
    </div>

    <form class="reservation-form" @submit.prevent="store.submitReservation" v-if="!store.reservationConfirmed">
      <div class="form-row">
        <div class="form-group"><label>Name</label><input v-model="store.reservationForm.name" required /></div>
        <div class="form-group"><label>Email</label><input v-model="store.reservationForm.email" required /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Phone</label><input v-model="store.reservationForm.phone" required /></div>
        <div class="form-group"><label>Party Size</label><input type="number" v-model.number="store.reservationForm.party_size" min="1" required /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Date</label><input type="date" v-model="store.reservationForm.date" :min="minDate" required /></div>
        <div class="form-group"><label>Time</label><input type="time" v-model="store.reservationForm.time" required /></div>
      </div>
      <div class="form-group"><label>Special requests</label><textarea v-model="store.reservationForm.special_requests"></textarea></div>
      <button class="btn btn-primary" type="submit">Reserve</button>
    </form>

    <div v-if="store.reservationConfirmed" class="reservation-confirmation">
      <div class="confirmation-icon">✅</div>
      <div class="confirmation-message">
        <h3>Reservation Confirmed!</h3>
        <p>Your table has been reserved.</p>
      </div>
      <div class="confirmation-details">
        <p><strong>Name:</strong> {{ store.reservationForm.name }}</p>
        <p><strong>Party Size:</strong> {{ store.reservationForm.party_size }}</p>
        <p><strong>Date:</strong> {{ store.reservationForm.date }}</p>
        <p><strong>Time:</strong> {{ store.reservationForm.time }}</p>
        <p><strong>Confirmation:</strong> {{ store.reservationConfirmationId }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useMainStore } from '@/store'
export default {
  setup() {
    const store = useMainStore();
    const minDate = computed(() => new Date().toISOString().split('T')[0]);
    return { store, minDate };
  }
}
</script>
