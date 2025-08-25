from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.search import PostSearchService


class SearchResponse(BaseModel):
    total: int
    items: list


search_router = APIRouter(prefix="/search", tags=["search"])


@search_router.get("/posts", response_model=SearchResponse)
def search_posts(q: str = Query(""), category: Optional[str] = Query(None), size: int = Query(10, ge=1, le=100), page: int = Query(1, ge=1)):
    service = PostSearchService()
    es_from = (page - 1) * size
    result = service.search_posts(query=q, category=category, size=size, from_=es_from)

    hits = result.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    items = [
        {
            "id": h.get("_id"),
            **h.get("_source", {}),
            "score": h.get("_score"),
        }
        for h in hits.get("hits", [])
    ]
    return {"total": total, "items": items}


