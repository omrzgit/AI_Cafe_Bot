from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import uuid

# -------------------------------------
# ✅ In-memory storage for customer data and carts
customer_data = {}  # Stores name, phone number, and order history
active_sessions = {}  # Tracks active chat sessions

# -------------------------------------
# ✅ Gemini API setup
GEMINI_API_KEY = "AIzaSyBJLHz_lNhtScBXfQbfz0rHJbtXMM2COUg"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# -------------------------------------
# ✅ FastAPI app setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  ---------------------------------------
#  ✅ MongoDB setup 
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient("mongodb+srv://syedalikamal5:OlHOXx2YVNqHoYQX@ai-cafebot.cwfw1oc.mongodb.net/?retryWrites=true&w=majority&appName=AI-CAFEBOT")
db = client["AI-CAFEBOT"]
menu_collection = db["menu"]
orders_collection = db["orders"]

# -------------------------------------
# ✅ Menu data (local)
menu_items = [
    {
        "category": "Burger",
        "items": [
            {"name": "Cheese Burger", "price": 17},
            {"name": "Spicy Jalapeño", "price": 20},
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

# -------------------------------------
# ✅ Models
class CustomerCredentials(BaseModel):
    customer_name: str
    customer_phone: str
    session_id: str

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    cart_items: list = []
    has_receipt: bool = False

# -------------------------------------
# ✅ Helper: Search item in menu
def find_item_in_menu(item_name):
    for category in menu_items:
        for item in category["items"]:
            if item_name.lower() in item["name"].lower():
                return item
    return None

# -------------------------------------
# ✅ Helper: Generate receipt
def generate_receipt(session_id):
    session = active_sessions.get(session_id)
    if not session or not session.get("cart"):
        return "Cart is empty. Cannot generate receipt."

    customer_name = session.get("customer_name", "Guest")
    customer_phone = session.get("customer_phone", "Unknown")
    cart = session["cart"]

    total = sum(item["price"] * item["quantity"] for item in cart)
    order_id = str(uuid.uuid4())[:8]

    orders_collection.insert_one({
        "order_id": order_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": cart.copy(),
        "total": total
    })

    receipt_lines = [
        f"🧾 Receipt for {customer_name} ({customer_phone}):",
        f"Order ID: {order_id}",
        "-"*30
    ]
    for item in cart:
        line = f"{item['name']} x{item['quantity']} = ${item['price']*item['quantity']}"
        receipt_lines.append(line)
    receipt_lines.append("-"*30)
    receipt_lines.append(f"Total: ${total}")
    return "\n".join(receipt_lines)

# -------------------------------------
# ✅ Routes
@app.get("/")
def read_root():
    return {"message": "CafeBot Backend is running."}

@app.post("/upload-menu")
def upload_menu():
    menu_collection.delete_many({})  # Purana menu clear karein
    menu_collection.insert_many(menu_items)  # Naya menu insert karein
    return {"status": "Menu uploaded to MongoDB"}

@app.get("/menu")
def get_menu():
    data = list(menu_collection.find({}, {"_id": 0}))
    return {"menu": data}

@app.post("/register", response_model=dict)
def register_customer(credentials: CustomerCredentials):
    session_id = credentials.session_id
    customer_name = credentials.customer_name
    customer_phone = credentials.customer_phone
    
    print(f"\n==== New Customer Registration ====")
    print(f"Session ID: {session_id}")
    print(f"Name: {customer_name}")
    print(f"Phone: {customer_phone}")
    
    # Store customer data
    if customer_name not in customer_data:
        customer_data[customer_name] = {
            "phone": customer_phone,
            "order_history": []
        }
    
    # Initialize or update session
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

@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    import re
    
    session_id = request.session_id
    message = request.message.lower().strip()
    
    print(f"\n==== New Chat Request ====")
    print(f"Session ID: {session_id}")
    print(f"Message: '{message}'")
    
    # Check if session exists
    if session_id not in active_sessions:
        print(f"No active session found. Creating new session.")
        active_sessions[session_id] = {
            "customer_name": "Guest",
            "customer_phone": "Unknown",
            "cart": []
        }
    
    session = active_sessions[session_id]
    customer_name = session.get("customer_name", "Guest")
    print(f"Customer: {customer_name}")
    
    response_text = ""
    has_receipt = False
    
    # STEP 1: Check for checkout/completion intent FIRST
    if (any(word in message for word in ["checkout", "receipt", "bill", "done", "finish", "complete", "pay"]) or
        re.search(r'\b(no|nope|that\'s all|that is all|that\'s it|that is it)\b', message)):
        print("Checkout intent detected")
        
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
    
    # STEP 2: Handle order intent
    elif any(word in message for word in ["order", "want", "get", "have", "burger", "fries", "drink"]):
        print("Order intent detected")
        
        if "cart" not in session:
            session["cart"] = []
        
        session["last_receipt_generated"] = False  # Reset receipt flag
        
        parts = re.split(r'\s+and\s+|\s*,\s*', message)
        parts = [part.strip() for part in parts if part.strip()]
        print(f"Split into parts: {parts}")
        
        items_found = False
        
        for part in parts:
            print(f"Processing part: '{part}'")
            
            # Default quantity
            quantity = 1
            
            # Try "2 cheeseburgers"
            match_qty = re.match(r"(\d+)\s+(.*)", part)
            if match_qty:
                quantity = int(match_qty.group(1))
                part = match_qty.group(2)
            
            # Try "cheeseburger x2"
            match_x = re.match(r"(.*)\s*[xX×]\s*(\d+)", part)
            if match_x:
                part = match_x.group(1).strip()
                quantity = int(match_x.group(2))
            
            # Try to match item
            matched_item = find_item_in_menu(part)
            if matched_item:
                print(f"Matched item: {matched_item['name']} x{quantity}")
                # Check if item already in cart
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
            else:
                print(f"Item not matched: '{part}'")
        
        if items_found:
            response_text = "Items added to your cart! Would you like anything else?"
        else:
            response_text = "I couldn't recognize any menu items in your request."
    
    # STEP 3: Handle general AI responses
    else:
        print("Using AI response")
        
        # Check for common expressions that might indicate "no more items"
        if re.search(r'\b(no|nope|that\'s all|that is all|that\'s it|that is it)\b', message) and session.get("cart", []):
            print("Detected 'no more items' intent")
            receipt = generate_receipt(session_id)
            if receipt:
                response_text = "Great! Here's your receipt:\n\n" + receipt
                session["last_receipt_generated"] = True
                has_receipt = True
            else:
                response_text = "I couldn't generate a receipt. Please try again."
        else:
            prompt = f"""
            You are CafeBot. Current Menu: {menu_items}
            Customer: {customer_name} says: {message}
            Current cart: {session.get("cart", [])}
            Respond briefly about menu or ordering.
            If they ask about their order status, mention their cart items.
            If they seem to be trying to finish their order, suggest using words like "checkout" or "done".
            """
            response = model.generate_content(prompt)
            response_text = response.text if response.text else "How may I help you?"
            
            # If the cart has items and the user might be trying to finish their order
            if session.get("cart", []) and any(word in message.lower() for word in ["finish", "done", "complete", "that's all"]):
                response_text += "\n\nWould you like to checkout now? Please say 'checkout' or 'done' to complete your order."

    print(f"Final response: {response_text}")
    print(f"Current cart state: {session.get('cart', [])}\n")
    
    return {
        "response": response_text, 
        "cart_items": session.get("cart", []),
        "has_receipt": has_receipt
    }


@app.get("/cart/{session_id}")
def get_cart(session_id: str):
    if session_id not in active_sessions:
        return {"cart": [], "customer_name": "Guest"}
    
    session = active_sessions[session_id]
    return {
        "cart": session.get("cart", []),
        "customer_name": session.get("customer_name", "Guest")
    }

@app.post("/clear-cart/{session_id}")
def clear_cart(session_id: str):
    if session_id in active_sessions:
        active_sessions[session_id]["cart"] = []
        return {"success": True, "message": "Cart cleared successfully"}
    return {"success": False, "message": "Session not found"}