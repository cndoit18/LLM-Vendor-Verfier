#!/bin/bash

# DeepSeek Tool Call Testing Script
# This script runs tests against both official and vendor APIs for comparison

set -e

echo "=========================================="
echo "DeepSeek Tool Call Validation"
echo "=========================================="
echo ""

# Configuration
SAMPLES_FILE="samples-deepseek.jsonl"
CONCURRENCY=5
TEMPERATURE=0.0

# Check if samples file exists
if [ ! -f "$SAMPLES_FILE" ]; then
    echo "Error: $SAMPLES_FILE not found!"
    echo "Please run: uv run convert_dataset.py first"
    exit 1
fi

# Function to run test
run_test() {
    local provider=$1
    local base_url=$2
    local api_key=$3
    local model=$4
    
    echo "Testing: $provider"
    echo "Model: $model"
    echo "Base URL: $base_url"
    echo ""
    
    uv run tool_calls_eval.py \
        "$SAMPLES_FILE" \
        --model "$model" \
        --base-url "$base_url" \
        --api-key "$api_key" \
        --filter-unsupported-roles \
        --concurrency "$CONCURRENCY" \
        --output "results-$provider.jsonl" \
        --summary "summary-$provider.json" \
        --timeout 600 \
        --retries 3
    
    echo ""
    echo "✓ Test completed for $provider"
    echo "Results: results-$provider.jsonl"
    echo "Summary: summary-$provider.json"
    echo ""
}

# Test Official DeepSeek API
if [ -n "$DEEPSEEK_API_KEY" ]; then
    echo "=== Testing Official DeepSeek API ==="
    run_test "deepseek-official" \
        "https://api.deepseek.com/v1" \
        "$DEEPSEEK_API_KEY" \
        "deepseek-chat"
else
    echo "⚠ Skipping official DeepSeek test (DEEPSEEK_API_KEY not set)"
fi

# Test Vendor API
if [ -n "$VENDOR_API_KEY" ] && [ -n "$VENDOR_BASE_URL" ]; then
    echo "=== Testing Vendor API ==="
    run_test "vendor" \
        "$VENDOR_BASE_URL" \
        "$VENDOR_API_KEY" \
        "${VENDOR_MODEL:-deepseek-chat}"
else
    echo "⚠ Skipping vendor test (VENDOR_API_KEY or VENDOR_BASE_URL not set)"
fi

# Generate comparison report
echo "=========================================="
echo "Test Summary"
echo "=========================================="

for summary_file in summary-*.json; do
    if [ -f "$summary_file" ]; then
        echo ""
        echo "File: $summary_file"
        echo "---"
        cat "$summary_file" | python3 -c "
import sys
import json
data = json.load(sys.stdin)
print(f\"Model: {data.get('model', 'N/A')}\")
print(f\"Success Rate: {data.get('success_count', 0)}/{data.get('success_count', 0) + data.get('failure_count', 0)} ({data.get('success_count', 0) / (data.get('success_count', 0) + data.get('failure_count', 1)) * 100:.2f}%)\")
print(f\"Tool Call Trigger Rate: {data.get('finish_tool_calls', 0)}/{data.get('success_count', 1)} ({data.get('finish_tool_calls', 0) / data.get('success_count', 1) * 100:.2f}%)\")
print(f\"Tool Call Accuracy: {data.get('successful_tool_call_count', 0)}/{data.get('finish_tool_calls', 1)} ({data.get('successful_tool_call_count', 0) / data.get('finish_tool_calls', 1) * 100:.2f}%)\")
print(f\"Schema Validation Errors: {data.get('schema_validation_error_count', 0)}\")
"
    fi
done

echo ""
echo "=========================================="
echo "All tests completed!"
echo "=========================================="
