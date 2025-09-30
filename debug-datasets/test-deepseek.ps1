# DeepSeek Tool Call Testing Script (PowerShell)
# This script runs tests against both official and vendor APIs for comparison

param(
    [string]$DeepSeekApiKey = $env:DEEPSEEK_API_KEY,
    [string]$VendorApiKey = $env:VENDOR_API_KEY,
    [string]$VendorBaseUrl = $env:VENDOR_BASE_URL,
    [string]$VendorModel = $env:VENDOR_MODEL
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DeepSeek Tool Call Validation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$SamplesFile = "samples-deepseek.jsonl"
$Concurrency = 5
$Temperature = 0.0

# Check if samples file exists
if (-not (Test-Path $SamplesFile)) {
    Write-Host "Error: $SamplesFile not found!" -ForegroundColor Red
    Write-Host "Please run: uv run convert_dataset.py first" -ForegroundColor Yellow
    exit 1
}

# Function to run test
function Run-Test {
    param(
        [string]$Provider,
        [string]$BaseUrl,
        [string]$ApiKey,
        [string]$Model
    )
    
    Write-Host "Testing: $Provider" -ForegroundColor Green
    Write-Host "Model: $Model"
    Write-Host "Base URL: $BaseUrl"
    Write-Host ""
    
    uv run tool_calls_eval.py `
        $SamplesFile `
        --model $Model `
        --base-url $BaseUrl `
        --api-key $ApiKey `
        --filter-unsupported-roles `
        --concurrency $Concurrency `
        --output "results-$Provider.jsonl" `
        --summary "summary-$Provider.json" `
        --timeout 600 `
        --retries 3
    
    Write-Host ""
    Write-Host "✓ Test completed for $Provider" -ForegroundColor Green
    Write-Host "Results: results-$Provider.jsonl"
    Write-Host "Summary: summary-$Provider.json"
    Write-Host ""
}

# Test Official DeepSeek API
if ($DeepSeekApiKey) {
    Write-Host "=== Testing Official DeepSeek API ===" -ForegroundColor Cyan
    Run-Test -Provider "deepseek-official" `
        -BaseUrl "https://api.deepseek.com/v1" `
        -ApiKey $DeepSeekApiKey `
        -Model "deepseek-chat"
} else {
    Write-Host "⚠ Skipping official DeepSeek test (DEEPSEEK_API_KEY not set)" -ForegroundColor Yellow
}

# Test Vendor API
if ($VendorApiKey -and $VendorBaseUrl) {
    Write-Host "=== Testing Vendor API ===" -ForegroundColor Cyan
    $ModelToUse = if ($VendorModel) { $VendorModel } else { "deepseek-chat" }
    Run-Test -Provider "vendor" `
        -BaseUrl $VendorBaseUrl `
        -ApiKey $VendorApiKey `
        -Model $ModelToUse
} else {
    Write-Host "⚠ Skipping vendor test (VENDOR_API_KEY or VENDOR_BASE_URL not set)" -ForegroundColor Yellow
}

# Generate comparison report
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Get-ChildItem -Path "summary-*.json" | ForEach-Object {
    Write-Host ""
    Write-Host "File: $($_.Name)" -ForegroundColor Yellow
    Write-Host "---"
    
    $data = Get-Content $_.FullName | ConvertFrom-Json
    $totalRequests = $data.success_count + $data.failure_count
    $successRate = if ($totalRequests -gt 0) { ($data.success_count / $totalRequests * 100) } else { 0 }
    $triggerRate = if ($data.success_count -gt 0) { ($data.finish_tool_calls / $data.success_count * 100) } else { 0 }
    $accuracy = if ($data.finish_tool_calls -gt 0) { ($data.successful_tool_call_count / $data.finish_tool_calls * 100) } else { 0 }
    
    Write-Host "Model: $($data.model)"
    Write-Host ("Success Rate: {0}/{1} ({2:N2}%)" -f $data.success_count, $totalRequests, $successRate)
    Write-Host ("Tool Call Trigger Rate: {0}/{1} ({2:N2}%)" -f $data.finish_tool_calls, $data.success_count, $triggerRate)
    Write-Host ("Tool Call Accuracy: {0}/{1} ({2:N2}%)" -f $data.successful_tool_call_count, $data.finish_tool_calls, $accuracy)
    Write-Host "Schema Validation Errors: $($data.schema_validation_error_count)"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "All tests completed!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
