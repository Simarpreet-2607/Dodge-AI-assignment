"""
graph.py - NetworkX graph builder and Cytoscape serializer

Builds a directed graph from Neon DB data:
  Customer → Order → OrderItem → Product
  Order → Delivery → Invoice → Payment
"""

from typing import Any, Dict, List
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app import models
from app.schemas import GraphNode, GraphEdge, GraphResponse


# Node type → display color mapping (used by frontend Cytoscape)
NODE_COLORS = {
    "customer": "#6366f1",   # Indigo
    "product":  "#f59e0b",   # Amber
    "order":    "#10b981",   # Emerald
    "delivery": "#3b82f6",   # Blue
    "invoice":  "#8b5cf6",   # Violet
    "payment":  "#ec4899",   # Pink
}


def _node_id(entity_type: str, entity_id: int) -> str:
    """Canonical node ID format: 'customer_1', 'order_5', etc."""
    return f"{entity_type}_{entity_id}"


class GraphBuilder:
    """Builds and caches the business data graph."""

    def __init__(self):
        self.G = nx.DiGraph()
        self._nodes: List[GraphNode] = []
        self._edges: List[GraphEdge] = []

    async def build(self, db: AsyncSession) -> "GraphBuilder":
        """Full graph construction from database."""
        self.G.clear()
        self._nodes = []
        self._edges = []

        await self._load_customers(db)
        await self._load_products(db)
        await self._load_orders(db)
        await self._load_order_items(db)
        await self._load_deliveries(db)
        await self._load_invoices(db)
        await self._load_payments(db)

        return self

    # ── Loaders ─────────────────────────────────────────────────────────────

    async def _load_customers(self, db: AsyncSession):
        result = await db.execute(select(models.Customer))
        for c in result.scalars():
            nid = _node_id("customer", c.id)
            self.G.add_node(nid, type="customer", label=c.name, entity_id=c.id,
                            data={"email": c.email, "phone": c.phone, "city": c.city})
            self._nodes.append(GraphNode(
                id=nid, label=c.name, type="customer",
                data={"id": c.id, "email": c.email, "phone": c.phone, "city": c.city}
            ))

    async def _load_products(self, db: AsyncSession):
        result = await db.execute(select(models.Product))
        for p in result.scalars():
            nid = _node_id("product", p.id)
            self.G.add_node(nid, type="product", label=p.name, entity_id=p.id,
                            data={"category": p.category, "price": str(p.price), "stock": p.stock})
            self._nodes.append(GraphNode(
                id=nid, label=p.name, type="product",
                data={"id": p.id, "category": p.category, "price": str(p.price), "stock": p.stock}
            ))

    async def _load_orders(self, db: AsyncSession):
        result = await db.execute(select(models.Order))
        for o in result.scalars():
            nid = _node_id("order", o.id)
            cid = _node_id("customer", o.customer_id)
            self.G.add_node(nid, type="order", label=f"Order #{o.id}", entity_id=o.id,
                            data={"status": o.status, "total": str(o.total_amount),
                                  "date": str(o.order_date)[:10] if o.order_date else None})
            self._nodes.append(GraphNode(
                id=nid, label=f"Order #{o.id}", type="order",
                data={"id": o.id, "customer_id": o.customer_id, "status": o.status,
                      "total_amount": str(o.total_amount),
                      "order_date": str(o.order_date)[:10] if o.order_date else None}
            ))
            # Customer → Order
            if self.G.has_node(cid):
                self.G.add_edge(cid, nid, label="placed")
                self._edges.append(GraphEdge(source=cid, target=nid, label="placed"))

    async def _load_order_items(self, db: AsyncSession):
        result = await db.execute(select(models.OrderItem))
        for item in result.scalars():
            oid = _node_id("order", item.order_id)
            pid = _node_id("product", item.product_id)
            # Order → Product (via order_item)
            if self.G.has_node(oid) and self.G.has_node(pid):
                # Avoid duplicate edges
                if not self.G.has_edge(oid, pid):
                    self.G.add_edge(oid, pid, label="contains")
                    self._edges.append(GraphEdge(source=oid, target=pid, label="contains"))

    async def _load_deliveries(self, db: AsyncSession):
        result = await db.execute(select(models.Delivery))
        for d in result.scalars():
            nid = _node_id("delivery", d.id)
            oid = _node_id("order", d.order_id)
            self.G.add_node(nid, type="delivery", label=f"Delivery #{d.id}", entity_id=d.id,
                            data={"status": d.status, "carrier": d.carrier,
                                  "tracking_no": d.tracking_no,
                                  "delivered_at": str(d.delivered_at)[:10] if d.delivered_at else None})
            self._nodes.append(GraphNode(
                id=nid, label=f"Delivery #{d.id}", type="delivery",
                data={"id": d.id, "order_id": d.order_id, "status": d.status,
                      "carrier": d.carrier, "tracking_no": d.tracking_no,
                      "delivered_at": str(d.delivered_at)[:10] if d.delivered_at else None}
            ))
            # Order → Delivery
            if self.G.has_node(oid):
                self.G.add_edge(oid, nid, label="shipped_as")
                self._edges.append(GraphEdge(source=oid, target=nid, label="shipped_as"))

    async def _load_invoices(self, db: AsyncSession):
        result = await db.execute(select(models.Invoice))
        for inv in result.scalars():
            nid = _node_id("invoice", inv.id)
            did = _node_id("delivery", inv.delivery_id)
            self.G.add_node(nid, type="invoice", label=f"Invoice #{inv.id}", entity_id=inv.id,
                            data={"amount": str(inv.amount),
                                  "issued_at": str(inv.issued_at)[:10] if inv.issued_at else None,
                                  "due_date": str(inv.due_date)[:10] if inv.due_date else None})
            self._nodes.append(GraphNode(
                id=nid, label=f"Invoice #{inv.id}", type="invoice",
                data={"id": inv.id, "delivery_id": inv.delivery_id,
                      "amount": str(inv.amount),
                      "issued_at": str(inv.issued_at)[:10] if inv.issued_at else None,
                      "due_date": str(inv.due_date)[:10] if inv.due_date else None}
            ))
            # Delivery → Invoice
            if self.G.has_node(did):
                self.G.add_edge(did, nid, label="billed_as")
                self._edges.append(GraphEdge(source=did, target=nid, label="billed_as"))

    async def _load_payments(self, db: AsyncSession):
        result = await db.execute(select(models.Payment))
        for pay in result.scalars():
            nid = _node_id("payment", pay.id)
            iid = _node_id("invoice", pay.invoice_id)
            self.G.add_node(nid, type="payment", label=f"Payment #{pay.id}", entity_id=pay.id,
                            data={"amount": str(pay.amount), "status": pay.status,
                                  "method": pay.method,
                                  "paid_at": str(pay.paid_at)[:10] if pay.paid_at else None})
            self._nodes.append(GraphNode(
                id=nid, label=f"Payment #{pay.id}", type="payment",
                data={"id": pay.id, "invoice_id": pay.invoice_id,
                      "amount": str(pay.amount), "status": pay.status,
                      "method": pay.method,
                      "paid_at": str(pay.paid_at)[:10] if pay.paid_at else None}
            ))
            # Invoice → Payment
            if self.G.has_node(iid):
                self.G.add_edge(iid, nid, label="settled_by")
                self._edges.append(GraphEdge(source=iid, target=nid, label="settled_by"))

    # ── Public interface ─────────────────────────────────────────────────────

    def to_response(self) -> GraphResponse:
        return GraphResponse(
            nodes=self._nodes,
            edges=self._edges,
            node_count=len(self._nodes),
            edge_count=len(self._edges),
        )

    def get_neighbors(self, node_id: str) -> List[str]:
        """Return all directly connected node IDs (both directions)."""
        neighbors = set(self.G.successors(node_id)) | set(self.G.predecessors(node_id))
        return list(neighbors)

    def get_node_data(self, node_id: str) -> Dict[str, Any]:
        return self.G.nodes.get(node_id, {})

    def node_exists(self, node_id: str) -> bool:
        return self.G.has_node(node_id)

    def all_node_ids(self) -> List[str]:
        return list(self.G.nodes())


# Singleton graph instance (rebuilt on startup and on /graph/refresh)
_graph_instance: GraphBuilder = GraphBuilder()


def get_graph() -> GraphBuilder:
    return _graph_instance


async def rebuild_graph(db: AsyncSession) -> GraphBuilder:
    global _graph_instance
    _graph_instance = GraphBuilder()
    await _graph_instance.build(db)
    return _graph_instance
