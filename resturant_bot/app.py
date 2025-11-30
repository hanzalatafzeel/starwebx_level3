
import os
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Tuple

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import google.generativeai as genai
from dotenv import load_dotenv
import jwt

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///restaurant.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Initialize extensions
db = SQLAlchemy(app)
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('CORS_ORIGINS', '*').split(',') if os.getenv('CORS_ORIGINS') else '*',
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    }
})

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', None)
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Order(db.Model):
    """Order model for tracking customer orders"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120))
    customer_phone = db.Column(db.String(20))
    items = db.Column(db.Text, nullable=False)  # JSON string
    special_requests = db.Column(db.Text)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, preparing, ready, delivered
    session_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'items': json.loads(self.items),
            'special_requests': self.special_requests,
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Reservation(db.Model):
    """Reservation model for table bookings"""
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    party_size = db.Column(db.Integer, nullable=False)
    reservation_date = db.Column(db.Date, nullable=False)
    reservation_time = db.Column(db.String(5), nullable=False)  # HH:MM format
    special_requests = db.Column(db.Text)
    status = db.Column(db.String(50), default='confirmed')  # confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'email': self.email,
            'phone': self.phone,
            'party_size': self.party_size,
            'reservation_date': self.reservation_date.isoformat(),
            'reservation_time': self.reservation_time,
            'special_requests': self.special_requests,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class Conversation(db.Model):
    """Conversation history model"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50))  # text, order, reservation, recommendation
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'bot_response': self.bot_response,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat()
        }


class UserSession(db.Model):
    """Session tracking for analytics"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    total_messages = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'started_at': self.started_at.isoformat(),
            'total_messages': self.total_messages
        }


# ============================================================================
# RESTAURANT DATA & SYSTEM PROMPT
# ============================================================================

RESTAURANT_CONFIG = {
    'name': 'Taste Haven',
    'location': '123 Food Street, Downtown',
    'phone': '(555) 123-4567',
    'email': 'info@tastehaven.com',
    'website': 'www.tastehaven.com',
    'hours': {
        'monday_thursday': '11:00 AM - 10:00 PM',
        'friday_saturday': '11:00 AM - 11:00 PM',
        'sunday': '10:00 AM - 9:00 PM'
    },
    'menu': {
        'appetizers': [
            {'id': 'app_1', 'name': 'Spring Rolls', 'price': 8.99, 'description': 'Crispy spring rolls with sweet chili dipping sauce', 'vegetarian': True, 'vegan': True},
            {'id': 'app_2', 'name': 'Bruschetta', 'price': 9.99, 'description': 'Toasted bread with fresh tomato, basil, and garlic', 'vegetarian': True, 'vegan': False},
            {'id': 'app_3', 'name': 'Calamari', 'price': 11.99, 'description': 'Fried squid rings with lemon and marinara sauce', 'vegetarian': False, 'vegan': False},
            {'id': 'app_4', 'name': 'Garlic Bread', 'price': 6.99, 'description': 'Crispy garlic bread with herb butter', 'vegetarian': True, 'vegan': False},
            {'id': 'app_5', 'name': 'Hummus Platter', 'price': 10.99, 'description': 'Assorted hummus with pita bread and vegetables', 'vegetarian': True, 'vegan': True}
        ],
        'main_courses': [
            {'id': 'main_1', 'name': 'Grilled Salmon', 'price': 24.99, 'description': 'Fresh Atlantic salmon with seasonal vegetables and lemon butter sauce', 'vegetarian': False, 'vegan': False, 'spicy': False},
            {'id': 'main_2', 'name': 'Vegetable Risotto', 'price': 18.99, 'description': 'Creamy arborio rice with seasonal vegetables, peas, and parmesan', 'vegetarian': True, 'vegan': False, 'spicy': False},
            {'id': 'main_3', 'name': 'Ribeye Steak', 'price': 32.99, 'description': 'Premium 16oz ribeye with garlic mashed potatoes and grilled asparagus', 'vegetarian': False, 'vegan': False, 'spicy': False},
            {'id': 'main_4', 'name': 'Vegetable Pasta', 'price': 17.99, 'description': 'Fresh pappardelle with seasonal vegetables and light tomato sauce', 'vegetarian': True, 'vegan': True, 'spicy': False},
            {'id': 'main_5', 'name': 'Chicken Parmesan', 'price': 21.99, 'description': 'Crispy chicken breast with marinara sauce and melted mozzarella', 'vegetarian': False, 'vegan': False, 'spicy': False},
            {'id': 'main_6', 'name': 'Spicy Thai Curry', 'price': 19.99, 'description': 'Coconut curry with chicken, vegetables, and jasmine rice', 'vegetarian': False, 'vegan': False, 'spicy': True}
        ],
        'desserts': [
            {'id': 'des_1', 'name': 'Tiramisu', 'price': 8.99, 'description': 'Classic Italian layered dessert with mascarpone and espresso', 'vegetarian': True, 'vegan': False},
            {'id': 'des_2', 'name': 'Cheesecake', 'price': 9.99, 'description': 'New York style cheesecake with berry compote', 'vegetarian': True, 'vegan': False},
            {'id': 'des_3', 'name': 'Chocolate Mousse', 'price': 7.99, 'description': 'Rich and fluffy dark chocolate mousse', 'vegetarian': True, 'vegan': True},
            {'id': 'des_4', 'name': 'Panna Cotta', 'price': 8.99, 'description': 'Silky Italian cream dessert with fresh fruit', 'vegetarian': True, 'vegan': False},
            {'id': 'des_5', 'name': 'Sorbet Trio', 'price': 8.99, 'description': 'Three flavors of refreshing homemade sorbet', 'vegetarian': True, 'vegan': True}
        ],
        'beverages': [
            {'id': 'bev_1', 'name': 'Soft Drinks', 'price': 3.50, 'description': 'Coke, Sprite, Fanta, Iced Tea'},
            {'id': 'bev_2', 'name': 'Coffee', 'price': 4.50, 'description': 'Espresso, Cappuccino, Latte, Americano'},
            {'id': 'bev_3', 'name': 'Wine Selection', 'price': 8.00, 'description': 'Red, White, and Rosé wines'},
            {'id': 'bev_4', 'name': 'Beer', 'price': 5.50, 'description': 'Domestic and imported craft beers'},
            {'id': 'bev_5', 'name': 'Cocktails', 'price': 9.99, 'description': 'House special cocktails and classics'}
        ]
    }
}

SYSTEM_PROMPT = f"""You are a professional AI assistant for {RESTAURANT_CONFIG['name']}, a fine dining restaurant.

RESTAURANT DETAILS:
- Name: {RESTAURANT_CONFIG['name']}
- Location: {RESTAURANT_CONFIG['location']}
- Phone: {RESTAURANT_CONFIG['phone']}
- Email: {RESTAURANT_CONFIG['email']}
- Website: {RESTAURANT_CONFIG['website']}

HOURS OF OPERATION:
- Monday to Thursday: {RESTAURANT_CONFIG['hours']['monday_thursday']}
- Friday to Saturday: {RESTAURANT_CONFIG['hours']['friday_saturday']}
- Sunday: {RESTAURANT_CONFIG['hours']['sunday']}

MENU CATEGORIES:

APPETIZERS:
"""

for item in RESTAURANT_CONFIG['menu']['appetizers']:
    dietary = []
    if item.get('vegan'): dietary.append('Vegan')
    elif item.get('vegetarian'): dietary.append('Vegetarian')
    dietary_str = f" ({', '.join(dietary)})" if dietary else ""
    SYSTEM_PROMPT += f"- {item['name']} (${item['price']:.2f}){dietary_str}: {item['description']}\n"

SYSTEM_PROMPT += "\nMAIN COURSES:\n"
for item in RESTAURANT_CONFIG['menu']['main_courses']:
    dietary = []
    if item.get('vegan'): dietary.append('Vegan')
    elif item.get('vegetarian'): dietary.append('Vegetarian')
    if item.get('spicy'): dietary.append('Spicy')
    dietary_str = f" ({', '.join(dietary)})" if dietary else ""
    SYSTEM_PROMPT += f"- {item['name']} (${item['price']:.2f}){dietary_str}: {item['description']}\n"

SYSTEM_PROMPT += "\nDESSERTS:\n"
for item in RESTAURANT_CONFIG['menu']['desserts']:
    dietary = []
    if item.get('vegan'): dietary.append('Vegan')
    elif item.get('vegetarian'): dietary.append('Vegetarian')
    dietary_str = f" ({', '.join(dietary)})" if dietary else ""
    SYSTEM_PROMPT += f"- {item['name']} (${item['price']:.2f}){dietary_str}: {item['description']}\n"

SYSTEM_PROMPT += "\nBEVERAGES:\n"
for item in RESTAURANT_CONFIG['menu']['beverages']:
    SYSTEM_PROMPT += f"- {item['name']} (${item['price']:.2f}): {item['description']}\n"

SYSTEM_PROMPT += f"""

YOUR RESPONSIBILITIES:
1. Provide friendly, natural conversation with customers
2. Answer questions about menu items, ingredients, and preparation
3. Suggest personalized menu recommendations based on preferences and dietary restrictions
4. Assist with order placement (confirm items, quantities, special requests)
5. Help with table reservations (collect name, party size, date, time, preferences)
6. Provide restaurant information (hours, location, contact details)
7. Handle dietary restrictions and allergies carefully
8. Be professional yet warm and welcoming

INTERACTION GUIDELINES:
- Keep responses concise and conversational (2-3 sentences typically)
- Use occasional emojis for warmth 😊
- When customers show interest in ordering, summarize items before final confirmation
- For reservations, collect: name, party size, date, time, and any special requests
- Always highlight dietary options (vegan, vegetarian) when relevant
- If uncertain about menu details, acknowledge and suggest calling the restaurant
- Be helpful about accommodating special needs and preferences

RESPONSE STYLE:
- Warm and professional
- Helpful and informative
- Conversational and engaging
- Respectful of dietary choices
"""

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Basic phone validation"""
    import re
    pattern = r'^[\d\s\-\+\(\)]{10,}$'
    return re.match(pattern, phone) is not None


def get_client_ip() -> str:
    """Get client IP address"""
    if request.environ.get('HTTP_CF_CONNECTING_IP'):
        return request.environ['HTTP_CF_CONNECTING_IP']
    return request.remote_addr


def track_session(session_id: str, message_count: int = 1):
    """Track user session"""
    try:
        session_record = UserSession.query.filter_by(session_id=session_id).first()
        if session_record:
            session_record.last_activity = datetime.utcnow()
            session_record.total_messages += message_count
        else:
            session_record = UserSession(
                session_id=session_id,
                user_agent=request.headers.get('User-Agent', ''),
                ip_address=get_client_ip(),
                total_messages=message_count
            )
            db.session.add(session_record)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error tracking session: {e}")


def detect_order_intent(message: str) -> bool:
    """Detect if user wants to place an order"""
    order_keywords = ['order', 'place an order', 'i want', 'can i have', 'give me', 'get me', 'buy', 'purchase']
    return any(keyword in message.lower() for keyword in order_keywords)


def detect_reservation_intent(message: str) -> bool:
    """Detect if user wants to make a reservation"""
    reservation_keywords = ['reservation', 'reserve', 'book', 'table', 'booking', 'dinner reservation', 'lunch reservation']
    return any(keyword in message.lower() for keyword in reservation_keywords)


def extract_order_items_from_message(message: str) -> List[Dict]:
    """Extract menu items mentioned in user message"""
    items = []
    menu_flat = []
    
    # Flatten all menu items
    for category, category_items in RESTAURANT_CONFIG['menu'].items():
        if isinstance(category_items, list):
            menu_flat.extend(category_items)
    
    # Check which items are mentioned
    message_lower = message.lower()
    for item in menu_flat:
        if item['name'].lower() in message_lower:
            items.append({
                'id': item['id'],
                'name': item['name'],
                'price': item['price'],
                'quantity': 1
            })
    
    return items


def process_order_intent_step(message: str, session_id: str = 'anonymous', step: int = 0, collected_data: Optional[Dict] = None) -> Dict:
    """Process a single step of the order multi-step flow"""
    if collected_data is None:
        collected_data = {}

    response_text = ""
    next_step = step

    try:
        if step == 0:  # Collect items
            items = extract_order_items_from_message(message)
            if items:
                collected_data['items'] = items
                items_str = ', '.join([item['name'] for item in items])
                response_text = f"Great! I found {items_str} in your message. What's your name?"
                next_step = 1
            else:
                response_text = "I didn't find any menu items in your message. Could you please specify which items you'd like to order?"
                next_step = 0

        elif step == 1:  # Collect name
            collected_data['customer_name'] = message
            response_text = "Thanks! What's your email address?"
            next_step = 2

        elif step == 2:  # Collect email
            if not validate_email(message):
                response_text = "That doesn't look like a valid email. Please try again."
                next_step = 2
            else:
                collected_data['customer_email'] = message
                response_text = "Great! What's your phone number?"
                next_step = 3

        elif step == 3:  # Collect phone
            if not validate_phone(message):
                response_text = "That doesn't look like a valid phone number. Please try again."
                next_step = 3
            else:
                collected_data['customer_phone'] = message
                items_summary = ', '.join([f"{item['quantity']}x {item['name']}" for item in collected_data.get('items', [])])
                total = sum(item['price'] * item['quantity'] for item in collected_data.get('items', []))
                response_text = f"Perfect! Here's your order summary:\n{items_summary}\nTotal: ${total:.2f}\n\nAny special requests? (or just say 'no')"
                next_step = 4

        elif step == 4:  # Collect special requests and confirm
            if message.lower() not in ['no', 'none', 'skip']:
                collected_data['special_requests'] = message
            else:
                collected_data['special_requests'] = ''

            # Create the order
            total_price = sum(item['price'] * item['quantity'] for item in collected_data.get('items', []))
            order = Order(
                customer_name=collected_data['customer_name'],
                customer_email=collected_data.get('customer_email', ''),
                customer_phone=collected_data.get('customer_phone', ''),
                items=json.dumps(collected_data['items']),
                special_requests=collected_data.get('special_requests', ''),
                total_price=total_price,
                status='confirmed',
                session_id=session_id
            )

            db.session.add(order)
            db.session.commit()

            response_text = f"✅ Order #{order.id} Confirmed!\nTotal: ${total_price:.2f}\nThank you for your order!"
            next_step = 0  # reset

        # Store conversation
        conversation = Conversation(
            session_id=session_id,
            user_message=message,
            bot_response=response_text,
            message_type='order'
        )
        db.session.add(conversation)
        db.session.commit()

        return {
            'success': True,
            'response': response_text,
            'step': next_step,
            'collected_data': collected_data,
            'session_id': session_id
        }
    except Exception as e:
        logger.error(f"Order intent error: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': 'Failed to process order'
        }


def process_reservation_intent_step(message: str, session_id: str = 'anonymous', step: int = 0, collected_data: Optional[Dict] = None) -> Dict:
    """Process a single step of the reservation multi-step flow"""
    if collected_data is None:
        collected_data = {}

    response_text = ""
    next_step = step

    try:
        if step == 0:  # Collect name
            collected_data['customer_name'] = message
            response_text = "What's your email address?"
            next_step = 1

        elif step == 1:  # Collect email
            if not validate_email(message):
                response_text = "That doesn't look like a valid email. Please try again."
                next_step = 1
            else:
                collected_data['email'] = message
                response_text = "What's your phone number?"
                next_step = 2

        elif step == 2:  # Collect phone
            if not validate_phone(message):
                response_text = "That doesn't look like a valid phone number. Please try again."
                next_step = 2
            else:
                collected_data['phone'] = message
                response_text = "How many people in your party? (1-20)"
                next_step = 3

        elif step == 3:  # Collect party size
            try:
                party_size = int(message)
                if 1 <= party_size <= 20:
                    collected_data['party_size'] = party_size
                    response_text = "What date would you like? (YYYY-MM-DD)"
                    next_step = 4
                else:
                    response_text = "Party size must be between 1 and 20. Please try again."
                    next_step = 3
            except ValueError:
                response_text = "Please enter a valid number."
                next_step = 3

        elif step == 4:  # Collect date
            try:
                res_date = datetime.strptime(message, '%Y-%m-%d').date()
                if res_date >= datetime.now().date():
                    collected_data['date'] = message
                    response_text = "What time would you like? (HH:MM, e.g., 19:30)"
                    next_step = 5
                else:
                    response_text = "The date must be in the future. Please try again."
                    next_step = 4
            except ValueError:
                response_text = "Please enter a valid date (YYYY-MM-DD format)."
                next_step = 4

        elif step == 5:  # Collect time
            if len(message) == 5 and message[2] == ':':
                try:
                    hours, minutes = map(int, message.split(':'))
                    if 0 <= hours < 24 and 0 <= minutes < 60:
                        collected_data['time'] = message
                        response_text = f"Perfect! Let me confirm:\nName: {collected_data['customer_name']}\nParty size: {collected_data['party_size']}\nDate: {collected_data['date']}\nTime: {collected_data['time']}\nAny special requests? (or say 'no')"
                        next_step = 6
                    else:
                        response_text = "Please enter a valid time (00:00 - 23:59)."
                        next_step = 5
                except ValueError:
                    response_text = "Please enter a valid time (HH:MM format)."
                    next_step = 5
            else:
                response_text = "Please enter time in HH:MM format."
                next_step = 5

        elif step == 6:  # Collect special requests and confirm
            if message.lower() not in ['no', 'none', 'skip']:
                collected_data['special_requests'] = message
            else:
                collected_data['special_requests'] = ''

            # Create the reservation
            reservation = Reservation(
                customer_name=collected_data['customer_name'],
                email=collected_data['email'],
                phone=collected_data['phone'],
                party_size=collected_data['party_size'],
                reservation_date=datetime.strptime(collected_data['date'], '%Y-%m-%d').date(),
                reservation_time=collected_data['time'],
                special_requests=collected_data.get('special_requests', ''),
                status='confirmed'
            )

            db.session.add(reservation)
            db.session.commit()

            response_text = f"✅ Reservation #{reservation.id} Confirmed!\nTable for {collected_data['party_size']} on {collected_data['date']} at {collected_data['time']}\nThank you!"
            next_step = 0

        # Store conversation
        conversation = Conversation(
            session_id=session_id,
            user_message=message,
            bot_response=response_text,
            message_type='reservation'
        )
        db.session.add(conversation)
        db.session.commit()

        return {
            'success': True,
            'response': response_text,
            'step': next_step,
            'collected_data': collected_data,
            'session_id': session_id
        }
    except Exception as e:
        logger.error(f"Reservation intent error: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': 'Failed to process reservation'
        }


# ============================================================================
# API ROUTES
# ============================================================================


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Restaurant Assistant Bot',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0'
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get restaurant configuration"""
    return jsonify({
        'restaurant': {
            'name': RESTAURANT_CONFIG['name'],
            'location': RESTAURANT_CONFIG['location'],
            'phone': RESTAURANT_CONFIG['phone'],
            'email': RESTAURANT_CONFIG['email'],
            'website': RESTAURANT_CONFIG['website'],
            'hours': RESTAURANT_CONFIG['hours']
        }
    })


@app.route('/api/menu', methods=['GET'])
@limiter.limit("30 per minute")
def get_menu():
    """Get full restaurant menu"""
    return jsonify({
        'success': True,
        'menu': RESTAURANT_CONFIG['menu']
    })


@app.route('/api/menu/<category>', methods=['GET'])
@limiter.limit("30 per minute")
def get_menu_category(category: str):
    """Get specific menu category"""
    if category not in RESTAURANT_CONFIG['menu']:
        return jsonify({'error': f'Category "{category}" not found'}), 404
    
    return jsonify({
        'success': True,
        'category': category,
        'items': RESTAURANT_CONFIG['menu'][category]
    })


@app.route('/api/chat', methods=['POST'])
@limiter.limit("30 per minute")
def chat():
    """Main chat endpoint for AI conversations, also handles order/reservation intent flows."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'anonymous')

        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        if len(user_message) > 1000:
            return jsonify({'error': 'Message too long (max 1000 characters)'}), 400

        # Track session
        track_session(session_id)

        # If client provided explicit step/collected_data for an intent flow, prefer that
        step = data.get('step', None)
        collected_data = data.get('collected_data', None)

        # If this message indicates ordering/reserving intent (or client is continuing a step), handle here
        if step is not None:
            # client explicitly continuing a flow: check type param if provided, default to order if both match
            intent_type = data.get('intent_type', None)  # 'order' or 'reservation'
            if intent_type == 'reservation':
                result = process_reservation_intent_step(user_message, session_id=session_id, step=step, collected_data=collected_data)
                return jsonify(result)
            else:
                # default to order processing
                result = process_order_intent_step(user_message, session_id=session_id, step=step, collected_data=collected_data)
                return jsonify(result)

        # Automatic intent detection from the message
        if detect_order_intent(user_message):
            # start order flow (step 0)
            result = process_order_intent_step(user_message, session_id=session_id, step=0, collected_data={})
            return jsonify(result)

        if detect_reservation_intent(user_message):
            # start reservation flow (step 0)
            result = process_reservation_intent_step(user_message, session_id=session_id, step=0, collected_data={})
            return jsonify(result)

        # Otherwise, proceed with Gemini as before (regular chat)
        history = Conversation.query.filter_by(session_id=session_id).order_by(
            Conversation.timestamp.desc()
        ).limit(5).all()

        context = "\n".join([
            f"User: {c.user_message}\nAssistant: {c.bot_response}"
            for c in reversed(history)
        ]) if history else ""

        full_prompt = f"{SYSTEM_PROMPT}\n"
        if context:
            full_prompt += f"\nPrevious conversation context:\n{context}\n"
        full_prompt += f"\nUser: {user_message}"

        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                top_k=40,
                top_p=0.9,
                max_output_tokens=300
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        )

        bot_message = response.text.strip()

        # Store conversation
        conversation = Conversation(
            session_id=session_id,
            user_message=user_message,
            bot_response=bot_message,
            message_type='text'
        )
        db.session.add(conversation)
        db.session.commit()

        return jsonify({
            'success': True,
            'response': bot_message,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process message'
        }), 500

@app.route('/api/orders', methods=['POST'])
@limiter.limit("10 per minute")
def create_order():
    """Create a new order"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        customer_name = data.get('customer_name', '').strip()
        customer_email = data.get('customer_email', '').strip()
        customer_phone = data.get('customer_phone', '').strip()
        items = data.get('items', [])
        special_requests = data.get('special_requests', '').strip()
        session_id = data.get('session_id', 'anonymous')
        
        if not customer_name:
            return jsonify({'error': 'Customer name is required'}), 400
        
        if not items or not isinstance(items, list):
            return jsonify({'error': 'Items must be a non-empty list'}), 400
        
        if customer_email and not validate_email(customer_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if customer_phone and not validate_phone(customer_phone):
            return jsonify({'error': 'Invalid phone format'}), 400
        
        # Calculate total
        total_price = sum(
            item.get('price', 0) * item.get('quantity', 1)
            for item in items
        )
        
        if total_price <= 0:
            return jsonify({'error': 'Order total must be greater than 0'}), 400
        
        # Create order
        order = Order(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            items=json.dumps(items),
            special_requests=special_requests,
            total_price=total_price,
            status='confirmed',
            session_id=session_id
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Log to conversation
        conversation = Conversation(
            session_id=session_id,
            user_message=f"Placed order for {', '.join([item.get('name', 'item') for item in items])}",
            bot_response=f"Order #{order.id} confirmed! Total: ${total_price:.2f}",
            message_type='order'
        )
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'total_price': total_price,
            'status': 'confirmed',
            'message': f'Order #{order.id} created successfully!'
        }), 201
    
    except Exception as e:
        logger.error(f"Order creation error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to create order'
        }), 500


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id: int):
    """Get order details"""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Order retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve order'}), 500


@app.route('/api/reservations', methods=['POST'])
@limiter.limit("10 per minute")
def create_reservation():
    """Create a table reservation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        customer_name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        party_size = data.get('party_size', 2)
        reservation_date = data.get('date', '').strip()
        reservation_time = data.get('time', '').strip()
        special_requests = data.get('special_requests', '').strip()
        
        # Validation
        if not all([customer_name, email, phone, reservation_date, reservation_time]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if not validate_phone(phone):
            return jsonify({'error': 'Invalid phone format'}), 400
        
        if not (1 <= party_size <= 20):
            return jsonify({'error': 'Party size must be between 1 and 20'}), 400
        
        # Parse date
        try:
            res_date = datetime.strptime(reservation_date, '%Y-%m-%d').date()
            if res_date < datetime.now().date():
                return jsonify({'error': 'Reservation date cannot be in the past'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
        
        # Create reservation
        reservation = Reservation(
            customer_name=customer_name,
            email=email,
            phone=phone,
            party_size=party_size,
            reservation_date=res_date,
            reservation_time=reservation_time,
            special_requests=special_requests,
            status='confirmed'
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'reservation_id': reservation.id,
            'confirmation': f'Table reserved for {customer_name} on {reservation_date} at {reservation_time}',
            'message': f'Reservation #{reservation.id} confirmed!'
        }), 201
    
    except Exception as e:
        logger.error(f"Reservation creation error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to create reservation'
        }), 500


@app.route('/api/reservations/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id: int):
    """Get reservation details"""
    try:
        reservation = Reservation.query.get(reservation_id)
        
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        
        return jsonify({
            'success': True,
            'reservation': reservation.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Reservation retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve reservation'}), 500


@app.route('/api/recommendations', methods=['POST'])
@limiter.limit("20 per minute")
def get_recommendations():
    """Get personalized menu recommendations using Gemini"""
    try:
        data = request.get_json()
        
        preferences = data.get('preferences', '').strip()
        dietary_restrictions = data.get('dietary_restrictions', [])
        budget = data.get('budget', 'no limit')
        session_id = data.get('session_id', 'anonymous')
        
        if not preferences:
            return jsonify({'error': 'Preferences are required'}), 400
        
        # Build recommendation prompt
        restrictions_text = ', '.join(dietary_restrictions) if dietary_restrictions else 'None'
        prompt = f"""Based on a customer's preferences and restrictions, recommend 3 dishes from our menu.

Customer Preferences: {preferences}
Dietary Restrictions: {restrictions_text}
Budget: {budget}

Provide your recommendations with brief reasons why they match the customer's preferences. Be warm and encouraging."""
        
        # Generate recommendations
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_k=40,
                top_p=0.9,
                max_output_tokens=400
            )
        )
        
        recommendations = response.text.strip()
        
        # Store in conversation history
        conversation = Conversation(
            session_id=session_id,
            user_message=f"Preferences: {preferences}, Restrictions: {restrictions_text}",
            bot_response=recommendations,
            message_type='recommendation'
        )
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate recommendations'
        }), 500


@app.route('/api/conversation/<session_id>', methods=['GET'])
@limiter.limit("20 per minute")
def get_conversation(session_id: str):
    """Get conversation history"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        
        if limit < 1 or limit > 100:
            limit = 10
        
        conversations = Conversation.query.filter_by(session_id=session_id).order_by(
            Conversation.timestamp.desc()
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'messages': [c.to_dict() for c in reversed(conversations)]
        })
    
    except Exception as e:
        logger.error(f"Conversation retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve conversation'}), 500


@app.route('/api/orders/confirm', methods=['POST'])
@limiter.limit("10 per minute")
def confirm_order_from_chat():
    """Confirm and create an order from chat conversation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        customer_name = data.get('customer_name', '').strip()
        customer_email = data.get('customer_email', '').strip()
        customer_phone = data.get('customer_phone', '').strip()
        items = data.get('items', [])
        special_requests = data.get('special_requests', '').strip()
        session_id = data.get('session_id', 'anonymous')
        
        # Validation
        if not customer_name:
            return jsonify({'error': 'Customer name is required'}), 400
        
        if not customer_email:
            return jsonify({'error': 'Customer email is required'}), 400
        
        if not customer_phone:
            return jsonify({'error': 'Customer phone is required'}), 400
        
        if not validate_email(customer_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if not validate_phone(customer_phone):
            return jsonify({'error': 'Invalid phone format'}), 400
        
        if not items or not isinstance(items, list):
            return jsonify({'error': 'Items must be a non-empty list'}), 400
        
        # Calculate total
        total_price = sum(
            item.get('price', 0) * item.get('quantity', 1)
            for item in items
        )
        
        if total_price <= 0:
            return jsonify({'error': 'Order total must be greater than 0'}), 400
        
        # Create order
        order = Order(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            items=json.dumps(items),
            special_requests=special_requests,
            total_price=total_price,
            status='confirmed',
            session_id=session_id
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Log to conversation
        items_str = ', '.join([f"{item.get('quantity', 1)}x {item.get('name', 'item')}" for item in items])
        conversation = Conversation(
            session_id=session_id,
            user_message=f"Order confirmed: {items_str}",
            bot_response=f"Order #{order.id} has been successfully placed! Your order total is ${total_price:.2f}. We'll prepare it right away!",
            message_type='order'
        )
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'total_price': total_price,
            'status': 'confirmed',
            'message': f'Order #{order.id} confirmed!',
            'confirmation_message': f"✅ Order #{order.id} Confirmed!\nTotal: ${total_price:.2f}\nThank you for your order!"
        }), 201
    
    except Exception as e:
        logger.error(f"Order confirmation error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to confirm order'
        }), 500


# ============================================================================
# CHAT INTENT API ENDPOINTS
# ============================================================================

@app.route('/api/chat/order-intent', methods=['POST'])
@limiter.limit("20 per minute")
def handle_order_intent():
    """Handle order collection through multi-step chat"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    message = data.get('message', '').strip()
    session_id = data.get('session_id', 'anonymous')
    step = data.get('step', 0)
    collected_data = data.get('collected_data', {})
    
    return jsonify(process_order_intent_step(message, session_id=session_id, step=step, collected_data=collected_data))


@app.route('/api/chat/reservation-intent', methods=['POST'])
@limiter.limit("20 per minute")
def handle_reservation_intent():
    """Handle reservation collection through multi-step chat"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    message = data.get('message', '').strip()
    session_id = data.get('session_id', 'anonymous')
    step = data.get('step', 0)
    collected_data = data.get('collected_data', {})
    
    return jsonify(process_reservation_intent_step(message, session_id=session_id, step=step, collected_data=collected_data))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


@app.before_request
def before_request():
    """Initialize database tables before first request"""
    db.create_all()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )