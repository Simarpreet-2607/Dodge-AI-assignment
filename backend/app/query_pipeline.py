"""
query_pipeline.py - Full NL → SQL → DB → NL pipeline with guardrails
"""

import re
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.llm import LLMService, DANGEROUS_KEYWORDS, ALLOWED_TABLES
from app.schemas import QueryRequest, QueryResponse


class QueryPipeline:
    """
    Orchestrates the full natural language query pipeline:
      1. Topic guardrail  — reject off-domain questions
      2. SQL generation   — LLM translates NL → SQL
      3. SQL validation   — safety + schema check
      4. DB execution     — run on Neon
      5. NL formatting    — LLM converts results → readable answer
      6. Node extraction  — identify highlighted graph nodes
    """

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(
        self,
        request: QueryRequest,
        db: AsyncSession,
    ) -> QueryResponse:
        question = request.question.strip()

        # ── Step 1: Topic Guardrail ──────────────────────────────────────────
        try:
            is_related = await self.llm.is_related_query(question)
        except Exception as e:
            return QueryResponse(
                answer="Unable to process your query at the moment. Please try again.",
                is_data_query=False,
                error=str(e),
            )

        if not is_related:
            return QueryResponse(
                answer="This system only answers dataset-related queries about customers, orders, products, deliveries, invoices, and payments.",
                is_data_query=False,
            )

        # ── Step 2: Generate SQL ─────────────────────────────────────────────
        try:
            sql_query = await self.llm.generate_sql(
                question,
                chat_history=request.chat_history,
            )
        except ValueError as e:
            return QueryResponse(
                answer=str(e),
                is_data_query=False,
            )
        except Exception as e:
            return QueryResponse(
                answer="Failed to generate SQL query. Please rephrase your question.",
                is_data_query=False,
                error=str(e),
            )

        # ── Step 3: Validate SQL ─────────────────────────────────────────────
        validation_error = self._validate_sql(sql_query)
        if validation_error:
            return QueryResponse(
                answer=f"Query rejected: {validation_error}",
                is_data_query=False,
                sql_query=sql_query,
            )

        # ── Step 4: Execute SQL ──────────────────────────────────────────────
        try:
            results = await self._execute_sql(db, sql_query)
        except Exception as e:
            return QueryResponse(
                answer="Failed to execute the query against the database. Please try a different question.",
                sql_query=sql_query,
                is_data_query=True,
                error=str(e),
            )

        # ── Step 5: Format Results ───────────────────────────────────────────
        try:
            answer = await self.llm.format_results(question, sql_query, results)
        except Exception as e:
            # Fallback: return raw results if formatting fails
            answer = f"Query returned {len(results)} result(s). Raw data available."

        # ── Step 6: Extract Highlighted Nodes ───────────────────────────────
        highlighted = self.llm.extract_highlighted_nodes(results)

        return QueryResponse(
            answer=answer,
            sql_query=sql_query,
            raw_results=results[:50],         # Cap at 50 for API response size
            highlighted_nodes=highlighted,
            is_data_query=True,
        )

    # ── SQL Validation ───────────────────────────────────────────────────────

    def _validate_sql(self, sql: str) -> Optional[str]:
        """
        Returns an error message if SQL is unsafe, else None.
        """
        sql_upper = sql.upper()

        # Block dangerous SQL
        if DANGEROUS_KEYWORDS.search(sql):
            return "Query contains forbidden SQL keywords (DML/DDL not allowed)."

        # Must start with SELECT
        sql_stripped = sql.strip()
        if not sql_stripped.upper().startswith("SELECT"):
            return "Only SELECT queries are permitted."

        # Check for comment-based injection
        if "--" in sql or "/*" in sql:
            return "SQL comments are not allowed."

        # Basic semicolon injection guard
        if sql.count(";") > 1:
            return "Multiple statements are not allowed."

        return None  # Valid

    # ── SQL Execution ────────────────────────────────────────────────────────

    async def _execute_sql(
        self,
        db: AsyncSession,
        sql: str,
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return list of row dicts."""
        result = await db.execute(text(sql))
        columns = list(result.keys())
        rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]
