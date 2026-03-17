import os
from pathlib import Path
from typing import Dict, Iterable, List

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag import _vectorstore

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


def _iter_files(paths: Iterable[str]) -> Iterable[Path]:
	for root in paths:
		root_path = Path(root)
		if not root_path.exists():
			continue
		if root_path.is_file() and root_path.suffix.lower() in SUPPORTED_EXTENSIONS:
			yield root_path
		for file in root_path.rglob("*"):
			if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
				yield file


def _load_file(path: Path):
	if path.suffix.lower() == ".pdf":
		return PyPDFLoader(str(path)).load()
	return TextLoader(str(path), autodetect_encoding=True).load()


def ingest_paths(paths: List[str], rebuild: bool = True) -> Dict[str, int]:
	splitter = RecursiveCharacterTextSplitter(
		chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
		chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
	)

	docs = []
	files = list(_iter_files(paths))
	for file in files:
		loaded = _load_file(file)
		for doc in loaded:
			doc.metadata["source_path"] = str(file)
		docs.extend(loaded)

	chunks = splitter.split_documents(docs)
	store = _vectorstore()

	if rebuild:
		store.delete_collection()
		store = _vectorstore()

	if chunks:
		store.add_documents(chunks)

	return {
		"files": len(files),
		"documents": len(docs),
		"chunks": len(chunks),
		"rebuild": int(rebuild),
	}

