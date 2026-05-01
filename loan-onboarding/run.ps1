Write-Host "Starting Loan Wizard Hackathon Prototype..." -ForegroundColor Green

# Start Backend
Start-Job -Name Backend -ScriptBlock {
    Set-Location -Path "$using:PWD"
    .\venv\Scripts\Activate.ps1
    Set-Location -Path backend
    uvicorn main:app --reload --port 8000
}

# Start Frontend
Start-Job -Name Frontend -ScriptBlock {
    Set-Location -Path "$using:PWD"
    Set-Location -Path frontend
    npm run dev -- -p 3000
}

Write-Host "Services are booting up in the background."
Write-Host "1. Frontend will be accessible at http://localhost:3000"
Write-Host "2. Backend will be serving ML inferences at http://localhost:8000"
Write-Host "Checking job status. Run 'Receive-Job -Name Frontend' for frontend logs..."

Get-Job | Wait-Job
