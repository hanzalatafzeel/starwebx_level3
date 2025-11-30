# Chat-Based Order & Reservation Implementation

## Overview
Successfully implemented **multi-turn conversation flows** for both **order placement** and **reservation booking** through the chat interface.

## Features Implemented

### 1. Backend Endpoints (Flask)

#### `/api/chat/order-intent` (POST)
**Purpose:** Handle multi-step order collection through conversation

**Flow:**
- **Step 0:** Collect menu items (user specifies what they want)
- **Step 1:** Collect customer name
- **Step 2:** Collect email address (with validation)
- **Step 3:** Collect phone number (with validation)
- **Step 4:** Collect special requests, then create order in database

**Validation:**
- Email validation using existing `validate_email()` function
- Phone validation using existing `validate_phone()` function
- Menu item extraction from user message using `extract_order_items_from_message()`

**Response:**
```json
{
  "success": true,
  "response": "Natural language response to user",
  "step": 1,
  "collected_data": {
    "items": [...],
    "customer_name": "John"
  },
  "session_id": "session_123"
}
```

#### `/api/chat/reservation-intent` (POST)
**Purpose:** Handle multi-step reservation collection through conversation

**Flow:**
- **Step 0:** Collect customer name
- **Step 1:** Collect email address (with validation)
- **Step 2:** Collect phone number (with validation)
- **Step 3:** Collect party size (1-20, validated)
- **Step 4:** Collect reservation date (YYYY-MM-DD format, must be future date)
- **Step 5:** Collect reservation time (HH:MM format validation)
- **Step 6:** Collect special requests, then create reservation in database

**Validation:**
- Email and phone validation
- Party size: 1-20 range
- Date: Must be today or in the future
- Time: Valid 24-hour format (00:00-23:59)

**Response:**
Same structure as order intent with appropriate data

### 2. Frontend State Management (Pinia Store)

**New State Variables:**
```javascript
orderCollectionMode: false,        // Flag: are we collecting order?
orderCollectionStep: 0,            // Current step in order flow (0-4)
orderCollectionData: {},           // Data collected so far

reservationCollectionMode: false,  // Flag: are we collecting reservation?
reservationCollectionStep: 0,      // Current step in reservation flow (0-6)
reservationCollectionData: {},     // Data collected so far
```

**Updated `sendChatMessage()` Action:**

The action now implements intelligent message routing:

1. **If in order collection mode:**
   - Send message to `/api/chat/order-intent` endpoint
   - Update order collection step and data
   - Display bot response
   - Exit mode when step returns to 0 (order complete)

2. **If in reservation collection mode:**
   - Send message to `/api/chat/reservation-intent` endpoint
   - Update reservation collection step and data
   - Display bot response
   - Exit mode when step returns to 0 (reservation complete)

3. **If order keywords detected** (`order`, `place an order`, `i want`, `can i have`, `give me`, `get me`, `buy`, `purchase`):
   - Activate `orderCollectionMode = true`
   - Initialize step to 0 and empty data
   - Show initial prompt: "I'll help you place an order! Which items would you like?"

4. **If reservation keywords detected** (`reservation`, `reserve`, `book`, `table`, `booking`, `dinner reservation`, `lunch reservation`):
   - Activate `reservationCollectionMode = true`
   - Initialize step to 0 and empty data
   - Show initial prompt: "I'll help you make a reservation! What's your name?"

5. **Otherwise:**
   - Normal chat flow via existing `/api/chat` endpoint

## How It Works

### Order Flow Example
```
User: "I want to place an order"
Bot:  "I'll help you place an order! Which items would you like?"

User: "I'd like 2 pizzas and 1 pasta"
Bot:  "Great! I found Pizza, Pasta in your message. What's your name?"

User: "John Smith"
Bot:  "Thanks! What's your email address?"

User: "john@example.com"
Bot:  "Great! What's your phone number?"

User: "555-1234"
Bot:  "Perfect! Here's your order summary:
       2x Pizza, 1x Pasta
       Total: $45.99
       Any special requests? (or just say 'no')"

User: "No extra onions on pizza please"
Bot:  "✅ Order #123 Confirmed!
       Total: $45.99
       Thank you for your order!"
```

### Reservation Flow Example
```
User: "I want to make a reservation"
Bot:  "I'll help you make a reservation! What's your name?"

User: "Sarah Johnson"
Bot:  "What's your email address?"

User: "sarah@email.com"
Bot:  "What's your phone number?"

User: "555-5678"
Bot:  "How many people in your party? (1-20)"

User: "4"
Bot:  "What date would you like? (YYYY-MM-DD)"

User: "2024-12-25"
Bot:  "What time would you like? (HH:MM, e.g., 19:30)"

User: "19:00"
Bot:  "Perfect! Let me confirm:
       Name: Sarah Johnson
       Party size: 4
       Date: 2024-12-25
       Time: 19:00
       Any special requests? (or say 'no')"

User: "Window seat please"
Bot:  "✅ Reservation #456 Confirmed!
       Table for 4 on 2024-12-25 at 19:00
       Thank you!"
```

## Database Integration

Both endpoints:
- Create records in the database (Order or Reservation tables)
- Store conversations in the Conversation table
- Assign conversation message_type ('order' or 'reservation')
- Include session tracking for multi-turn conversations

## Conversation History

Each step in the conversation is stored in the database:
- User messages
- Bot responses
- Message type (order/reservation)
- Session ID
- Timestamp (auto-generated)

This enables:
- Conversation replay
- Analytics on order/reservation flows
- Debugging user interactions

## Testing

### Test Order Flow:
1. Open chat interface
2. Type: "I want to place an order"
3. Follow prompts to provide items, name, email, phone
4. Verify order appears in database

### Test Reservation Flow:
1. Open chat interface
2. Type: "I'd like to make a reservation"
3. Follow prompts to provide all required details
4. Verify reservation appears in database

### Test Validation:
- Try invalid email: should ask again
- Try invalid phone: should ask again
- Try party size > 20: should ask again
- Try past date: should ask again
- Try invalid time: should ask again

## Edge Cases Handled

✅ Empty messages - validation in store  
✅ Invalid email format - rejected with friendly message  
✅ Invalid phone format - rejected with friendly message  
✅ Party size out of range - rejected with friendly message  
✅ Past dates - rejected as invalid  
✅ Invalid time format - rejected with friendly message  
✅ User exits mid-flow - handled gracefully  
✅ Network errors - fallback in frontend  
✅ Database errors - proper error logging and responses  

## API Compliance

- Rate limited to 20 requests per minute (via Flask-Limiter)
- CORS enabled for frontend communication
- Proper error responses with HTTP status codes
- JSON request/response format
- Session tracking for multi-turn conversations

## Files Modified

1. **Backend:** `/resturant_bot/app.py`
   - Added `/api/chat/order-intent` endpoint (lines 879-987)
   - Added `/api/chat/reservation-intent` endpoint (lines 989-1097)

2. **Frontend:** `/frontend/src/store/index.js`
   - Added state variables for order collection
   - Added state variables for reservation collection
   - Updated `sendChatMessage()` action with intent detection and multi-step routing

## Future Enhancements

- Add UI progress indicators showing "Step 2 of 4"
- Add ability to cancel mid-flow with "cancel" command
- Add menu items display when asking for items
- Add order/reservation modification through chat
- Add payment method selection through chat
- Add dietary restrictions collection for reservations
- Add recommended items based on order history
