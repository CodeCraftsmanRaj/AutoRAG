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
6. Full one-shot e2e test:
  `./scripts/e2e_gemini.sh`

How it works: `/ingest` builds vectors with Gemini embeddings from `docs/`, `/query` retrieves and answers with Gemini, and `app.eval` runs local heuristic scoring from `golden_dataset.json`; after changing `.env`, recreate the container.

## How to access docs used by RAG

- Source docs are under [docs](docs/).
- They are mounted into container at `/app/docs`.
- After editing docs, rerun `/ingest` with `rebuild=true`.

## Proof / verification checks

### Local app (working proof)

- Health: `GET http://localhost:8000/health` should return `"status":"ok"`.
- Ingest: `/ingest` should return `"status":"ingested"` with `chunks > 0`.
- Query: `/query` should return non-empty `answer` and relevant `contexts`.
- E2E: `./scripts/e2e_gemini.sh` should end with `PASS`.

### Jenkins (configured in repo)

- Files: [jenkins/Jenkinsfile](jenkins/Jenkinsfile), [jenkins/shared-library/vars/ragPipeline.groovy](jenkins/shared-library/vars/ragPipeline.groovy).
- UI proof: open your Jenkins job and confirm stages run (checkout, quality, build, eval, deploy).

### Prometheus (configured in repo)

- File: [monitoring/prometheus.yml](monitoring/prometheus.yml).
- UI proof: in Prometheus `Status -> Targets`, `auto-rag-app` target should be `UP` when deployed.

### Grafana (configured in repo)

- File: [monitoring/rag-dashboard.json](monitoring/rag-dashboard.json).
- UI proof: import dashboard JSON; panels should show request/latency/health metrics.

> Note: this Docker compose starts only the RAG app. Jenkins/Prometheus/Grafana are present as project artifacts and require your deployment environment to run.

For full architecture and lifecycle details, see [AUTO_RAG_END_TO_END.md](AUTO_RAG_END_TO_END.md).
