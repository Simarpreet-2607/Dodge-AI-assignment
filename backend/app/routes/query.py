"""
routes/query.py - Natural language query endpoint
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.llm import get_llm_service
from app.query_pipeline import QueryPipeline
from app.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def natural_language_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a natural language question and return:
      - Natural language answer (grounded in DB data)
      - SQL query that was executed
      - Raw result rows
      - Graph node IDs to highlight
    """
    if not request.question or len(request.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question is too short.")

    if len(request.question) > 1000:
        raise HTTPException(status_code=400, detail="Question is too long (max 1000 chars).")

    llm = get_llm_service()
    pipeline = QueryPipeline(llm)
    result = await pipeline.run(request, db)
    return result
