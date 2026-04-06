# Auto-RAG (Docker only)

This setup now runs a full local stack with Docker: RAG API + Jenkins + Prometheus + Grafana + SonarQube.

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
  `powershell -ExecutionPolicy Bypass -File .\scripts\e2e_windows_gemini.ps1`

How it works: `/ingest` builds vectors with Gemini embeddings from `docs/`, `/query` retrieves and answers with Gemini, and `app.eval` runs local heuristic scoring from `golden_dataset.json`; after changing `.env`, recreate the container.

## How to access docs used by RAG

- Source docs are under [docs](docs/).
- They are mounted into container at `/app/docs`.
- After editing docs, rerun `/ingest` with `rebuild=true`.

## Local UI access (all running via Docker)

- RAG API: http://localhost:8000/docs
- Jenkins: http://localhost:8081
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (default `admin` / `admin`)
- SonarQube: http://localhost:9000

If any port is already occupied, change it in `.env` using `RAG_API_PORT`, `JENKINS_PORT`, `PROMETHEUS_PORT`, `GRAFANA_PORT`, `SONARQUBE_PORT`.

## Proof / verification checks

### Local app (working proof)

- Health: `GET http://localhost:8000/health` should return `"status":"ok"`.
- Ingest: `/ingest` should return `"status":"ingested"` with `chunks > 0`.
- Query: `/query` should return non-empty `answer` and relevant `contexts`.
- E2E: `./scripts/e2e_gemini.sh` should end with `PASS`.

### Jenkins (configured in repo)

- Files: [jenkins/Jenkinsfile](jenkins/Jenkinsfile), [jenkins/shared-library/vars/ragPipeline.groovy](jenkins/shared-library/vars/ragPipeline.groovy).
- UI proof:
  - Open Jenkins UI and create a Pipeline job from this repo.
  - Set script path to [jenkins/Jenkinsfile](jenkins/Jenkinsfile).
  - Trigger build and verify stages appear and execute.

### Prometheus (configured in repo)

- File: [monitoring/prometheus.yml](monitoring/prometheus.yml).
- UI proof: open `Status -> Targets` and verify `auto-rag-app` is `UP`.

### Grafana (configured in repo)

- File: [monitoring/rag-dashboard.json](monitoring/rag-dashboard.json).
- UI proof:
  - Login at Grafana UI.
  - Datasource `Prometheus` is auto-provisioned.
  - Dashboard `Auto-RAG Overview` is auto-loaded and should show request/latency metrics after traffic.

### SonarQube (configured for local use)

- UI proof:
  - Open SonarQube UI.
  - Create a local project token.
  - Use token in Jenkins credentials and run pipeline scan stage.

All above services are started by [docker-compose.yml](docker-compose.yml) in this local setup.

For full architecture and lifecycle details, see [AUTO_RAG_END_TO_END.md](AUTO_RAG_END_TO_END.md).
For step-by-step UI actions (where to ingest/query and where to verify outputs), see [UI_WORKFLOW_GUIDE.md](UI_WORKFLOW_GUIDE.md).
