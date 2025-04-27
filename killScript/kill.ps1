Write-Host "🛑 Killing all React (node) and Python dev threads..."

taskkill /IM node.exe /F > $null 2>&1
taskkill /IM python.exe /F > $null 2>&1

Write-Host "✅ All dev threads cleaned up."
# uvicorn backend.main:app --reload

# ON PI: uvicorn backend.main:app --host 0.0.0.0 --port 8000
