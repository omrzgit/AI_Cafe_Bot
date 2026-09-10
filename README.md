# AI Café & Appointment Booking Assistant 📅

An enterprise-grade, full-stack AI chatbot and appointment reservation platform combining **Next.js 15**, **FastAPI**, **LangGraph**, and **Google Calendar**. 

Customers can seamlessly browse the café menu, order food with real-time cart tracking and automated receipts, or interact with a conversational AI agent to book table reservations, coffee tastings, barista workshops, and catering consultations with automatic Google Calendar invites and Google Meet video links.

---

## Key Features

### 🍔 1. AI Café Ordering & Menu Browsing
* **Natural Language Ordering**: Order food items in plain English (e.g., *"I'd like 2 Cheese Burgers and large fries"*).
* **Automated Regex & Semantic Extraction**: Detects item names, variants, and quantities on the fly.
* **Live Interactive Cart**: Instant subtotal calculation and real-time cart management.
* **Instant Digital Receipts**: Formatted itemized receipt generation with unique Order IDs.
* **Full Café Menu API**: Endpoints for browsing items across categories (Burgers, Fries, Drinks).

### 📅 2. LangGraph-Powered Appointment & Table Booking
* **Multi-Turn State Machine**: Explicit conversational routing through LangGraph:
  $$\text{GREET} \longrightarrow \text{LIST\_SERVICES} \longrightarrow \text{SELECT\_SERVICE} \longrightarrow \text{COLLECT\_DETAILS} \longrightarrow \text{CONFIRM} \longrightarrow \text{BOOKED}$$
* **Smart Parameter Validation**: Enforces valid future dates (`YYYY-MM-DD`), 24-hour time slots (`HH:MM`), and email validation before transitioning to confirmation.
* **Session Memory & Expiry**: Persistent state per browser session in SQLite/PostgreSQL with automatic 24-hour expiration resets.
* **Conflict Prevention**: Real-time slot availability check preventing double-bookings.
* **Seeded Service Catalog**: Pre-configured services including:
  - **Table Reservation** (60 min)
  - **Coffee & Burger Tasting Experience** (45 min)
  - **Barista Masterclass & Brewing** (60 min)
  - **Event & Catering Consultation** (30 min)

### 🎥 3. Google Calendar & Google Meet Integration
* **Auto Event Creation**: Directly creates scheduled events on the business Google Calendar.
* **Google Meet Links**: Generates one-click video meeting links for virtual consultations and confirmations.
* **Calendar Sync & Cancellation**: Deleting or cancelling a booking removes the calendar event automatically.
* **OAuth2 Authentication Flow**: Built-in helper routes (`/auth/google` & `/auth/google/callback`) to easily obtain refresh tokens.

### 💻 4. Modern Dual-Mode Next.js 15 Frontend
* **Tabbed Experience**: Easily toggle between **🍔 Food & Drinks** and **📅 Table & Appointments**.
* **Interactive Service Badges**: Click any service card to initiate an automated booking flow.
* **Booking Confirmation Cards**: Visual confirmation display with Booking ID and Google Meet join button.
* **"My Bookings" Drawer**: Look up and cancel past reservations by customer email.

---

## 🏗️ Architecture & Tech Stack

```
AI_Cafe_Bot/
├── backend/
│   ├── src/
│   │   └── app/
│   │       ├── main.py                     # FastAPI entrypoint, lifespan, CORS, GZip
│   │       ├── config/
│   │       │   ├── settings.py             # Pydantic Settings (.env configuration)
│   │       │   ├── database.py             # Async SQLAlchemy engine & session factory
│   │       │   └── llm_client.py           # Multi-provider LLM client (Groq / Gemini)
│   │       ├── models/
│   │       │   ├── service.py              # Service ORM Model
│   │       │   ├── booking.py              # Booking ORM Model
│   │       │   └── session.py              # ChatSession ORM Model
│   │       ├── routes/
│   │       │   ├── chat.py                 # POST /api/chat (LangGraph flow)
│   │       │   ├── services_bookings.py    # CRUD for Services and Bookings
│   │       │   ├── cafe.py                 # Cafe menu, cart, ordering & receipts
│   │       │   └── schemas.py              # Pydantic schemas with validators
│   │       ├── services/
│   │       │   ├── ai/
│   │       │   │   ├── booking_graph.py    # Compiled LangGraph StateGraph
│   │       │   │   ├── graph_state.py      # TypedDict GraphState
│   │       │   │   ├── nodes.py            # LLM invoke, validation & finalization
│   │       │   │   ├── orchestrator.py     # Session manager & LangGraph runner
│   │       │   │   └── prompts.py          # State-specific prompt templates
│   │       │   ├── booking/
│   │       │   │   └── booking_service.py  # Booking logic & conflict checker
│   │       │   ├── services/
│   │       │   │   └── catalog_service.py  # Service catalog & auto-seeding
│   │       │   └── calendar/
│   │       │       └── google_calendar.py  # Google Calendar & Meet API client
│   │       ├── middleware/
│   │       │   └── logging_middleware.py   # Request logging with ms timing
│   │       └── utils/
│   │           └── date_utils.py           # Date & time parsing utilities
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── pages/
│   │   ├── index.js                        # Dual-mode Interactive Chat & Ordering UI
│   │   ├── _app.js
│   │   └── _document.js
│   ├── styles/
│   └── package.json
├── tests/
│   └── test_backend.py                     # Unit and integration tests
├── Backendd/                               # Backwards-compatible legacy entrypoint
│   └── main.py
└── README.md
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.10+** (Python 3.11, 3.12, or 3.13 recommended)
- **Node.js 18+** & **npm**

---

### 1. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in `backend/` or project root (copy from `backend/.env.example`):
   ```env
   # LLM API Keys
   GROQ_API_KEY=your_groq_api_key
   GEMINI_API_KEY=your_gemini_api_key
   LLM_MODEL=llama-3.3-70b-versatile

   # App Configuration
   COMPANY_NAME=Fireball Cafe & Bistro
   APP_NAME=Fireball Cafe & Reservations
   PORT=8000
   ENVIRONMENT=development
   FRONTEND_URL=http://localhost:3000

   # Database (Async SQLite by default)
   DATABASE_URL=sqlite+aiosqlite:///./appointments.db
   SYNC_DATABASE_URL=sqlite:///./appointments.db

   # Google Calendar (Optional)
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REFRESH_TOKEN=your_google_refresh_token
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
   GOOGLE_CALENDAR_ID=primary
   ```

5. **Start the Backend Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   # or from project root:
   python Backendd/main.py
   ```
   * The API documentation will be accessible at: `http://localhost:8000/docs`
   * Health status check: `http://localhost:8000/api/health`

---

### 2. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Configure Environment Variables**:
   Create `.env.local` in `frontend/`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start the Next.js development server**:
   ```bash
   npm run dev
   ```
   * Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🌐 Deploying to Vercel

This repository is pre-configured for zero-config deployment on **[Vercel](https://vercel.com)** supporting both the **Next.js Frontend** and the **Python FastAPI Serverless Backend**:

### Method 1 — Deploy via Vercel Dashboard (Recommended)

1. Push your changes to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new) and import your `AI_Cafe_Bot` repository.
3. Keep the Root Directory as `./` (the repository root contains [`vercel.json`](file:///D:/Omer/Installments/Related%20to%20.bat/LAB/AI%20Appointment%20Booking%20Chatbot/AI_Cafe_Bot/vercel.json)).
4. Under **Environment Variables**, add:
   - `GROQ_API_KEY` (or `GEMINI_API_KEY`)
   - `COMPANY_NAME` = `Fireball Cafe & Bistro`
   - `LLM_MODEL` = `llama-3.3-70b-versatile`
   - *(Optional)* `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
5. Click **Deploy**. Vercel will automatically build the Next.js frontend and deploy the Python Serverless APIs.

### Method 2 — Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

---

## 📅 Google Calendar & Meet Integration (Optional)

To enable automatic Google Calendar event creation and Google Meet link generation:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Google Calendar API** under *APIs & Services > Library*.
3. Configure **OAuth Consent Screen** (add your email as a Test User).
4. Create **OAuth 2.0 Client ID** (Web application), adding Authorized Redirect URI:
   `http://localhost:8000/auth/google/callback`
5. Place `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your `.env`.
6. Start the backend and visit: `http://localhost:8000/auth/google` in your browser.
7. Grant permissions and copy the returned `refresh_token` into your `.env` as `GOOGLE_REFRESH_TOKEN`.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend and LLM health check |
| `POST` | `/api/chat` | AI Appointment Booking chat endpoint (LangGraph) |
| `GET` | `/api/services` | List all active booking services |
| `POST` | `/api/services` | Create a new service (Admin) |
| `POST` | `/api/bookings` | Directly create an appointment booking |
| `GET` | `/api/bookings/{id}` | Get booking details by ID |
| `GET` | `/api/bookings?email=` | List all bookings for a given customer email |
| `DELETE` | `/api/bookings/{id}` | Cancel booking and remove Calendar event |
| `GET` | `/api/menu` | Retrieve café food and drink menu |
| `POST` | `/api/register` | Register customer credentials and session |
| `POST` | `/api/cafe/chat` | AI Café food ordering chat endpoint |
| `GET` | `/api/cart/{session_id}` | Retrieve customer shopping cart |
| `POST` | `/api/clear-cart/{session_id}` | Clear cart items |
| `GET` | `/auth/google` | Initiate Google OAuth2 authorization |
| `GET` | `/auth/google/callback` | OAuth2 callback to receive refresh token |

---

## 🧪 Testing

Run the automated test suite verifying date utilities, models, LangGraph validation nodes, and state transitions:

```bash
# Using pytest
pytest tests/test_backend.py -v

# Or run directly via Python
python tests/test_backend.py
```

---

## 👥 Authors & Acknowledgements

- **Omer ([@omrzgit](https://github.com/omrzgit))**
- **Ali ([@AKM-13](https://github.com/AKM-13))**
- Reference architecture inspired by **[AI-Appointment-Booking-assistant](https://github.com/Rajatkpaliwal/AI-Appointment-Booking-assistant)** (used with permission).
