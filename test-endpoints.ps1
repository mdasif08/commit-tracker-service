# QUICK ENDPOINT TESTING SCRIPT
Write-Host "🧪 TESTING ALL COMMIT TRACKER SERVICE ENDPOINTS" -ForegroundColor Yellow

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name,
        [int]$TimeoutSec = 10
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSec -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $Name`: $($response.StatusCode) - SUCCESS" -ForegroundColor Green
            
            # Show response preview for key endpoints
            if ($Name -eq "Health Check") {
                try {
                    $healthData = $response.Content | ConvertFrom-Json
                    Write-Host "   Status: $($healthData.status)" -ForegroundColor Green
                    Write-Host "   Database: $($healthData.database_status)" -ForegroundColor Green
                    Write-Host "   Git: $($healthData.git_status)" -ForegroundColor Green
                    Write-Host "   System: $($healthData.system_status)" -ForegroundColor Green
                } catch {
                    Write-Host "   Response: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))..." -ForegroundColor Green
                }
            }
            return $true
        } else {
            Write-Host "❌ $Name`: $($response.StatusCode) - FAIL (Expected: 200)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ $Name`: FAILED - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test all endpoints
$endpoints = @(
    @{Name="Health Check"; URL="http://localhost:8001/health"},
    @{Name="Readiness Probe"; URL="http://localhost:8001/health/ready"},
    @{Name="Liveness Probe"; URL="http://localhost:8001/health/live"},
    @{Name="Root Endpoint"; URL="http://localhost:8001/"},
    @{Name="Git Status"; URL="http://localhost:8001/api/git/status"},
    @{Name="System Info"; URL="http://localhost:8001/api/system"},
    @{Name="Commits"; URL="http://localhost:8001/api/commits"},
    @{Name="Metrics"; URL="http://localhost:8001/metrics"},
    @{Name="Debug Info"; URL="http://localhost:8001/debug"}
)

$passedTests = 0
$totalTests = $endpoints.Count

Write-Host "`n🧪 Testing $totalTests endpoints..." -ForegroundColor Cyan

foreach ($endpoint in $endpoints) {
    $success = Test-Endpoint -Url $endpoint.URL -Name $endpoint.Name
    if ($success) {
        $passedTests++
    }
    Start-Sleep -Milliseconds 500  # Small delay between tests
}

# Summary
Write-Host "`n📊 TEST RESULTS:" -ForegroundColor Cyan
Write-Host "Tests Passed: $passedTests/$totalTests" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Red" })

if ($passedTests -eq $totalTests) {
    Write-Host "`n🎉 ALL ENDPOINTS WORKING PERFECTLY!" -ForegroundColor Green
    Write-Host "✅ Service is 100% healthy and operational" -ForegroundColor Green
} else {
    Write-Host "`n❌ SOME ENDPOINTS FAILED!" -ForegroundColor Red
    Write-Host "Failed Tests: $($totalTests - $passedTests)" -ForegroundColor Red
}

# Show container status
Write-Host "`n📋 Container Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n🌐 Service URLs:" -ForegroundColor Cyan
Write-Host "Main Service: http://localhost:8001" -ForegroundColor Green
Write-Host "Health Check: http://localhost:8001/health" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8001/api/docs" -ForegroundColor Green
Write-Host "Metrics: http://localhost:8001/metrics" -ForegroundColor Green
