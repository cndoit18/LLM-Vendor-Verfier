base_url="https://api.ppinfra.com/openai"
api_key="<您的 API Key>"

curl "$base_url/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $api_key" \
  -d @- << 'EOF'
{
    "model": "deepseek/deepseek-v3.2-exp",
    "messages": [
        
        {
            "role": "user",
            "content": "Hi there!"
        }
    ],
    "response_format": { "type": "text" }
}
EOF
  

PPIO: sk_ynQqBlF5zbHVcvH1Oyw_CJuHn_J-hIMtOnvR5Ci3FXg
deepseek: sk-7329131ba44c43f98010f0744f262400


uv run python ./tool_calls_eval.py samples.jsonl \
    --model "deepseek/deepseek-v3.2-exp" \
    --base-url "https://api.ppinfra.com/openai/v1" \
    --api-key "sk_ynQqBlF5zbHVcvH1Oyw_CJuHn_J-hIMtOnvR5Ci3FXg" \
    --concurrency 10 \
    --output benchmark-result/results-ppio-deepseek-v3.2-exp.jsonl \
    --summary benchmark-result/summary-ppio-deepseek-v3.2-exp.json

uv run python ./tool_calls_eval.py samples-no-stream.jsonl \
    --model "deepseek/deepseek-v3.2-exp" \
    --base-url "https://api.ppinfra.com/openai/v1" \
    --api-key "sk_ynQqBlF5zbHVcvH1Oyw_CJuHn_J-hIMtOnvR5Ci3FXg" \
    --concurrency 10 \
    --output benchmark-result/results-ppio-deepseek-v3.2-exp.jsonl \
    --summary benchmark-result/summary-ppio-deepseek-v3.2-exp.json


## PPIO

uv run python ./tool_calls_eval.py ./datasets/tool-call-single-content-dataset.jsonl \
    --model "deepseek/deepseek-v3.2-exp" \
    --base-url "https://api.ppinfra.com/openai/v1" \
    --api-key "sk_ynQqBlF5zbHVcvH1Oyw_CJuHn_J-hIMtOnvR5Ci3FXg" \
    --filter-unsupported-roles \
    --concurrency 5 \
    --output benchmark-result/results-ppio-2-deepseek-v3.2-exp.jsonl \
    --summary benchmark-result/summary-ppio-2-deepseek-v3.2-exp.json



## DeepSeek



uv run python ./tool_calls_eval.py ./datasets/tool-call-single-content-dataset.jsonl \
    --model "deepseek-reasoner" \
    --base-url "https://api.deepseek.com/v1" \
    --api-key "sk-7329131ba44c43f98010f0744f262400" \
    --filter-unsupported-roles \
    --concurrency 5 \
    --output benchmark-result/results-deepseek-official-deepseek-v3.2-exp.jsonl \
    --summary benchmark-result/summary-deepseek-official-deepseek-v3.2-exp.json


## openrouter


uv run python ./tool_calls_eval.py samples-deepseek.jsonl \
    --model "deepseek/deepseek-v3.2-exp" \
    --base-url "https://openrouter.ai/api/v1" \
    --api-key "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" \
    --filter-unsupported-roles \
    --concurrency 5 \
    --vendor openrouter \
    --provider-order "novita" \
    --output benchmark-result/results-openrouter-novita-deepseek-v3.2-exp.jsonl \
    --summary benchmark-result/summary-openrouter-novita-deepseek-v3.2-exp.json




base_url="https://api.ppinfra.com/openai"
api_key="sk_ynQqBlF5zbHVcvH1Oyw_CJuHn_J-hIMtOnvR5Ci3FXg"

curl "$base_url/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $api_key" \
  -d @- << 'EOF'
{
    "model": "deepseek/deepseek-v3.2-exp",
    "messages": [
        
        {
            "role": "user",
            "content": "Hi there!"
        }
    ],
    "response_format": { "type": "text" }
}
EOF
  