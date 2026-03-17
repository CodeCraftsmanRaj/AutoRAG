import os
import time
from pathlib import Path
from typing import Any, Dict, List

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./.chroma")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "auto_rag")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def _embeddings():
	"""Prefer OpenAI embeddings; fallback to local HF embeddings for local/minikube runs."""
	if os.getenv("OPENAI_API_KEY"):
		return OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
	return HuggingFaceEmbeddings(model_name=os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))


def _vectorstore() -> Chroma:
	Path(VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
	return Chroma(
		collection_name=COLLECTION_NAME,
		embedding_function=_embeddings(),
		persist_directory=VECTOR_DB_PATH,
	)


def get_rag_health() -> Dict[str, Any]:
	store = _vectorstore()
	count = store._collection.count() if store._collection else 0
	return {
		"collection": COLLECTION_NAME,
		"vector_db_path": VECTOR_DB_PATH,
		"chunks": count,
		"llm_model": LLM_MODEL,
	}


def _format_context(docs) -> List[str]:
	return [d.page_content[:1200] for d in docs]


def _build_prompt(question: str, contexts: List[str]) -> str:
	context_blob = "\n\n".join([f"Context {i+1}:\n{ctx}" for i, ctx in enumerate(contexts)])
	return (
		"You are a precise RAG assistant. "
		"Answer using only the given contexts. If unknown, say you don't know.\n\n"
		f"{context_blob}\n\n"
		f"Question: {question}\nAnswer:"
	)


def query_rag(question: str, top_k: int = 4, namespace: str = "default") -> Dict[str, Any]:
	start = time.perf_counter()
	store = _vectorstore()
	retriever = store.as_retriever(search_kwargs={"k": top_k})
	docs = retriever.invoke(question)
	contexts = _format_context(docs)

	if not contexts:
		return {
			"answer": "I don't know based on the available knowledge base.",
			"contexts": [],
			"latency_ms": round((time.perf_counter() - start) * 1000, 2),
			"tokens": {},
			"namespace": namespace,
		}

	if os.getenv("OPENAI_API_KEY"):
		llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
		prompt = _build_prompt(question, contexts)
		output = llm.invoke(prompt)
		answer = output.content if hasattr(output, "content") else str(output)
	else:
		# Local fallback when no API key is provided.
		answer = (
			"OPENAI_API_KEY is not set. "
			"Top retrieved context: " + contexts[0][:400]
		)

	return {
		"answer": answer,
		"contexts": contexts,
		"latency_ms": round((time.perf_counter() - start) * 1000, 2),
		"tokens": {},
		"namespace": namespace,
	}

