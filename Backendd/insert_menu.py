from pymongo import MongoClient

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://alikamalmustafanaqvi:QHA5jJnkPWxlFeq0@cluster0.sxy5hio.mongodb.net/AI_CafeBot?retryWrites=true&w=majority&appName=Cluster0")
db = client["AI_CafeBot"]
menu_collection = db["menu"]

# Sample Menu Items
menu_items = [
    {"name": "Zinger Burger", "price": 450, "ingredients": ["chicken fillet", "lettuce", "mayo", "bun"]},
    {"name": "Cheese Fries", "price": 250, "ingredients": ["potatoes", "cheese sauce", "spices"]},
    {"name": "Club Sandwich", "price": 350, "ingredients": ["chicken", "egg", "mayo", "bread", "lettuce"]},
    {"name": "Pepsi (Can)", "price": 100, "ingredients": ["carbonated water", "sugar", "flavor"]},
    {"name": "Chicken Shawarma", "price": 300, "ingredients": ["chicken", "pita bread", "sauce", "veggies"]},
    {"name": "BBQ Pizza", "price": 650, "ingredients": ["bbq chicken", "cheese", "pizza dough", "sauce"]},
    {"name": "Grilled Chicken Wrap", "price": 400, "ingredients": ["grilled chicken", "tortilla", "veggies", "sauce"]},
]

# Clear old menu (optional)
menu_collection.delete_many({})

# Insert new menu
menu_collection.insert_many(menu_items)

print("✅ Menu inserted successfully into MongoDB.")
