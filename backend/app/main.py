"""
main.py - FastAPI application entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.graph import rebuild_graph, get_graph
from app.database import AsyncSessionLocal
from app.routes import graph as graph_router
from app.routes import query as query_router
from app.routes import node as node_router


# ── Lifespan (startup / shutdown) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before serving requests."""
    print("🚀 Starting Graph-Based Data Modeling and Query System...")

    # Create DB tables if they don't exist
    await create_tables()
    print("✅ Database tables ready.")

    # Pre-build the graph
    async with AsyncSessionLocal() as db:
        graph = await rebuild_graph(db)
        print(f"✅ Graph built: {graph.to_response().node_count} nodes, "
              f"{graph.to_response().edge_count} edges.")

    yield  # App runs here

    print("👋 Shutting down...")


# ── App Instance ────────────────────────────────────────────────────────────

app = FastAPI(
    title="Graph-Based Data Modeling and Query System",
    description=(
        "Transform relational business data into an interactive graph "
        "and query it using natural language powered by Groq LLM."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────────────────────

app.include_router(graph_router.router)
app.include_router(query_router.router)
app.include_router(node_router.router)


@app.get("/health", tags=["Health"])
async def health_check():
    graph = get_graph()
    stats = graph.to_response()
    return {
        "status": "healthy",
        "graph_nodes": stats.node_count,
        "graph_edges": stats.edge_count,
        "model": settings.GROQ_MODEL,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Graph-Based Data Modeling and Query System API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "graph":  "GET /graph",
            "query":  "POST /query",
            "node":   "GET /node/{type}/{id}",
            "refresh":"GET /graph/refresh",
        },
    }
