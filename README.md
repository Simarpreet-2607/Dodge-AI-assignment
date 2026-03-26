# Graph-Based Data Modeling and Query System

A full-stack application that transforms relational business data into an interactive visual graph and allows users to query it using natural language.

---

## 🎨 Overview

This system bridges the gap between tabular data and intuitive exploration. 
It takes standard relational tables (Customers, Orders, Products, Deliveries, Invoices, Payments), maps them into an interconnected property graph, and leverages Large Language Models (LLM) to translate plain English questions into exact, grounded answers backed by live data.

### Key Features
- **Visual Graph Construction**: Automatically builds and renders a visual node/edge mapping of database entities using NetworkX and Cytoscape.js.
- **Natural Language SQL querying**: Powered by Groq (LLaMA-3.3-70B), transforming "Show me delayed orders" to proper analytical SQL.
- **Interactive Explore Mode**: Click any node to see rich metadata and directly inspect relationships.
- **Robust Guardrails**: The LLM pipeline blocks destructive SQL (DROP/DELETE) and rejects out-of-domain queries to prevent hallucinations.
- **Node Highlighting**: Asking a question highlights the corresponding entities in the visualization map.

---

## 🏗 Architecture

### Backend Stack
- **FastAPI** (Python) for ultra-fast async REST API.
- **Neon** (Serverless PostgreSQL) as the source of truth, interacted with via SQLAlchemy async engine.
- **NetworkX** to compute, build, and format graph structures efficiently.
- **Groq API** for low-latency LLaMA-based model routing.

### Frontend Stack
- **Next.js 14** (App Router) acting as the main dashboard wrapper.
- **Cytoscape.js** for interactive and smooth graph visualization using the Cola force-directed layout engine.
- **Vanilla CSS** with CSS Variables to provide a rich dark mode interface.

---

## 🗄️ Database Schema & Modeling

The schema models an e-commerce workflow. Seven normalized tables are represented:
1. `customers` → 2. `orders` → 3. `order_items` → 4. `products`
5. `deliveries` (linked to orders)
6. `invoices` (linked to deliveries)
7. `payments` (linked to invoices)

**Graph Mapping Strategy**:
- Each database row becomes a Node.
- Each foreign key relationship becomes an Edge (e.g., Customer `placed` Order, Order `shipped_as` Delivery).

---

## 🛡️ LLM Guardrails & Prompting Strategy

The querying pipeline operates via a multi-stage execution flow with strict guardrails:
1. **Domain Classification**: Evaluates if the natural language question relates to the allowed schema scope. If unrelated, returns `UNRELATED_QUERY`.
2. **SQL Generation**: Instructs the LLM using the explicit schema to output *only* `SELECT` based queries.
3. **Safety Evaluation**: Using Regex, the Python execution layer blocks keywords like `DROP`, `UPDATE`, `ALTER`, or statement stacking.
4. **Execution & Formatting**: The raw JSON output from PostgreSQL is piped back to the LLM to format it into human-readable text strictly anchored to the data context.

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 20+
- A [Neon](https://neon.tech/) PostgreSQL Database URL.
- A [Groq](https://console.groq.com/) API Key.

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Fill out environment variables:
cp .env.example .env
# Edit .env and supply NEON_DATABASE_URL and GROQ_API_KEY
```

**Seed Data**:
Populate the database with realistic randomized data:
```bash
python -m app.seed
```

**Start the API Server**:
```bash
uvicorn app.main:app --reload
```
API runs on `http://localhost:8000`.

### 2. Frontend Setup
```bash
cd frontend
npm install

# Connect to the API server:
cp .env.local.example .env.local
# Default port for development is already correct (http://localhost:8000)

# Start Dev Server:
npm run dev
```
The application will launch on `http://localhost:3000`.

---

## 📦 Deployment Strategy

- **Database**: Already cloud-managed via Neon Serverless Postgres.
- **Backend**: Can be natively deployed via Render / Railway.
  - Setup a Web Service connected to your repo targeting the `backend` folder.
  - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Ensure `.env` variables are added in the service configuration.
- **Frontend**: One-click deployable via Vercel. 
  - Framework Preset: Next.js.
  - Set `NEXT_PUBLIC_API_URL` to your Render/Railway backend address.
