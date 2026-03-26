"""
routes/node.py - Individual node detail endpoint
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.graph import get_graph, _node_id
from app.schemas import NodeDetailResponse
from app import models

router = APIRouter(prefix="/node", tags=["Node"])

# Map type → SQLAlchemy model
MODEL_MAP = {
    "customer": models.Customer,
    "product":  models.Product,
    "order":    models.Order,
    "delivery": models.Delivery,
    "invoice":  models.Invoice,
    "payment":  models.Payment,
}


@router.get("/{node_type}/{node_id}", response_model=NodeDetailResponse)
async def get_node_detail(
    node_type: str,
    node_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Return detailed metadata for a specific graph node, along with
    its direct neighbors in the graph.
    """
    if node_type not in MODEL_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown node type: {node_type}")

    model_cls = MODEL_MAP[node_type]
    result = await db.execute(select(model_cls).where(model_cls.id == node_id))
    entity = result.scalar_one_or_none()

    if entity is None:
        raise HTTPException(status_code=404, detail=f"{node_type} #{node_id} not found.")

    # Serialize entity columns to dict (exclude relationships)
    properties = {
        col.key: str(getattr(entity, col.key)) if getattr(entity, col.key) is not None else None
        for col in entity.__table__.columns
    }

    # Get graph neighbors
    graph = get_graph()
    canonical_id = _node_id(node_type, node_id)
    neighbor_ids = graph.get_neighbors(canonical_id)

    connected_nodes = []
    for nid in neighbor_ids:
        nd = graph.get_node_data(nid)
        if nd:
            connected_nodes.append({
                "id": nid,
                "type": nd.get("type"),
                "label": nd.get("label"),
            })

    label = properties.get("name") or f"{node_type.capitalize()} #{node_id}"

    return NodeDetailResponse(
        id=canonical_id,
        type=node_type,
        label=label,
        properties=properties,
        connected_nodes=connected_nodes,
    )
