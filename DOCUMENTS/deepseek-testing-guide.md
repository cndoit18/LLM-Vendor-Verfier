# DeepSeek Tool Call 测试指南

## 数据集准备

### 数据来源
- 原始数据集：`glaive_toolcall_zh` 1K 样本
- 转换后数据：`samples-deepseek.jsonl` (512条有效样本)

### 数据清洗说明

从1000条原始数据中提取了512条适合测试的样本，跳过了488条不适合的样本。

**筛选标准：**
1. ✅ 包含至少一次 function call
2. ✅ 有用户输入（human消息）
3. ✅ 工具定义完整且可解析
4. ❌ 跳过没有 function call 的纯对话
5. ❌ 跳过工具定义缺失或格式错误的样本

**转换规则：**
- `human` → `user`
- `gpt` → `assistant` (仅保留 function_call 之前的)
- `function_call` → 预期输出 (保存在 `_expected_function_call` 字段供参考)
- `observation` → 移除 (因为 DeepSeek 不支持 `tool` role)

### 数据格式示例

```json
{
  "model": "deepseek-chat",
  "messages": [
    {"role": "user", "content": "你好，我需要一个1到100之间的随机数。"}
  ],
  "tools": [{
    "type": "function",
    "function": {
      "name": "generate_random_number",
      "description": "在指定范围内生成一个随机数",
      "parameters": {
        "type": "object",
        "properties": {
          "min": {"type": "integer", "description": "最小值"},
          "max": {"type": "integer", "description": "最大值"}
        },
        "required": ["min", "max"]
      }
    }
  }],
  "temperature": 0.0,
  "max_tokens": 4096,
  "stream": false,
  "_expected_function_call": {
    "name": "generate_random_number",
    "arguments": {"min": 1, "max": 100}
  }
}
```

## 测试 DeepSeek 官方 API

### 基本测试命令

```bash
uv run tool_calls_eval.py \
  samples-deepseek.jsonl \
  --model deepseek-chat \
  --base-url https://api.deepseek.com/v1 \
  --api-key YOUR_DEEPSEEK_API_KEY \
  --filter-unsupported-roles \
  --concurrency 5 \
  --output results-deepseek-official.jsonl \
  --summary summary-deepseek-official.json \
  --temperature 0.0
```

### 参数说明

- `--filter-unsupported-roles`: **必须使用！** 过滤掉 DeepSeek 不支持的 `tool` 和 `_input` role
- `--model`: 模型名称，如 `deepseek-chat` 或 `deepseek-reasoner`
- `--base-url`: API 端点
- `--concurrency`: 并发请求数，建议 3-10
- `--temperature`: 温度参数，建议 0.0 以保证一致性

## 测试第三方 Vendor API

### 示例：测试某个第三方提供商

```bash
uv run tool_calls_eval.py \
  samples-deepseek.jsonl \
  --model deepseek-chat \
  --base-url https://api.third-party-vendor.com/v1 \
  --api-key YOUR_VENDOR_API_KEY \
  --filter-unsupported-roles \
  --concurrency 5 \
  --output results-vendor-xyz.jsonl \
  --summary summary-vendor-xyz.json
```

## 结果分析

### Summary 文件说明

测试完成后，`summary.json` 会包含以下统计信息：

```json
{
  "model": "deepseek-chat",
  "success_count": 500,           // 成功响应的请求数
  "failure_count": 12,             // 失败的请求数
  "finish_stop": 10,               // 正常结束（未调用工具）
  "finish_tool_calls": 490,        // 触发工具调用
  "finish_others": 2,              // 其他结束原因
  "schema_validation_error_count": 15,  // 工具参数验证失败数
  "successful_tool_call_count": 475     // 成功的工具调用数
}
```

### 关键指标

1. **Tool Call 触发率** = `finish_tool_calls` / `success_count`
   - 衡量模型是否能识别需要调用工具的场景

2. **Tool Call 准确率** = `successful_tool_call_count` / `finish_tool_calls`
   - 衡量生成的工具调用参数是否符合 schema

3. **综合成功率** = `successful_tool_call_count` / 总样本数
   - 综合评估工具调用能力

### 对比分析步骤

1. **测试官方 API**（作为基准）
2. **测试第三方 Vendor API**
3. **对比关键指标**：
   - 如果 Vendor 的 Tool Call 准确率显著低于官方（例如低 10%+），可能使用了量化版本
   - 如果触发率差异大，可能是 prompt 处理不一致
   - 如果参数准确率差异大，说明推理能力下降

## 增量测试模式

如果测试中断或需要重跑失败的请求：

```bash
uv run tool_calls_eval.py \
  samples-deepseek.jsonl \
  --model deepseek-chat \
  --base-url YOUR_API_URL \
  --api-key YOUR_API_KEY \
  --filter-unsupported-roles \
  --incremental \
  --output results-vendor-xyz.jsonl \
  --summary summary-vendor-xyz.json
```

`--incremental` 模式会：
- 跳过已成功的请求
- 重新运行失败的请求
- 追加新的结果

## 重新生成测试集

如果需要调整测试参数或重新生成：

```bash
# 查看帮助
uv run convert_dataset.py --help

# 自定义生成
uv run convert_dataset.py \
  --input path/to/dataset.json \
  --output my-samples.jsonl \
  --model deepseek-chat \
  --temperature 0.1 \
  --max-tokens 2048
```

## 注意事项

1. **API Rate Limit**: 注意调整 `--concurrency` 避免触发速率限制
2. **成本控制**: 512条测试样本 × 2个API = ~1000次调用，注意成本
3. **结果文件**: 每次测试使用不同的输出文件名，便于对比
4. **重复测试**: 建议运行2-3次取平均值，减少随机性影响
5. **Temperature**: Tool call 测试建议使用 0.0 或很低的值

## 故障排查

### 常见错误

1. **认证失败**: 检查 API Key 是否正确
2. **Rate Limit**: 降低 `--concurrency` 值
3. **Timeout**: 增加 `--timeout` 值（默认600秒）
4. **Schema 验证失败**: 检查返回的 tool_call 格式是否正确

### 调试模式

设置环境变量查看详细日志：

```bash
export LOGURU_LEVEL=DEBUG
uv run tool_calls_eval.py ...
```
