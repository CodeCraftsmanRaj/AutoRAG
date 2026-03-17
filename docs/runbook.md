# Runbook

## Health checks

- API health: `GET /health`
- Query smoke test: `POST /query`
- Rebuild index: `POST /ingest` with `{ "rebuild": true }`

## Deployment rollback

- `helm rollback auto-rag <revision> -n rag`

## Troubleshooting

- Low faithfulness score: verify docs freshness and chunking parameters.
- Empty retrieval context: verify PVC mount and vector DB path.
- API failures: check pod logs and secret injection.

