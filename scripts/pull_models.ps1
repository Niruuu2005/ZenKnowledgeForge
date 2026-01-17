# Requires: Ollama installed and running (default: http://localhost:11434)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/pull_models.ps1
# Optional: set $env:OLLAMA_HOST to override host (e.g., http://127.0.0.1:11434)

$ErrorActionPreference = 'Stop'

# Configure host and models
$ollamaHost = $env:OLLAMA_HOST
if ([string]::IsNullOrWhiteSpace($ollamaHost)) {
    $ollamaHost = 'http://localhost:11434'
}

$models = @(
    'llama3.1:8b-instruct-q4_K_M'
    'qwen2.5:7b-instruct-q4_K_M'
    'gemma2:9b-instruct-q4_K_M'
    'phi3.5:3.8b-mini-instruct-q4_K_M'
    'qwen2.5:14b-instruct-q4_K_M'
)

$succeeded = @()
$failed = @()

Write-Host "ZenKnowledgeForge Model Downloader" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "This will download ~35GB of models. Ensure you have space." -ForegroundColor Yellow
Write-Host "Ollama host: $ollamaHost" -ForegroundColor Yellow

# Basic Ollama health check
try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri "$ollamaHost/api/tags" -Method GET -TimeoutSec 5
    if ($resp.StatusCode -ne 200) {
        throw "Unexpected status code: $($resp.StatusCode)"
    }
} catch {
    Write-Host "Ollama is not reachable at $ollamaHost. Start Ollama (or docker-compose up) and retry." -ForegroundColor Red
    exit 1
}

Write-Host "Models to download:" -ForegroundColor Cyan
$models | ForEach-Object { Write-Host "  - $_" }

$confirm = Read-Host "Continue? (y/n)"
if ($confirm -notmatch '^[Yy]$') {
    Write-Host "Cancelled." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting downloads..." -ForegroundColor Green

foreach ($model in $models) {
    Write-Host "Pulling $model..." -ForegroundColor Cyan
    $proc = Start-Process -FilePath "ollama" -ArgumentList @('pull', $model) -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Write-Host "Failed to download $model (exit code $($proc.ExitCode)). Verify the model tag exists or pull a supported variant." -ForegroundColor Red
        $failed += $model
        continue
    }
    $succeeded += $model
    Write-Host "$model downloaded successfully" -ForegroundColor Green
    Write-Host ""
}

if ($failed.Count -eq 0) {
    Write-Host "All models downloaded successfully!" -ForegroundColor Green
} else {
    Write-Host "Completed with failures." -ForegroundColor Yellow
}

if ($succeeded.Count -gt 0) {
    Write-Host "Downloaded:" -ForegroundColor Green
    $succeeded | ForEach-Object { Write-Host "  - $_" }
}

if ($failed.Count -gt 0) {
    Write-Host "Failed:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" }
    Write-Host "Tip: run 'ollama list' to see available tags and adjust scripts/pull_models.ps1 accordingly." -ForegroundColor Yellow
    exit 1
}

Write-Host 'You can now run: python -m zen "your brief here"' -ForegroundColor Yellow
