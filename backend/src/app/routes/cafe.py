import re
import uuid
import logging
from fastapi import APIRouter
from app.routes.schemas import CustomerCredentials, ChatRequest, ChatResponse
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["cafe & food ordering"])

# In-memory customer data and sessions
customer_data = {}
active_sessions = {}

# Menu data
menu_items = [
    {
        "category": "Burger",
        "items": [
            {"name": "Cheese Burger", "price": 17},
            {"name": "Spicy Jalape?o", "price": 20},
            {"name": "Smoky BBQ", "price": 19},
            {"name": "Non-Cheese Burger", "price": 16},
            {"name": "Garlic Mushroom", "price": 19},
            {"name": "Avocado Ranch", "price": 20},
            {"name": "Chicken Burger", "price": 18},
            {"name": "Buffalo Heat", "price": 20},
            {"name": "Honey Mustard Glaze", "price": 20},
            {"name": "Beef Burger", "price": 19},
            {"name": "Bacon Jam Bliss", "price": 20},
            {"name": "Truffle Deluxe", "price": 20}
        ]
    },
    {
        "category": "Fries",
        "items": [
            {"name": "Large Fries", "price": 13},
            {"name": "Medium Fries", "price": 11},
            {"name": "Regular Fries", "price": 9}
        ]
    },
    {
        "category": "Drinks",
        "items": [
            {"name": "Large Drink", "price": 11},
            {"name": "Medium Drink", "price": 9},
            {"name": "Regular Drink", "price": 7}
        ]
    }
]

def find_item_in_menu(item_name: str):
    for category in menu_items:
        for item in category["items"]:
            if item_name.lower() in item["name"].lower():
                return item
    return None

def generate_receipt(session_id: str) -> str:
    session = active_sessions.get(session_id)
    if not session or not session.get("cart"):
        return "Cart is empty. Cannot generate receipt."

    customer_name = session.get("customer_name", "Guest")
    customer_phone = session.get("customer_phone", "Unknown")
    cart = session["cart"]

    total = sum(item["price"] * item["quantity"] for item in cart)
    order_id = str(uuid.uuid4())[:8]

    receipt_lines = [
        f"?? Receipt for {customer_name} ({customer_phone}):",
        f"Order ID: {order_id}",
        "-" * 30
    ]
    for item in cart:
        line = f"{item['name']} x{item['quantity']} = ${item['price'] * item['quantity']}"
        receipt_lines.append(line)
    receipt_lines.append("-" * 30)
    receipt_lines.append(f"Total: ${total}")
    return "\n".join(receipt_lines)

@router.get("/menu")
@router.get("/api/menu")
def get_menu():
    return {"menu": menu_items}

@router.post("/upload-menu")
@router.post("/api/upload-menu")
def upload_menu():
    return {"status": "Menu synchronized successfully"}

@router.post("/register")
@router.post("/api/register")
def register_customer(credentials: CustomerCredentials):
    session_id = credentials.session_id
    customer_name = credentials.customer_name
    customer_phone = credentials.customer_phone
    
    if customer_name not in customer_data:
        customer_data[customer_name] = {
            "phone": customer_phone,
            "order_history": []
        }
    
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "cart": []
        }
    else:
        active_sessions[session_id]["customer_name"] = customer_name
        active_sessions[session_id]["customer_phone"] = customer_phone
    
    return {
        "success": True,
        "message": f"Welcome, {customer_name}! How can I help you today?"
    }

@router.post("/chat", response_model=ChatResponse)
@router.post("/cafe/chat", response_model=ChatResponse)
def cafe_chat(request: ChatRequest):
    session_id = request.session_id
    message = request.message.lower().strip()
    
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "customer_name": "Guest",
            "customer_phone": "Unknown",
            "cart": []
        }
    
    session = active_sessions[session_id]
    customer_name = session.get("customer_name", "Guest")
    response_text = ""
    has_receipt = False
    
    if (any(word in message for word in ["checkout", "receipt", "bill", "done", "finish", "complete", "pay"]) or
        re.search(r'\b(no|nope|that\'s all|that is all|that\'s it|that is it)\b', message)):
        
        if not session.get("cart", []):
            response_text = "Your cart is empty! Please order something first."
        else:
            receipt = generate_receipt(session_id)
            if receipt:
                response_text = receipt
                session["last_receipt_generated"] = True
                has_receipt = True
            else:
                response_text = "I couldn't generate a receipt. Please try again."
    
    elif any(word in message for word in ["order", "want", "get", "have", "burger", "fries", "drink"]):
        if "cart" not in session:
            session["cart"] = []
        
        session["last_receipt_generated"] = False
        parts = re.split(r'\s+and\s+|\s*,\s*', message)
        parts = [part.strip() for part in parts if part.strip()]
        items_found = False
        
        for part in parts:
            quantity = 1
            match_qty = re.match(r"(\d+)\s+(.*)", part)
            if match_qty:
                quantity = int(match_qty.group(1))
                part = match_qty.group(2)
            
            match_x = re.match(r"(.*)\s*[xX?]\s*(\d+)", part)
            if match_x:
                part = match_x.group(1).strip()
                quantity = int(match_x.group(2))
            
            matched_item = find_item_in_menu(part)
            if matched_item:
                found = False
                for cart_item in session["cart"]:
                    if cart_item["name"] == matched_item["name"]:
                        cart_item["quantity"] += quantity
                        found = True
                        break
                if not found:
                    session["cart"].append({
                        "name": matched_item["name"],
                        "price": matched_item["price"],
                        "quantity": quantity
                    })
                items_found = True
        
        if items_found:
            response_text = "Items added to your cart! Would you like anything else?"
        else:
            response_text = "I couldn't recognize any menu items in your request."
    
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = f"""
            You are CafeBot for {settings.company_name}. Current Menu: {menu_items}
            Customer: {customer_name} says: {message}
            Current cart: {session.get("cart", [])}
            Respond briefly about menu or ordering.
            """
            resp = model.generate_content(prompt)
            response_text = resp.text if resp.text else "How may I help you with your order?"
        except Exception:
            response_text = "Welcome to Fireball Cafe! You can browse the menu, add items to your cart, or switch to Table Booking."
            
    return ChatResponse(
        reply=response_text,
        cart_items=session.get("cart", []),
        has_receipt=has_receipt
    )

@router.get("/cart/{session_id}")
@router.get("/api/cart/{session_id}")
def get_cart(session_id: str):
    if session_id not in active_sessions:
        return {"cart": [], "customer_name": "Guest"}
    session = active_sessions[session_id]
    return {
        "cart": session.get("cart", []),
        "customer_name": session.get("customer_name", "Guest")
    }

@router.post("/clear-cart/{session_id}")
@router.post("/api/clear-cart/{session_id}")
def clear_cart(session_id: str):
    if session_id in active_sessions:
        active_sessions[session_id]["cart"] = []
        return {"success": True, "message": "Cart cleared successfully"}
    return {"success": False, "message": "Session not found"}
