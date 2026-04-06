#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/6] Rebuild + recreate"
docker compose down --remove-orphans >/dev/null 2>&1 || true
docker compose up -d --build --force-recreate

echo "[2/6] Wait for health"
for i in {1..40}; do
  if curl -fsS http://localhost:8000/health >/tmp/arag_health.json; then
    cat /tmp/arag_health.json
    break
  fi
  sleep 2
  if [[ "$i" == "40" ]]; then
    docker compose logs --tail=120 rag-app || true
    echo "Health check failed"
    exit 1
  fi
done

echo "[3/6] Rebuild vector index"
curl -fsS -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"paths":["/app/docs"],"rebuild":true}'
echo

echo "[4/6] Query smoke test"
curl -fsS -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the support SLA for critical incidents?"}'
echo

echo "[5/6] Dataset evaluation"
set +e
docker compose exec -T rag-app python -m app.eval
EVAL_CODE=$?
set -e

if [[ $EVAL_CODE -ne 0 ]]; then
  echo "[6/6] Evaluation failed. If query works but score is slightly low, reduce RAG_SCORE_THRESHOLD for local heuristic mode (e.g. 0.70)."
  exit $EVAL_CODE
fi

echo "[6/6] PASS"
