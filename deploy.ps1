# DEVOPS-FRIENDLY DEPLOYMENT SCRIPT
param(
    [switch]$SkipTests,
    [switch]$SkipBuild,
    [string]$Environment = "production",
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

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
            Write-ColorOutput "✅ $Name`: $($response.StatusCode) - SUCCESS" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ $Name`: $($response.StatusCode) - FAIL (Expected: 200)" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "❌ $Name`: FAILED - $($_.Exception.Message)" "Red"
        return $false
    }
}

# Function to wait for service
function Wait-ForService {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$MaxWait = 120,
        [int]$Interval = 5
    )
    
    $waitTime = 0
    Write-ColorOutput "⏳ Waiting for $ServiceName..." "Yellow"
    
    while ($waitTime -lt $MaxWait) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                $healthData = $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($healthData -and $healthData.status -eq "healthy") {
                    Write-ColorOutput "✅ $ServiceName is healthy and ready" "Green"
                    return $true
                }
            }
        } catch {
            # Continue waiting
        }
        Write-ColorOutput "⏳ $ServiceName... ($waitTime/$MaxWait seconds)" "Yellow"
        Start-Sleep -Seconds $Interval
        $waitTime += $Interval
    }
    
    Write-ColorOutput "❌ $ServiceName failed to start within $MaxWait seconds" "Red"
    return $false
}

# Main deployment script
Write-ColorOutput "🚀 DEVOPS-FRIENDLY COMMIT TRACKER SERVICE DEPLOYMENT" "Yellow"
Write-ColorOutput "Environment: $Environment" "Cyan"
Write-ColorOutput "Skip Tests: $SkipTests" "Cyan"
Write-ColorOutput "Skip Build: $SkipBuild" "Cyan"
Write-ColorOutput "Verbose: $Verbose" "Cyan"

# Step 1: Pre-deployment checks
Write-ColorOutput "`n🔍 Step 1: Pre-deployment checks..." "Cyan"

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-ColorOutput "✅ Docker is running" "Green"
} catch {
    Write-ColorOutput "❌ Docker is not running. Please start Docker first." "Red"
    exit 1
}

# Check if required files exist
$requiredFiles = @("requirements.txt", "Dockerfile", "docker-compose.yml", "src/main.py")
foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        Write-ColorOutput "❌ Required file not found: $file" "Red"
        exit 1
    }
}
Write-ColorOutput "✅ All required files found" "Green"

# Verify critical dependencies
$requirements = Get-Content "requirements.txt"
if ($requirements -notcontains "aiosqlite==0.19.0") {
    Write-ColorOutput "❌ CRITICAL: aiosqlite==0.19.0 missing from requirements.txt!" "Red"
    exit 1
}
if ($requirements -notcontains "psutil==5.9.6") {
    Write-ColorOutput "❌ CRITICAL: psutil==5.9.6 missing from requirements.txt!" "Red"
    exit 1
}

# Verify critical environment variables
$compose = Get-Content "docker-compose.yml"
if ($compose -notcontains "SECRET_KEY=your-secret-key-change-in-production") {
    Write-ColorOutput "❌ CRITICAL: SECRET_KEY missing from docker-compose.yml!" "Red"
    exit 1
}
if ($compose -notcontains "condition: service_healthy") {
    Write-ColorOutput "❌ CRITICAL: condition: service_healthy missing from docker-compose.yml!" "Red"
    exit 1
}

Write-ColorOutput "✅ All critical configurations verified" "Green"

# Step 2: Run tests (if not skipped)
if (!$SkipTests) {
    Write-ColorOutput "`n🧪 Step 2: Running tests..." "Cyan"
    try {
        docker-compose run --rm commit-tracker-service python -m pytest tests/ -v
        Write-ColorOutput "✅ All tests passed" "Green"
    } catch {
        Write-ColorOutput "❌ Tests failed. Use -SkipTests to bypass." "Red"
        exit 1
    }
} else {
    Write-ColorOutput "`n⏭️ Step 2: Skipping tests (--SkipTests flag used)" "Yellow"
}

# Step 3: Clean environment
Write-ColorOutput "`n🧹 Step 3: Cleaning environment..." "Cyan"
docker-compose down --remove-orphans
if ($Environment -eq "production") {
    docker container prune -f
    docker image prune -f
    docker volume prune -f
}

# Step 4: Build and deploy
Write-ColorOutput "`n🔨 Step 4: Building and deploying..." "Cyan"
if (!$SkipBuild) {
    docker-compose up -d --build --force-recreate
} else {
    docker-compose up -d --force-recreate
}

# Step 5: Wait for services with progress
Write-ColorOutput "`n⏳ Step 5: Waiting for services..." "Cyan"

# Wait for PostgreSQL
$postgresReady = Wait-ForService -Url "http://localhost:5433" -ServiceName "PostgreSQL" -MaxWait 120
if (!$postgresReady) {
    Write-ColorOutput "❌ PostgreSQL failed to start" "Red"
    Write-ColorOutput "📋 PostgreSQL logs:" "Yellow"
    docker logs commit-tracker-postgres --tail 20
    exit 1
}

# Wait for application
$appReady = Wait-ForService -Url "http://localhost:8001/health" -ServiceName "Application" -MaxWait 90
if (!$appReady) {
    Write-ColorOutput "❌ Application failed to start" "Red"
    Write-ColorOutput "📋 Application logs:" "Yellow"
    docker logs commit-tracker-service --tail 30
    exit 1
}

# Step 6: Comprehensive endpoint testing
Write-ColorOutput "`n🧪 Step 6: Testing all endpoints..." "Cyan"

$endpoints = @(
    @{Name="Health Check"; URL="http://localhost:8001/health"; ExpectedStatus=200},
    @{Name="Readiness Probe"; URL="http://localhost:8001/health/ready"; ExpectedStatus=200},
    @{Name="Liveness Probe"; URL="http://localhost:8001/health/live"; ExpectedStatus=200},
    @{Name="Root Endpoint"; URL="http://localhost:8001/"; ExpectedStatus=200},
    @{Name="Git Status"; URL="http://localhost:8001/api/git/status"; ExpectedStatus=200},
    @{Name="System Info"; URL="http://localhost:8001/api/system"; ExpectedStatus=200},
    @{Name="Commits"; URL="http://localhost:8001/api/commits"; ExpectedStatus=200},
    @{Name="Metrics"; URL="http://localhost:8001/metrics"; ExpectedStatus=200},
    @{Name="Debug Info"; URL="http://localhost:8001/debug"; ExpectedStatus=200}
)

$passedTests = 0
$totalTests = $endpoints.Count

foreach ($endpoint in $endpoints) {
    $success = Test-Endpoint -Url $endpoint.URL -Name $endpoint.Name
    if ($success) {
        $passedTests++
    }
}

# Step 7: Deployment summary
Write-ColorOutput "`n📊 Step 7: Deployment Summary" "Cyan"
Write-ColorOutput "Tests Passed: $passedTests/$totalTests" $(if ($passedTests -eq $totalTests) { "Green" } else { "Red" })

if ($passedTests -eq $totalTests) {
    Write-ColorOutput "`n🎉 DEPLOYMENT SUCCESSFUL!" "Green"
    Write-ColorOutput "🌐 Service URL: http://localhost:8001" "Green"
    Write-ColorOutput " Health Check: http://localhost:8001/health" "Green"
    Write-ColorOutput "📚 API Docs: http://localhost:8001/api/docs" "Green"
    Write-ColorOutput "📊 Metrics: http://localhost:8001/metrics" "Green"
    Write-ColorOutput "🔧 System Info: http://localhost:8001/api/system" "Green"
    
    # Create deployment success file
    @"
DEPLOYMENT SUCCESS
==================
Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Environment: $Environment
Tests Passed: $passedTests/$totalTests
Service URL: http://localhost:8001
Health Check: http://localhost:8001/health
API Docs: http://localhost:8001/api/docs
Metrics: http://localhost:8001/metrics
"@ | Out-File -FilePath "deployment_success.txt" -Encoding UTF8
    
} else {
    Write-ColorOutput "`n❌ DEPLOYMENT FAILED!" "Red"
    Write-ColorOutput "Some endpoints are not working properly." "Red"
    
    # Create deployment failure file
    @"
DEPLOYMENT FAILED
=================
Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Environment: $Environment
Tests Passed: $passedTests/$totalTests
Failed Tests: $($totalTests - $passedTests)
"@ | Out-File -FilePath "deployment_failure.txt" -Encoding UTF8
    
    exit 1
}

# Step 8: Show container status
Write-ColorOutput "`n📋 Container Status:" "Cyan"
docker-compose ps

# Step 9: Show service logs (last 10 lines)
Write-ColorOutput "`n📋 Recent Service Logs:" "Cyan"
docker logs commit-tracker-service --tail 10

Write-ColorOutput "`n🎯 DEVOPS-FRIENDLY DEPLOYMENT COMPLETED!" "Green"
Write-ColorOutput "All endpoints are working perfectly!" "Green"
