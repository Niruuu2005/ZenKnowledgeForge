# PowerShell script to run ZenKnowledgeForge with proper venv
# This runs in the background without interference from the terminal

Write-Host "[*] Activating venv..." -ForegroundColor Cyan
& "$PSScriptRoot\venv\Scripts\Activate.ps1"

Write-Host "[*] Starting ZenKnowledgeForge..." -ForegroundColor Cyan
python run_zen.py "What are the fundamental principles of deep learning?" --mode research

Write-Host "`n[*] Execution complete" -ForegroundColor Green
