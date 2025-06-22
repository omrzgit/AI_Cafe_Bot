from pymongo import MongoClient

uri = "mongodb+srv://alikamalmustafanaqvi:QHA5jJnkPWxlFeq0@cluster0.sxy5hio.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.server_info()  # Trigger server selection
    print("✅ Connected successfully to MongoDB Atlas!")
except Exception as e:
    print("❌ Connection failed:")
    print(e)
