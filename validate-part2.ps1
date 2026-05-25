#!/usr/bin/env pwsh

<#
.SYNOPSIS
Comprehensive validation script for Part 2 completion
.DESCRIPTION
Tests all critical systems and configurations to verify Part 2 is complete
#>

Write-Output ""
Write-Output "╔═══════════════════════════════════════════════════════════════╗"
Write-Output "║          PART 2 VALIDATION - COMPREHENSIVE CHECK             ║"
Write-Output "╚═══════════════════════════════════════════════════════════════╝"
Write-Output ""

$tests_passed = 0
$tests_failed = 0

function Test-Condition {
    param(
        [string]$Description,
        [scriptblock]$TestBlock,
        [string]$ErrorMessage
    )
    
    try {
        $result = & $TestBlock
        if ($result) {
            Write-Output "✅ $Description"
            $script:tests_passed++
            return $true
        } else {
            Write-Output "❌ $Description"
            if ($ErrorMessage) { Write-Output "   └─ $ErrorMessage" }
            $script:tests_failed++
            return $false
        }
    } catch {
        Write-Output "❌ $Description"
        Write-Output "   └─ Error: $($_.Exception.Message)"
        $script:tests_failed++
        return $false
    }
}

# ═══════════════════════════════════════════════════════════════
Write-Output "1️⃣ DOCKER & CONTAINER TESTS"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Test-Condition "Docker daemon is running" {
    $null = docker ps 2>$null
    $?
}

Test-Condition "pm-backend image exists" {
    docker images --filter "reference=pm-backend" --quiet | Measure-Object -Line | Select-Object -ExpandProperty Lines -gt 0
}

Test-Condition "pm-backend-1 container exists" {
    docker ps -a --filter "name=pm-backend-1" --quiet | Measure-Object -Line | Select-Object -ExpandProperty Lines -gt 0
}

Test-Condition "pm-backend-1 container is running" {
    $status = docker inspect pm-backend-1 --format='{{.State.Running}}' 2>$null
    $status -eq "true"
}

Test-Condition "Container health check is passing" {
    $health = docker inspect pm-backend-1 --format='{{.State.Health.Status}}' 2>$null
    $health -eq "healthy"
}

# ═══════════════════════════════════════════════════════════════
Write-Output ""
Write-Output "2️⃣ PORT & NETWORK TESTS"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Test-Condition "Port 8000 is listening" {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 5
        $response.StatusCode -eq 200
    } catch {
        $false
    }
}

Test-Condition "Server responds within 2 seconds" {
    $start = Get-Date
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 5
    $elapsed = (Get-Date) - $start
    $elapsed.TotalSeconds -lt 2
}

# ═══════════════════════════════════════════════════════════════
Write-Output ""
Write-Output "3️⃣ API ENDPOINTS TESTS"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Test-Condition "GET /api/health returns 200" {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing
    $response.StatusCode -eq 200
}

Test-Condition "Health response contains 'status: ok'" {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing
    $response.Content -match '"status"\s*:\s*"ok"'
}

Test-Condition "Health response contains version" {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing
    $response.Content -match '"version"\s*:\s*"0\.1\.0"'
}

Test-Condition "GET /docs (Swagger) returns 200" {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing
    $response.StatusCode -eq 200
}

Test-Condition "GET /openapi.json returns 200" {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/openapi.json" -UseBasicParsing
    $response.StatusCode -eq 200
}

Test-Condition "CORS headers are present" {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing
    $response.Headers.ContainsKey('Access-Control-Allow-Origin') -or $response.Headers.ContainsKey('access-control-allow-origin')
}

# ═══════════════════════════════════════════════════════════════
Write-Output ""
Write-Output "4️⃣ DATABASE TESTS"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Test-Condition "Database file exists in container" {
    docker exec pm-backend-1 test -f data/app.db 2>$null
    $?
}

Test-Condition "Database file size is > 0 bytes (or freshly created)" {
    $fileInfo = docker exec pm-backend-1 ls -lh data/app.db 2>$null
    $fileInfo -match 'app\.db'
}

Test-Condition "Database directory exists" {
    docker exec pm-backend-1 test -d data 2>$null
    $?
}

# ═══════════════════════════════════════════════════════════════
Write-Output ""
Write-Output "5️⃣ CONFIGURATION TESTS"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Test-Condition ".env file exists in project root" {
    Test-Path ".env" -PathType Leaf
}

Test-Condition ".env contains OPENROUTER_API_KEY" {
    (Get-Content ".env" -ErrorAction SilentlyContinue) -match "OPENROUTER_API_KEY"
}

Test-Condition "docker-compose.yml exists" {
    Test-Path "docker-compose.yml" -PathType Leaf
}

Test-Condition "Dockerfile exists" {
    Test-Path "Dockerfile" -PathType Leaf
}

Test-Condition "pyproject.toml exists" {
    Test-Path "backend/pyproject.toml" -PathType Leaf
}

Test-Condition "backend/app/main.py exists" {
    Test-Path "backend/app/main.py" -PathType Leaf
}

Test-Condition "backend/app/database.py exists" {
    Test-Path "backend/app/database.py" -PathType Leaf
}

# ═══════════════════════════════════════════════════════════════
Write-Output ""
Write-Output "6️⃣ SCRIPT FILES TESTS"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Test-Condition "scripts/start.ps1 exists" {
    Test-Path "scripts/start.ps1" -PathType Leaf
}

Test-Condition "scripts/stop.ps1 exists" {
    Test-Path "scripts/stop.ps1" -PathType Leaf
}

Test-Condition "scripts/start.bat exists" {
    Test-Path "scripts/start.bat" -PathType Leaf
}

Test-Condition "scripts/stop.bat exists" {
    Test-Path "scripts/stop.bat" -PathType Leaf
}

Test-Condition "scripts/start.sh exists" {
    Test-Path "scripts/start.sh" -PathType Leaf
}

Test-Condition "scripts/stop.sh exists" {
    Test-Path "scripts/stop.sh" -PathType Leaf
}

# ═══════════════════════════════════════════════════════════════
Write-Output ""
Write-Output "7️⃣ LOGS & HEALTH TESTS"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Test-Condition "Container logs show successful startup" {
    $logs = docker logs pm-backend-1 2>$null
    $logs -match "Application startup complete"
}

Test-Condition "No critical errors in logs" {
    $logs = docker logs pm-backend-1 2>$null
    -not ($logs -match "ERROR|CRITICAL|ModuleNotFoundError|ImportError")
}

Test-Condition "Uvicorn is running in container" {
    $logs = docker logs pm-backend-1 2>$null
    $logs -match "Uvicorn running"
}

# ═══════════════════════════════════════════════════════════════
Write-Output ""
Write-Output "╔═══════════════════════════════════════════════════════════════╗"
Write-Output "║                    FINAL TEST RESULTS                        ║"
Write-Output "╚═══════════════════════════════════════════════════════════════╝"
Write-Output ""

$total = $tests_passed + $tests_failed
$percentage = if ($total -gt 0) { ($tests_passed / $total) * 100 } else { 0 }

Write-Output "📊 Summary:"
Write-Output "   ✅ Passed:  $tests_passed"
Write-Output "   ❌ Failed:  $tests_failed"
Write-Output "   📈 Total:   $total"
Write-Output "   🎯 Score:   {0:F1}%" -f $percentage
Write-Output ""

if ($tests_failed -eq 0) {
    Write-Output "╔═══════════════════════════════════════════════════════════════╗"
    Write-Output "║  ✅ ALL TESTS PASSED - PART 2 IS COMPLETE & OPERATIONAL      ║"
    Write-Output "╚═══════════════════════════════════════════════════════════════╝"
    exit 0
} elseif ($tests_failed -le 2) {
    Write-Output "⚠️  MINOR ISSUES DETECTED - Most systems operational"
    exit 1
} else {
    Write-Output "❌ CRITICAL ISSUES DETECTED - Please review failures above"
    exit 2
}
