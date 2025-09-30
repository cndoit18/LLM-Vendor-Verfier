# LLM Vendor Verifier

本项目为 [K2-Vendor-Verifier](https://github.com/MoonshotAI/K2-Vendor-Verfier) 的衍生版本，补全了测试集，并且增加了很多供应商的兼容性代码（比如适配了 openrouter 的 provider 让大家可以选择 vendor）

<video src="./assets/images/logo.mp4" autoplay loop muted></video>

## 评估榜单

### Model: `deepseek/deepseek-v3.2-exp`

| Vendor | Success Count | Failure Count | Finish Stop | Finish Tool Calls | Finish Others | Schema Validation Errors | **Successful Tool Call Count** | **Similarity to Official** |
|--------|---------------|---------------|-------------|-------------------|---------------|--------------------------|-------------------------------|---------------------------|
| deepseek-official | 511 | 1 | 60 | 451 | 0 | 4 | **447** | **1.0000** |
| openrouter-novita | 512 | 0 | 77 | 435 | 0 | 1 | **434** | **0.9765** |
| ppio | 511 | 0 | 78 | 433 | 0 | 1 | **432** | **0.9740** |

## 评估结果

详细的评估指标如下：

| 指标名称                           | 描述                                                                             |
| ---------------------------------- | -------------------------------------------------------------------------------- |
| Count of Finish Reason: stop       | finish_reason 为 "stop" 的响应数量                                               |
| Count of Finish Reason: tool_calls | finish_reason 为 "tool_calls" 的响应数量                                         |
| Count of Finish Reason: others     | finish_reason 既不是 "stop" 也不是 "tool_calls" 的响应数量                       |
| Schema Validation Error Count      | 在 "tool_calls" 响应中，未通过 schema 验证的数量                                 |
| Successful Tool Call Count         | 在 "tool_calls" 响应中，通过 schema 验证的数量                                   |
| Similarity to Official API         | 1-Euclidean 供应商指标值与官方 Moonshot AI API 之间的欧氏距离/estimated_max_distance(datasets_num) |


## 自行验证

要使用样本数据运行评估工具，请使用以下命令：

```bash
python tool_calls_eval.py ./datasets/tool-call-single-content-dataset.jsonl \
    --model kimi-k2-0905-preview \
    --base-url https://api.moonshot.cn/v1 \
    --api-key YOUR_API_KEY \
    --concurrency 5 \
    --output ./benchmark-result/results-{vendor-name}-{model-name}.jsonl \
    --summary ./benchmark-result/summary-{vendor-name}-{model-name}.json
```

- `./datasets/tool-call-single-content-dataset.jsonl`: JSONL 格式的测试集文件路径
- `--model`: 模型名称（例如 kimi-k2-0905-preview）
- `--base-url`: API 端点 URL (注意格式采用的是 OpenAI 兼容格式, 用了 OpenAI 的 SDK. 会自动补全 URL 的 chat/completions)
- `--api-key`: 用于身份验证的 API 密钥（或设置 OPENAI_API_KEY 环境变量）
- `--concurrency`: 最大并发请求数（默认：5）
- `--output`: 保存详细结果的路径（默认：results.jsonl, 如果提交 PR, 请按照格式 results-{vendor-name}-{model-name}.jsonl 提交）
- `--summary`: 保存汇总摘要的路径（默认：summary.json, 如果提交 PR, 请按照格式 summary-{vendor-name}-{model-name}.json 提交）
- `--timeout`: 每个请求的超时时间（秒）（默认：600）
- `--retries`: 失败时的重试次数（默认：3）
- `--extra-body`: 作为字符串的额外 JSON 内容，合并到每个请求负载中（例如 '{"temperature":0.6}'）
- `--incremental`: 增量模式，仅重新运行失败的请求
- `--filter-unsupported-roles`: 过滤不支持的消息角色（tool、_input）和带有 tool_calls 的 assistant 消息。在测试不支持完整工具调用对话历史的 API 时使用此选项
- `--vendor`: 指定供应商名称（例如 'openrouter'）。在使用供应商特定功能时必需
- `--provider-order`: 用于 OpenRouter 的 provider 路由的逗号分隔的 provider 名称列表（例如 'openai,together'）。仅在 --vendor 设置为 'openrouter' 时使用


### 通过 OpenRouter 测试

要通过 OpenRouter 测试供应商，请使用 `--vendor` 和 `--provider-order` 参数：

```bash
python tool_calls_eval.py samples.jsonl \
    --model kimi-k2-0905-preview \
    --base-url https://openrouter.ai/api/v1 \
    --api-key YOUR_OPENROUTER_API_KEY \
    --vendor openrouter \
    --provider-order "novita,siliconflow" \
    --concurrency 5 \
    --output results-openrouter.jsonl \
    --summary summary-openrouter.json
```

这将使用 OpenRouter 的 provider 路由按顺序优先使用指定的 provider。如果所有指定的 provider 都不可用，OpenRouter 将回退到其他可用的 provider。

**仅针对特定 provider：**

如果您想测试特定的 provider 而不使用回退，可以指定单个 provider：

```bash
python tool_calls_eval.py samples.jsonl \
    --model kimi-k2-0905-preview \
    --base-url https://openrouter.ai/api/v1 \
    --api-key YOUR_OPENROUTER_API_KEY \
    --vendor openrouter \
    --provider-order "novita" \
    --concurrency 5
```

**注意：** `--vendor` 参数专门为 OpenRouter 设计。当设置 `--vendor openrouter` 时，provider 字段将自动添加到 API 请求中。对于其他 API 供应商，请不要使用此参数。

