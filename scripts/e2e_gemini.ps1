#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

Write-Host "[1/6] Rebuild + recreate"
try {
    docker compose down --remove-orphans *> $null
} catch {
}
docker compose up -d --build --force-recreate

Write-Host "[2/6] Wait for health"
$healthPath = Join-Path $env:TEMP "arag_health.json"
for ($i = 1; $i -le 40; $i++) {
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/health" -OutFile $healthPath | Out-Null
        Get-Content $healthPath
        break
    } catch {
        Start-Sleep -Seconds 2
        if ($i -eq 40) {
            try {
                docker compose logs --tail=120 rag-app
            } catch {
            }
            Write-Host "Health check failed"
            exit 1
        }
    }
}

Write-Host "[3/6] Rebuild vector index"
$ingestBody = @{
    paths   = @("/app/docs")
    rebuild = $true
} | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/ingest" -ContentType "application/json" -Body $ingestBody
Write-Host ""

Write-Host "[4/6] Query smoke test"
$queryBody = @{
    question = "What is the support SLA for critical incidents?"
} | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/query" -ContentType "application/json" -Body $queryBody
Write-Host ""

Write-Host "[5/6] Dataset evaluation"
& docker compose exec -T rag-app python -m app.eval
$evalCode = $LASTEXITCODE

if ($evalCode -ne 0) {
    Write-Host "[6/6] Evaluation failed. If query works but score is slightly low, reduce RAG_SCORE_THRESHOLD for local heuristic mode (e.g. 0.70)."
    exit $evalCode
}

Write-Host "[6/6] PASS"