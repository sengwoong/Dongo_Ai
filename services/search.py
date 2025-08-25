from typing import List, Optional

from elasticsearch import Elasticsearch


class PostSearchService:
    def __init__(self, es: Optional[Elasticsearch] = None, index_name: str = "posts-shared") -> None:
        self._es = es or Elasticsearch("http://localhost:9200")
        self._index = index_name

    def search_posts(self, query: str, category: Optional[str] = None, size: int = 10, from_: int = 0) -> dict:
        must_clauses: List[dict] = []
        if query:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content"],
                        "type": "most_fields",
                    }
                }
            )
        filter_clauses: List[dict] = [
            {"term": {"is_shared": True}}
        ]
        if category:
            filter_clauses.append({"term": {"category": category}})

        es_query = {
            "bool": {
                "must": must_clauses or {"match_all": {}},
                "filter": filter_clauses,
            }
        }

        resp = self._es.search(
            index=self._index,
            query=es_query,
            sort=[{"updatedAt": {"order": "desc"}}],
            size=size,
            from_=from_,
        )
        return resp


