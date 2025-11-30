# Quick Start Guide - Chat-Based Order & Reservation

## Prerequisites
- Node.js installed (for frontend)
- Python 3.8+ installed (for backend)
- Both servers running

## Server Setup

### Backend Server
```bash
cd /media/hanzala/NewVolume2/starwebx/Level_3/resturant_bot

# Install dependencies (first time only)
pip install -r requirements.txt

# Run Flask app
python app.py
# Should show: Running on http://127.0.0.1:5000
```

### Frontend Server
```bash
cd /media/hanzala/NewVolume2/starwebx/Level_3/frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
# Should show: Local: http://localhost:5173
```

## Testing Order Flow

### Step 1: Open Chat
Navigate to http://localhost:5173 and go to the Chat tab

### Step 2: Trigger Order Intent
Type one of these:
- "I want to place an order"
- "I'd like to order"
- "Can I have a pizza and pasta"
- "I want to buy something"

### Step 3: Follow Bot Prompts
The bot will ask for:
1. Menu items you want (from your user message)
2. Your name
3. Your email address
4. Your phone number
5. Any special requests

### Step 4: Confirm
Type "no" or "none" if no special requests, or specify them

### Expected Output
```
✅ Order #1 Confirmed!
Total: $XX.XX
Thank you for your order!
```

## Testing Reservation Flow

### Step 1: Trigger Reservation Intent
Type one of these:
- "I want to make a reservation"
- "I'd like to book a table"
- "Can I reserve a table"
- "I need a reservation"

### Step 2: Follow Bot Prompts
The bot will ask for:
1. Your name
2. Your email
3. Your phone number
4. Party size (number of people)
5. Date (YYYY-MM-DD format)
6. Time (HH:MM format, e.g., 19:30)
7. Special requests

### Step 3: Confirm
Type "no" or "none" if no special requests, or specify them

### Expected Output
```
✅ Reservation #1 Confirmed!
Table for 4 on 2024-12-25 at 19:00
Thank you!
```

## Database Verification

After placing an order or reservation, check the database:

```bash
cd /media/hanzala/NewVolume2/starwebx/Level_3/resturant_bot

# Open SQLite database
sqlite3 restaurant.db

# View orders
SELECT * FROM "order";

# View reservations
SELECT * FROM reservation;

# View conversations
SELECT * FROM conversation;

# Exit
.exit
```

## Troubleshooting

### "Message not working" or "Bot not responding"
1. Check backend is running on port 5000
2. Check frontend has correct API endpoint: `http://127.0.0.1:5000/api`
3. Check browser console for errors (F12 → Console)
4. Check terminal for backend errors

### "Email/Phone validation failing"
- Email must be valid format: `user@domain.com`
- Phone must be numeric or standard format: `555-1234` or `5551234`

### "Date in past" error
- Ensure date is today or in the future
- Format must be YYYY-MM-DD (e.g., 2024-12-25)

### "Invalid time" error
- Format must be HH:MM in 24-hour format
- Valid range: 00:00 to 23:59

## Common Test Scenarios

### Scenario 1: Complete Order
```
User: I want to order 2 pizzas and a coke
Bot: Great! I found Pizza, Coke in your message. What's your name?
User: John Smith
Bot: Thanks! What's your email address?
User: john@example.com
Bot: Great! What's your phone number?
User: 555-1234567
Bot: Perfect! Order summary...
User: Extra cheese on pizza
Bot: ✅ Order confirmed!
```

### Scenario 2: Complete Reservation
```
User: Book me a table for 4 people
Bot: I'll help you make a reservation! What's your name?
User: Sarah Johnson
Bot: What's your email address?
User: sarah@email.com
Bot: What's your phone number?
User: 555-9876543
Bot: How many people? (1-20)
User: 4
Bot: What date? (YYYY-MM-DD)
User: 2024-12-25
Bot: What time? (HH:MM)
User: 19:30
Bot: Any special requests?
User: Window seat please
Bot: ✅ Reservation confirmed!
```

### Scenario 3: Invalid Email Retry
```
User: I want to order pizza
Bot: I found Pizza. What's your name?
User: John
Bot: Thanks! What's your email?
User: invalid-email (missing @)
Bot: That doesn't look like a valid email. Please try again.
User: john@example.com
Bot: Great! What's your phone number?
...
```

## Features

✅ Multi-turn conversation for order placement  
✅ Multi-turn conversation for reservations  
✅ Automatic menu item extraction from user message  
✅ Email/phone validation with friendly error messages  
✅ Date validation (must be future)  
✅ Time validation (24-hour format)  
✅ Party size validation (1-20)  
✅ Database persistence  
✅ Conversation history tracking  
✅ Natural language bot responses  
✅ Session tracking for multi-turn flows  

## API Endpoints

### Order Collection
- **Endpoint:** `POST /api/chat/order-intent`
- **Rate:** 20 requests/minute
- **Fields:** message, session_id, step, collected_data

### Reservation Collection
- **Endpoint:** `POST /api/chat/reservation-intent`
- **Rate:** 20 requests/minute
- **Fields:** message, session_id, step, collected_data

### Normal Chat
- **Endpoint:** `POST /api/chat`
- **Rate:** 20 requests/minute

## Success Indicators

- ✅ Chat opens without errors
- ✅ Order flow completes with "Order #X Confirmed!"
- ✅ Reservation flow completes with "Reservation #X Confirmed!"
- ✅ Data appears in database
- ✅ Conversation history shows in database
- ✅ Validation messages appear for invalid inputs
- ✅ No console errors in browser
- ✅ No errors in backend terminal
