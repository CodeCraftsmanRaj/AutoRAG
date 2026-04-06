import os
import time
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./.chroma")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "auto_rag")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "gemini").lower()


def _load_symbol(module_name: str, symbol_name: str):
	module = import_module(module_name)
	return getattr(module, symbol_name)


class _ChromaEmbeddingAdapter:
	"""Adapt Chroma's callable embedding function to LangChain's interface."""

	def __init__(self, embedding_function):
		self._embedding_function = embedding_function

	def embed_documents(self, texts: List[str]) -> List[List[float]]:
		return self._embedding_function(texts)

	def embed_query(self, text: str) -> List[float]:
		return self._embedding_function([text])[0]


def _embeddings():
	"""Prefer API embeddings over local transformer models to avoid torch/meta runtime issues."""
	if EMBEDDINGS_PROVIDER == "gemini" and os.getenv("GEMINI_API_KEY"):
		GoogleGenerativeAIEmbeddings = _load_symbol(
			"langchain_google_genai",
			"GoogleGenerativeAIEmbeddings",
		)
		return GoogleGenerativeAIEmbeddings(
			model=os.getenv("EMBEDDING_MODEL", "models/text-embedding-004"),
			google_api_key=os.getenv("GEMINI_API_KEY"),
		)
	if EMBEDDINGS_PROVIDER == "openai" and os.getenv("OPENAI_API_KEY"):
		OpenAIEmbeddings = _load_symbol("langchain_openai", "OpenAIEmbeddings")
		return OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
	DefaultEmbeddingFunction = _load_symbol(
		"chromadb.utils.embedding_functions",
		"DefaultEmbeddingFunction",
	)
	return _ChromaEmbeddingAdapter(DefaultEmbeddingFunction())


def _vectorstore():
	Chroma = _load_symbol("langchain_chroma", "Chroma")
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
		"llm_provider": LLM_PROVIDER,
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


def _extractive_answer(question: str, contexts: List[str]) -> str:
	question_terms = {term.strip("?,.!:;()[]{}\"'").lower() for term in question.split() if len(term) > 2}
	best_line = contexts[0][:400]
	best_score = -1
	for context in contexts:
		for line in context.splitlines():
			line_terms = {term.strip("?,.!:;()[]{}\"'").lower() for term in line.split() if len(term) > 2}
			score = len(question_terms & line_terms)
			if score > best_score and line.strip():
				best_score = score
				best_line = line.strip()
	return best_line


def query_rag(question: str, top_k: int = 4, namespace: str = "default", use_llm: bool = True) -> Dict[str, Any]:
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

	if not use_llm:
		answer = _extractive_answer(question, contexts)
	elif LLM_PROVIDER == "gemini" and os.getenv("GEMINI_API_KEY"):
		try:
			ChatGoogleGenerativeAI = _load_symbol("langchain_google_genai", "ChatGoogleGenerativeAI")
			llm = ChatGoogleGenerativeAI(
				model=LLM_MODEL,
				temperature=0,
				google_api_key=os.getenv("GEMINI_API_KEY"),
			)
			prompt = _build_prompt(question, contexts)
			output = llm.invoke(prompt)
			answer = output.content if hasattr(output, "content") else str(output)
		except Exception:
			answer = "Gemini generation unavailable (auth/quota/model issue). Top retrieved context: " + contexts[0][:400]
	elif os.getenv("OPENAI_API_KEY"):
		try:
			ChatOpenAI = _load_symbol("langchain_openai", "ChatOpenAI")
			llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
			prompt = _build_prompt(question, contexts)
			output = llm.invoke(prompt)
			answer = output.content if hasattr(output, "content") else str(output)
		except Exception:
			answer = "LLM generation unavailable (auth/quota/model issue). Top retrieved context: " + contexts[0][:400]
	else:
		# Local fallback when no API key is provided.
		answer = (
			"No LLM key is set. "
			"Top retrieved context: " + contexts[0][:400]
		)

	return {
		"answer": answer,
		"contexts": contexts,
		"latency_ms": round((time.perf_counter() - start) * 1000, 2),
		"tokens": {},
		"namespace": namespace,
	}

