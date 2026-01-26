# PowerShell script to start ZenKnowledgeForge services
# Run this before executing the main application

Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ZenKnowledgeForge - Service Startup Script              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if Docker Desktop is running
Write-Host "Checking Docker service..." -ForegroundColor Yellow

try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker is running" -ForegroundColor Green
    } else {
        throw "Docker not responding"
    }
} catch {
    Write-Host "✗ Docker is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    Write-Host "After Docker starts, run this script again." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Start docker-compose services
Write-Host ""
Write-Host "Starting Docker Compose services..." -ForegroundColor Yellow

try {
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker Compose services started" -ForegroundColor Green
    } else {
        throw "docker-compose failed"
    }
} catch {
    Write-Host "✗ Failed to start services" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Wait for Ollama to be ready
Write-Host ""
Write-Host "Waiting for Ollama to be ready..." -ForegroundColor Yellow

$maxAttempts = 30
$attempt = 0
$ollamaReady = $false

while ($attempt -lt $maxAttempts -and -not $ollamaReady) {
    $attempt++
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 2 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            $ollamaReady = $true
            Write-Host "✓ Ollama is ready" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Attempt $attempt/$maxAttempts..." -NoNewline
        Start-Sleep -Seconds 2
        Write-Host " retrying" -ForegroundColor Gray
    }
}

if (-not $ollamaReady) {
    Write-Host "✗ Ollama did not become ready in time" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs ollama" -ForegroundColor Yellow
    exit 1
}

# Check for downloaded models
Write-Host ""
Write-Host "Checking for required models..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET
    $models = $response.models
    
    $requiredModels = @(
        "llama3.1:8b-instruct-q4_K_M",
        "mistral:7b-instruct",
        "qwen2.5:7b-instruct-q4_K_M",
        "gemma2:9b-instruct-q4_K_M",
        "phi3.5:3.8b-mini-instruct-q4_K_M"
    )
    
    $missingModels = @()
    
    foreach ($reqModel in $requiredModels) {
        $found = $false
        foreach ($model in $models) {
            if ($model.name -eq $reqModel) {
                $found = $true
                Write-Host "  ✓ $reqModel" -ForegroundColor Green
                break
            }
        }
        
        if (-not $found) {
            Write-Host "  ✗ $reqModel - MISSING" -ForegroundColor Red
            $missingModels += $reqModel
        }
    }
    
    if ($missingModels.Count -gt 0) {
        Write-Host ""
        Write-Host "⚠ Missing models detected!" -ForegroundColor Yellow
        Write-Host "Download them with: bash scripts/pull_models.sh" -ForegroundColor Yellow
        Write-Host "Or manually: ollama pull <model_name>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Note: This will download ~35GB of models" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "✓ All required models are available" -ForegroundColor Green
    }
    
} catch {
    Write-Host "⚠ Could not check models" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Services Ready!                                         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run ZenKnowledgeForge:" -ForegroundColor Green
Write-Host "  python run_zen.py 'Your query here' --mode research" -ForegroundColor White
Write-Host ""
Write-Host "To stop services later:" -ForegroundColor Yellow
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
