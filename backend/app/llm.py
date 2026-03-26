"""
llm.py - Groq LLM integration for NL→SQL and result formatting
"""

import json
import re
from typing import Any, Dict, List, Optional
from groq import AsyncGroq
from app.config import settings


# ── Schema description injected into every LLM prompt ──────────────────────

SCHEMA_DESCRIPTION = """
DATABASE SCHEMA (PostgreSQL):

TABLE: customers
  - id (INTEGER, PRIMARY KEY)
  - name (VARCHAR)
  - email (VARCHAR)
  - phone (VARCHAR)
  - city (VARCHAR)
  - created_at (TIMESTAMP)

TABLE: products
  - id (INTEGER, PRIMARY KEY)
  - name (VARCHAR)
  - category (VARCHAR)
  - price (NUMERIC)
  - stock (INTEGER)

TABLE: orders
  - id (INTEGER, PRIMARY KEY)
  - customer_id (INTEGER, FK → customers.id)
  - order_date (TIMESTAMP)
  - status (ENUM: pending, confirmed, shipped, delivered, cancelled)
  - total_amount (NUMERIC)
  - notes (TEXT)

TABLE: order_items
  - id (INTEGER, PRIMARY KEY)
  - order_id (INTEGER, FK → orders.id)
  - product_id (INTEGER, FK → products.id)
  - quantity (INTEGER)
  - unit_price (NUMERIC)

TABLE: deliveries
  - id (INTEGER, PRIMARY KEY)
  - order_id (INTEGER, FK → orders.id, UNIQUE)
  - status (ENUM: pending, in_transit, delivered, failed)
  - delivered_at (TIMESTAMP)
  - carrier (VARCHAR)
  - tracking_no (VARCHAR)

TABLE: invoices
  - id (INTEGER, PRIMARY KEY)
  - delivery_id (INTEGER, FK → deliveries.id, UNIQUE)
  - amount (NUMERIC)
  - issued_at (TIMESTAMP)
  - due_date (TIMESTAMP)

TABLE: payments
  - id (INTEGER, PRIMARY KEY)
  - invoice_id (INTEGER, FK → invoices.id)
  - amount (NUMERIC)
  - status (ENUM: pending, paid, failed, refunded)
  - method (VARCHAR)
  - paid_at (TIMESTAMP)

RELATIONSHIPS:
  Customer (1) → (many) Orders
  Order (1) → (many) OrderItems
  OrderItem (many) → (1) Product
  Order (1) → (0..1) Delivery
  Delivery (1) → (0..1) Invoice
  Invoice (1) → (many) Payments
"""

# Tables allowed in queries
ALLOWED_TABLES = {
    "customers", "products", "orders", "order_items",
    "deliveries", "invoices", "payments"
}

# Dangerous SQL keywords
DANGEROUS_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|TRUNCATE|CREATE|REPLACE|EXEC|EXECUTE|GRANT|REVOKE)\b",
    re.IGNORECASE
)


class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    # ── Topic Guardrail ──────────────────────────────────────────────────────

    async def is_related_query(self, question: str) -> bool:
        """Classify question as RELATED or UNRELATED to the dataset."""
        system_prompt = (
            "You are a classifier that determines if a user's question is related to "
            "a business database containing customers, products, orders, deliveries, invoices, and payments. "
            "Respond with exactly one word: RELATED or UNRELATED."
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": question},
            ],
            max_tokens=10,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer == "RELATED"

    # ── NL → SQL ─────────────────────────────────────────────────────────────

    async def generate_sql(self, question: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        Translate a natural language question into a SQL SELECT query.
        Returns the raw SQL string or raises ValueError.
        """
        system_prompt = f"""You are an expert PostgreSQL query generator.

{SCHEMA_DESCRIPTION}

RULES:
1. Generate ONLY a valid PostgreSQL SELECT query.
2. Do NOT use DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, CREATE, or any DDL/DML.
3. Only reference the tables listed in the schema above.
4. Do NOT wrap the query in markdown code blocks or add any explanation.
5. Use table aliases for clarity. Use LIMIT 100 unless the question asks for a count.
6. Always use lowercase for SQL keywords? No — follow PostgreSQL convention (uppercase keywords).
7. If the question cannot be answered from the schema, output exactly: CANNOT_ANSWER
"""
        messages = [{"role": "system", "content": system_prompt}]

        # Include recent chat history for context
        if chat_history:
            for msg in chat_history[-4:]:  # Last 4 messages only
                messages.append(msg)

        messages.append({"role": "user", "content": question})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=500,
            temperature=0.1,
        )

        sql = response.choices[0].message.content.strip()

        if sql == "CANNOT_ANSWER":
            raise ValueError("Query cannot be answered from the available schema.")

        return sql

    # ── Format Results as Natural Language ───────────────────────────────────

    async def format_results(
        self,
        question: str,
        sql_query: str,
        results: List[Dict[str, Any]],
    ) -> str:
        """
        Convert raw SQL results into a human-readable answer.
        Strictly grounded — no hallucination.
        """
        if not results:
            return "No records found matching your query."

        results_json = json.dumps(results[:50], default=str, indent=2)

        system_prompt = """You are a data analyst that explains query results clearly.

STRICT RULES:
1. Base your answer ONLY on the data provided. Do NOT add any information not in the data.
2. Be concise but complete.
3. Use bullet points or tables when listing multiple items.
4. If the data is empty, say "No records found."
5. Never make up numbers, names, or facts."""

        user_prompt = f"""User question: {question}

SQL query used:
{sql_query}

Query results (JSON):
{results_json}

Write a clear, accurate answer based strictly on these results."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=800,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    # ── Extract highlighted node IDs from results ────────────────────────────

    def extract_highlighted_nodes(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Parse result rows and return graph node IDs to highlight.
        Looks for columns named: customer_id, product_id, order_id,
        delivery_id, invoice_id, payment_id
        """
        highlighted = set()
        id_map = {
            "customer_id":  "customer",
            "product_id":   "product",
            "order_id":     "order",
            "delivery_id":  "delivery",
            "invoice_id":   "invoice",
            "payment_id":   "payment",
            # Direct id columns in entity-specific queries
            "id": None,
        }

        for row in results:
            for col, entity_type in id_map.items():
                if col in row and row[col] is not None and entity_type:
                    highlighted.add(f"{entity_type}_{row[col]}")

        return list(highlighted)


# Module-level singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
