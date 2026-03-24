# Auto-RAG (Docker only)

This service runs a RAG API with 3 endpoints: `GET /health`, `POST /ingest`, `POST /query`. It stores vectors in Docker volume `rag_chroma_data`, ingests docs from `./docs`, and evaluates quality from `rag-app/golden_dataset.json`.

## Run / Use / Test (short)

1. `cp .env.example .env` and set `GEMINI_API_KEY`.
2. `docker compose up -d --build --force-recreate` (required after any `.env` change).
3. Ingest docs:
  `curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d '{"paths":["/app/docs"],"rebuild":true}'`
4. Ask:
  `curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question":"What is the support SLA for critical incidents?"}'`
5. Test quality gate:
  `docker compose exec rag-app python -m app.eval`

How it works: `/ingest` builds vectors with Gemini embeddings from `docs/`, `/query` retrieves and answers with Gemini, and `app.eval` now runs local heuristic scoring from `golden_dataset.json` so it does not burn Gemini quota; after changing `.env`, recreate the container.
