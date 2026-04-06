# UI Workflow Guide (What to do in each UI)

## 1) RAG API UI (Swagger)

Open: http://localhost:8000/docs

Use this UI for actual RAG operations:

1. `POST /ingest`
   - Body: `{ "paths": ["/app/docs"], "rebuild": true }`
   - Click **Execute**.
   - Success proof: response has `"status": "ingested"` and `chunks > 0`.

2. `POST /query`
   - Body example: `{ "question": "What is the support SLA for critical incidents?" }`
   - Click **Execute**.
   - Success proof: response has non-empty `answer` and non-empty `contexts`.

3. `GET /health`
   - Click **Execute**.
   - Success proof: `"status": "ok"`.

## 2) Jenkins UI

Open: http://localhost:8081

Use this UI for CI/CD pipeline checks.

1. Create a **Pipeline** job.
2. Point it to this repo and set script path to `jenkins/Jenkinsfile`.
3. Run build.
4. Success proof:
   - stages appear and run (checkout, scan, build, eval, deploy flow as configured)
   - build ends **Success**.

## 3) Prometheus UI

Open: http://localhost:9090

Use this UI for target + raw metrics checks.

1. Go to **Status → Targets**.
2. Confirm target `auto-rag-app` is **UP**.
3. Optional query examples:
   - `up{job="auto-rag-app"}`
   - `rate(http_requests_total{job="auto-rag-app"}[1m])`

## 4) Grafana UI

Open: http://localhost:3001
Login: `admin` / `admin`

Use this UI for dashboards and visualization.

1. Confirm datasource `Prometheus` exists.
2. Open dashboard `Auto-RAG Overview`.
3. Run a few `/query` calls from Swagger.
4. Success proof:
   - panels update (latency/requests/health trends).

## 5) SonarQube UI

Open: http://localhost:9000

Use this UI for static code quality status.

1. Create a project + token.
2. Use token in Jenkins credentials.
3. Run Jenkins scan stage.
4. Success proof:
   - project appears with analysis history
   - quality gate result visible in SonarQube.

## End-to-end proof sequence (UI + API)

1. In Swagger, run `/ingest`.
2. In Swagger, run `/query`.
3. In Prometheus, verify `auto-rag-app` target is UP.
4. In Grafana, verify dashboard graphs update.
5. In Jenkins, run pipeline.
6. In SonarQube, verify analysis report.
