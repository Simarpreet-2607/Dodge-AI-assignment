"""
routes/graph.py - Graph data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.graph import get_graph, rebuild_graph, _node_id, NODE_COLORS
from app.schemas import GraphResponse, NodeDetailResponse

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("", response_model=GraphResponse)
async def get_graph_data(db: AsyncSession = Depends(get_db)):
    """
    Return the full graph (nodes + edges) in Cytoscape-compatible format.
    Uses cached graph; call /graph/refresh to rebuild from latest DB data.
    """
    graph = get_graph()

    # If graph is empty (first request), build it
    if not graph.all_node_ids():
        await rebuild_graph(db)
        graph = get_graph()

    return graph.to_response()


@router.get("/refresh", response_model=GraphResponse)
async def refresh_graph(db: AsyncSession = Depends(get_db)):
    """Force-rebuild the graph from the latest database state."""
    graph = await rebuild_graph(db)
    return graph.to_response()


@router.get("/colors")
async def get_node_colors():
    """Return color mapping for each node type (used by frontend)."""
    return NODE_COLORS
