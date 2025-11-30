# Architecture Diagram - Chat-Based Order & Reservation System

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue 3 + Pinia)                     │
│                          Port 5173 (Vite)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐       ┌─────────────────────────────────┐   │
│  │   ChatView.vue   │       │     Pinia Store (index.js)      │   │
│  │                  │       │                                 │   │
│  │  • Message list  │◄─────►│  • conversationHistory          │   │
│  │  • Input field   │       │  • chatInput                    │   │
│  │  • Send button   │       │  • sessionId                    │   │
│  └──────────────────┘       │  • orderCollectionMode ✨       │   │
│                              │  • orderCollectionStep ✨       │   │
│                              │  • orderCollectionData ✨       │   │
│                              │  • reservationCollectionMode ✨ │   │
│                              │  • reservationCollectionStep ✨ │   │
│                              │  • reservationCollectionData ✨ │   │
│                              │                                 │   │
│                              │  sendChatMessage() Action:      │   │
│                              │  ┌─────────────────────────┐   │   │
│                              │  │ 1. Check if in order    │   │   │
│                              │  │    collection mode      │   │   │
│                              │  │    YES → Route to ✨    │   │   │
│                              │  │    /api/chat/order...   │   │   │
│                              │  ├─────────────────────────┤   │   │
│                              │  │ 2. Check if in          │   │   │
│                              │  │    reservation mode     │   │   │
│                              │  │    YES → Route to ✨    │   │   │
│                              │  │    /api/chat/reservation│   │   │
│                              │  ├─────────────────────────┤   │   │
│                              │  │ 3. Check for order      │   │   │
│                              │  │    keywords             │   │   │
│                              │  │    YES → Activate ✨    │   │   │
│                              │  │    order mode           │   │   │
│                              │  ├─────────────────────────┤   │   │
│                              │  │ 4. Check for            │   │   │
│                              │  │    reservation keywords │   │   │
│                              │  │    YES → Activate ✨    │   │   │
│                              │  │    reservation mode     │   │   │
│                              │  ├─────────────────────────┤   │   │
│                              │  │ 5. Else: Normal chat    │   │   │
│                              │  │    → /api/chat          │   │   │
│                              │  └─────────────────────────┘   │   │
│                              └─────────────────────────────────┘   │
│                                                                       │
│  HTTP Fetch Requests ↓                                              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ JSON POST Requests
                                  │ (session_id, message, step, data)
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (Flask + SQLAlchemy)                     │
│                          Port 5000                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Routing Layer (Flask Routes)                  │    │
│  └────────────────────────────────────────────────────────────┘    │
│           │                    │                    │              │
│           ▼                    ▼                    ▼              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  /api/chat       │  │  /api/chat/      │  │  /api/chat/      │ │
│  │                  │  │  order-intent ✨ │  │  reservation-int.│ │
│  │  (Normal Chat)   │  │                  │  │  (New) ✨        │ │
│  │                  │  │  (New) ✨        │  │                  │ │
│  │  • Send to       │  │                  │  │  • Step: 0-6     │ │
│  │    Gemini API    │  │  • Step: 0-4     │  │  • Collect:      │ │
│  │  • Get response  │  │  • Collect:      │  │    - Name        │ │
│  │  • Store in DB   │  │    - Items       │  │    - Email       │ │
│  │                  │  │    - Name        │  │    - Phone       │ │
│  └──────────────────┘  │    - Email       │  │    - Party size  │ │
│                        │    - Phone       │  │    - Date        │ │
│                        │    - Requests    │  │    - Time        │ │
│                        │  • Validate:     │  │    - Requests    │ │
│                        │    - Email       │  │  • Validate:     │ │
│                        │    - Phone       │  │    - Email       │ │
│                        │  • Extract items │  │    - Phone       │ │
│                        │    from message  │  │    - Size (1-20) │ │
│                        │  • Create Order  │  │    - Date (fut.)  │ │
│                        │    when done     │  │    - Time (valid)│ │
│                        │  • Response:     │  │  • Create        │ │
│                        │    - Text for    │  │    Reservation   │ │
│                        │      next step   │  │    when done     │ │
│                        │    - Current     │  │  • Response:     │ │
│                        │      step #      │  │    - Text for    │ │
│                        │    - Data so far │  │      next step   │ │
│                        │                  │  │    - Current     │ │
│                        │                  │  │      step #      │ │
│                        │                  │  │    - Data so far │ │
│                        └──────────────────┘  └──────────────────┘ │
│                                                                       │
│  Helper Functions:                                                 │
│  • validate_email()                                                │
│  • validate_phone()                                                │
│  • detect_order_intent() ✨                                        │
│  • detect_reservation_intent() ✨                                  │
│  • extract_order_items_from_message() ✨                           │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │           SQLAlchemy ORM Models                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│           │                    │              │                   │
│           ▼                    ▼              ▼                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Order Model     │  │ Reservation Model│  │ Conversation    │  │
│  │                  │  │                  │  │ Model           │  │
│  │ Fields:          │  │ Fields:          │  │                 │  │
│  │ • id             │  │ • id             │  │ Fields:         │  │
│  │ • customer_name  │  │ • customer_name  │  │ • id            │  │
│  │ • email          │  │ • email          │  │ • session_id    │  │
│  │ • phone          │  │ • phone          │  │ • user_message  │  │
│  │ • items (JSON)   │  │ • party_size     │  │ • bot_response  │  │
│  │ • total_price    │  │ • date           │  │ • message_type  │  │
│  │ • status         │  │ • time           │  │ • timestamp     │  │
│  │ • created_at     │  │ • status         │  │                 │  │
│  │                  │  │ • created_at     │  │ (for each turn) │  │
│  │                  │  │                  │  │                 │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
│           │                    │              │                   │
│           └────────────────────┴──────────────┘                   │
│                                  │                                 │
│                                  ▼                                 │
│                        SQLite Database                             │
│                      (restaurant.db)                              │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Message Flow Diagram

### Order Collection Flow
```
User Message: "I want to place an order"
        │
        ▼
Frontend detects "order" keyword
        │
        ├─► Set orderCollectionMode = true
        ├─► Set orderCollectionStep = 0
        ├─► Set orderCollectionData = {}
        │
        ▼
Display: "I'll help you place an order! Which items would you like?"
        │
        │ (User types next message)
        │
        ▼
User Message: "2 pizzas and a coke"
        │
        ▼
Frontend in orderCollectionMode = true
        │
        ├─► POST to /api/chat/order-intent
        │   └─► body: {message, session_id, step: 0, collected_data: {}}
        │
        ▼
Backend receives step 0 (collecting items)
        │
        ├─► Extract items from message
        ├─► Store: collected_data.items = [{Pizza...}, {Coke...}]
        ├─► Return response: "Great! I found Pizza, Coke. What's your name?"
        ├─► Return step: 1 (move to name collection)
        │
        ▼
Frontend receives response
        │
        ├─► Update orderCollectionStep = 1
        ├─► Update orderCollectionData = {items: [...]}
        ├─► Display bot response
        │
        │ (User types name)
        │
        ▼
User Message: "John Smith"
        │
        ▼
Backend receives step 1 (collecting name)
        │
        ├─► Store: collected_data.customer_name = "John Smith"
        ├─► Return response: "Thanks! What's your email address?"
        ├─► Return step: 2
        │
        ▼
[Continue through steps 2, 3, 4...]
        │
        ▼
Backend receives step 4 (special requests + confirm)
        │
        ├─► Store special requests
        ├─► CREATE Order in database
        ├─► INSERT Conversation entry
        ├─► Return response: "✅ Order #X Confirmed!"
        ├─► Return step: 0 (RESET - process complete)
        │
        ▼
Frontend receives step 0
        │
        ├─► Set orderCollectionMode = false
        ├─► Clear orderCollectionData
        ├─► Display confirmation
        ├─► Ready for normal chat again
```

### Reservation Collection Flow
```
Similar to above but with 7 steps:
Step 0: Collect Name
Step 1: Collect Email
Step 2: Collect Phone
Step 3: Collect Party Size
Step 4: Collect Date
Step 5: Collect Time
Step 6: Collect Special Requests + Create Reservation
Return Step 0 to reset mode
```

## State Management Lifecycle

```
┌─────────────────────────────────────────────────────┐
│           User Types Order-Related Message           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ sendChatMessage() called    │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Check orderCollectionMode  │
        │ (Initially false)          │
        └────────────┬───────────────┘
                     │ FALSE
                     ▼
        ┌────────────────────────────┐
        │ Check for order keywords   │
        │ (Finds: "order")           │
        └────────────┬───────────────┘
                     │ FOUND
                     ▼
        ┌────────────────────────────┐
        │ Set State:                 │
        │ • orderCollectionMode=true │
        │ • orderCollectionStep=0    │
        │ • orderCollectionData={}   │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Show initial prompt        │
        │ Return (don't call API)    │
        └─────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Next User Message Arrives  │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Check orderCollectionMode  │
        │ (Now true!)                │
        └────────────┬───────────────┘
                     │ TRUE
                     ▼
        ┌────────────────────────────────┐
        │ Fetch /api/chat/order-intent   │
        │ With:                          │
        │ • message                      │
        │ • session_id                   │
        │ • step: 0                      │
        │ • collected_data: {}           │
        └────────────┬────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │ Receive Response:              │
        │ {                              │
        │   response: "...",             │
        │   step: 1,                     │
        │   collected_data: {items...}   │
        │ }                              │
        └────────────┬────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Update State:              │
        │ • orderCollectionStep=1    │
        │ • orderCollectionData=...  │
        │ • Display bot response     │
        └─────────────────────────────┘
                     │
           [Repeat until step=0]
                     │
                     ▼
        ┌────────────────────────────┐
        │ Backend returns step: 0    │
        │ (Process complete)         │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Frontend Sets:             │
        │ • orderCollectionMode=false│
        │ • orderCollectionData={}   │
        │ (Back to normal chat)      │
        └─────────────────────────────┘
```

## Database Schema

```
Order Table:
┌────────┬──────────────┬───────┬───────┬──────────┬────────────┬────────┬────────────┐
│ id     │ customer_name│ email │ phone │ items    │ special_req│ total_ │ status     │
│ (PK)   │ (STR)        │ (STR) │ (STR) │ (JSON)   │ (STR)      │ price  │ (STR)      │
├────────┼──────────────┼───────┼───────┼──────────┼────────────┼────────┼────────────┤
│ 1      │ John Smith   │ j@... │ 555.. │ [{pizza},│ Extra      │ 45.99  │ confirmed  │
│        │              │       │       │  {coke}] │ cheese     │        │            │
└────────┴──────────────┴───────┴───────┴──────────┴────────────┴────────┴────────────┘

Reservation Table:
┌────────┬──────────────┬───────┬───────┬────────────┬──────────┬────────┬────────┐
│ id     │ customer_name│ email │ phone │ party_size │ date     │ time   │ status │
│ (PK)   │ (STR)        │ (STR) │ (STR) │ (INT)      │ (DATE)   │ (STR)  │ (STR)  │
├────────┼──────────────┼───────┼───────┼────────────┼──────────┼────────┼────────┤
│ 1      │ Sarah J.     │ s@... │ 555.. │ 4          │ 2024-12-25│ 19:30  │ confirm│
└────────┴──────────────┴───────┴───────┴────────────┴──────────┴────────┴────────┘

Conversation Table:
┌────────┬────────────┬───────────────┬────────────┬──────────────┬─────────────┐
│ id     │ session_id │ user_message  │ bot_respons│ message_type │ timestamp   │
│ (PK)   │ (STR)      │ (STR)         │ (STR)      │ (STR)        │ (DATETIME)  │
├────────┼────────────┼───────────────┼────────────┼──────────────┼─────────────┤
│ 1      │ session_.. │ "I want order"│ "I'll help"│ "order"      │ 2024-...    │
│ 2      │ session_.. │ "2 pizzas"    │ "Great! I  │ "order"      │ 2024-...    │
│ 3      │ session_.. │ "John"        │ "Thanks!.."│ "order"      │ 2024-...    │
└────────┴────────────┴───────────────┴────────────┴──────────────┴─────────────┘
```

## Keywords Detection

```
Order Keywords Trigger:
├─ "order"
├─ "place an order"
├─ "i want"
├─ "can i have"
├─ "give me"
├─ "get me"
├─ "buy"
└─ "purchase"

Reservation Keywords Trigger:
├─ "reservation"
├─ "reserve"
├─ "book"
├─ "table"
├─ "booking"
├─ "dinner reservation"
└─ "lunch reservation"
```

---

**✨ NEW FEATURES** - Marked with ✨
