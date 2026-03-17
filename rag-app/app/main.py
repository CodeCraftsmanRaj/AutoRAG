from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.ingest import ingest_paths
from app.rag import get_rag_health, query_rag

app = FastAPI(title="Auto-RAG Pipeline", version="0.1.0")


class IngestRequest(BaseModel):
	paths: List[str] = Field(default=["/app/docs"])
	rebuild: bool = True


class QueryRequest(BaseModel):
	question: str
	top_k: int = 4
	namespace: Optional[str] = "default"


@app.get("/health")
def health() -> dict:
	return {"status": "ok", **get_rag_health()}


@app.post("/ingest")
def ingest(req: IngestRequest) -> dict:
	try:
		result = ingest_paths(req.paths, rebuild=req.rebuild)
		return {"status": "ingested", "details": result}
	except Exception as exc:  # pragma: no cover
		raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/query")
def query(req: QueryRequest) -> dict:
	try:
		response = query_rag(question=req.question, top_k=req.top_k, namespace=req.namespace)
		return {
			"question": req.question,
			"answer": response["answer"],
			"contexts": response["contexts"],
			"latency_ms": response["latency_ms"],
			"tokens": response.get("tokens", {}),
		}
	except Exception as exc:  # pragma: no cover
		raise HTTPException(status_code=500, detail=str(exc)) from exc

