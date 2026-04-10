# AI Café Bot

Just a quick spin using flask, a simple python based AI assistant for café environments, answering menu queries, taking orders, and more.

---

### Features

* AI‐powered café conversations
* menu browsing, order simulation
* dmin features & analytics

---

### Project Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/omrzgit/AI_Cafe_Bot.git
   cd AI_Cafe_Bot
   ```

2. **Create a virtual environment & activate**

   ```bash
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

### Configuration

Create a `.env` file or set environment variables:

```
FLASK_ENV=development
FLASK_APP=app.py         # replace if different
SECRET_KEY=your_secret
API_KEY=your_api_key
```

---

### Usage

Run locally:

```bash
flask run
# or
python app.py
```

Visit `http://localhost:5000/` in your browser to interact with the app.

---

### Deployment (Render.com)

To deploy continuously via GitHub:

1. Create `requirements.txt`:

   ```bash
   pip freeze > requirements.txt
   ```

2. Ensure `app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))` is in your entry file.

3. On Render.com:

   * New → Web Service → Connect your GitHub repo
   * Set Build Command: `pip install -r requirements.txt`
   * Set Start Command: `python app.py` *(or `main.py`, whichever)*

---

### Tests

If tests exist:

```bash
pytest
```

---

### Project Structure

```
AI_Cafe_Bot/
├── app.py
├── requirements.txt
├── templates/
├── static/
└── README.md
```


### Authors

**Omer ([omrzgit](https://github.com/omrzgit))**
**Ali ([AKM-13](https://github.com/AKM-13))**
