"""
schemas.py - Pydantic schemas for API request/response validation
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr


# ── Customer ───────────────────────────────────────────────────────────────

class CustomerBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    city: Optional[str] = None

class CustomerOut(CustomerBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Product ────────────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None
    price: Decimal
    stock: int = 0

class ProductOut(ProductBase):
    id: int
    model_config = {"from_attributes": True}


# ── Order ──────────────────────────────────────────────────────────────────

class OrderOut(BaseModel):
    id: int
    customer_id: int
    order_date: Optional[datetime] = None
    status: str
    total_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    model_config = {"from_attributes": True}


# ── OrderItem ──────────────────────────────────────────────────────────────

class OrderItemOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    model_config = {"from_attributes": True}


# ── Delivery ───────────────────────────────────────────────────────────────

class DeliveryOut(BaseModel):
    id: int
    order_id: int
    status: str
    delivered_at: Optional[datetime] = None
    carrier: Optional[str] = None
    tracking_no: Optional[str] = None
    model_config = {"from_attributes": True}


# ── Invoice ────────────────────────────────────────────────────────────────

class InvoiceOut(BaseModel):
    id: int
    delivery_id: int
    amount: Decimal
    issued_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Payment ────────────────────────────────────────────────────────────────

class PaymentOut(BaseModel):
    id: int
    invoice_id: int
    amount: Decimal
    status: str
    method: Optional[str] = None
    paid_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Graph ──────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    type: str          # customer | product | order | delivery | invoice | payment
    data: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    source: str
    target: str
    label: str

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    node_count: int
    edge_count: int


# ── Query ──────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = []

class QueryResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    raw_results: Optional[List[Dict[str, Any]]] = None
    highlighted_nodes: Optional[List[str]] = []
    is_data_query: bool = True
    error: Optional[str] = None


# ── Node Detail ────────────────────────────────────────────────────────────

class NodeDetailResponse(BaseModel):
    id: str
    type: str
    label: str
    properties: Dict[str, Any]
    connected_nodes: List[Dict[str, Any]] = []
