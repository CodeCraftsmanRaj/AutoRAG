# Auto-RAG End-to-End Guide

## What this project does

This repository automates a RAG workflow with Gemini:

1. Ingest docs from `docs/` into Chroma vectors.
2. Retrieve context and answer queries via FastAPI.
3. Run a quality gate over a golden dataset.
4. Keep CI/CD + infra + monitoring artifacts ready (Jenkins, Helm, Terraform, Prometheus, Grafana).

## Runtime flow (current local setup)

Local Docker run currently starts the RAG app service.

- API: `rag-app/app/main.py`
- Ingestion: `rag-app/app/ingest.py`
- RAG logic: `rag-app/app/rag.py`
- Eval gate: `rag-app/app/eval.py`
- Dataset: `rag-app/golden_dataset.json`
- Docs source: `docs/`

### End-to-end command (already created)

Use:

- `./scripts/e2e_gemini.sh`

This script performs:

1. Rebuild/recreate containers.
2. Wait for `/health`.
3. Run `/ingest` with rebuild=true.
4. Run `/query` smoke test.
5. Run `python -m app.eval` and enforce threshold.

PASS means the local RAG pipeline is healthy end-to-end.

## How to verify docs are actually used

1. Put/update content in `docs/`.
2. Run ingest.
3. Ask a question tied to that new content.
4. Check `contexts` in `/query` response include the updated docs text.

## CI/CD + monitoring components in repo

These are present in code and can be validated by file/config and runtime checks.

### Jenkins

- Pipeline: `jenkins/Jenkinsfile`
- Shared library: `jenkins/shared-library/vars/ragPipeline.groovy`

Proof checks:

- Open Jenkins UI and confirm job uses this Jenkinsfile.
- Run build and verify stages: checkout, quality scan, build, eval, deploy.

### Prometheus

- Config: `monitoring/prometheus.yml`

Proof checks:

- Prometheus UI `Status -> Targets` should show `auto-rag-app` target as UP.

### Grafana

- Dashboard definition: `monitoring/rag-dashboard.json`

Proof checks:

- Import dashboard JSON in Grafana.
- Verify panels render latency/requests/health metrics.

## Important note about “working” state

- Local Docker currently proves the RAG app path is working.
- Jenkins/Prometheus/Grafana are configured in repo; they are “running” only after you deploy/start those services in your environment.

## Recommended acceptance checklist

- [ ] `./scripts/e2e_gemini.sh` returns PASS
- [ ] `/query` answer is non-empty and context-grounded
- [ ] Eval gate passes at chosen threshold
- [ ] Jenkins pipeline run is green
- [ ] Prometheus target is UP
- [ ] Grafana dashboard renders metrics
