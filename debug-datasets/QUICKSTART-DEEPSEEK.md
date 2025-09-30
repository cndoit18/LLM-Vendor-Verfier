# DeepSeek 测试快速开始

本指南帮助你快速开始 DeepSeek 模型的 Tool Call 能力测试。

## 📋 前提条件

- Python 3.10+
- uv 包管理器
- DeepSeek API Key（官方或第三方 vendor）

## 🚀 快速开始（3步）

### 1. 转换数据集

已经为你准备好了 512 条测试样本！

```bash
# 数据已经转换完成，位于：
samples-deepseek.jsonl
```

如果需要重新生成：

```bash
uv run convert_dataset.py
```

### 2. 查看数据统计

```bash
uv run analyze_samples.py samples-deepseek.jsonl
```

输出示例：
```
📊 Basic Statistics
  Total samples: 512
  Unique tool types: 122

💬 Message Statistics
  Single-turn samples: 323 (63.09%)
  Multi-turn samples: 189 (36.91%)

🔧 Tool Statistics
  Avg parameters per tool: 2.05
```

### 3. 运行测试

**方式 A：使用 PowerShell 脚本（推荐 Windows 用户）**

```powershell
# 设置环境变量
$env:DEEPSEEK_API_KEY = "sk-your-key"
$env:VENDOR_API_KEY = "sk-vendor-key"
$env:VENDOR_BASE_URL = "https://vendor-url/v1"

# 运行测试
.\test-deepseek.ps1
```

**方式 B：手动运行（推荐高级用户）**

测试官方 API：
```bash
uv run tool_calls_eval.py samples-deepseek.jsonl \
  --model deepseek-chat \
  --base-url https://api.deepseek.com/v1 \
  --api-key YOUR_KEY \
  --filter-unsupported-roles \
  --concurrency 5 \
  --output results-official.jsonl \
  --summary summary-official.json
```

测试第三方 Vendor：
```bash
uv run tool_calls_eval.py samples-deepseek.jsonl \
  --model deepseek-chat \
  --base-url https://vendor-url/v1 \
  --api-key VENDOR_KEY \
  --filter-unsupported-roles \
  --concurrency 5 \
  --output results-vendor.jsonl \
  --summary summary-vendor.json
```

## 📊 查看结果

测试完成后，查看 `summary-*.json` 文件：

```json
{
  "model": "deepseek-chat",
  "success_count": 500,
  "finish_tool_calls": 490,
  "successful_tool_call_count": 475,
  "schema_validation_error_count": 15
}
```

### 关键指标计算

1. **Tool Call 触发率**：490 / 500 = 98%
   - 模型识别需要调用工具的准确性

2. **Tool Call 准确率**：475 / 490 = 96.9%
   - 生成的工具参数符合 schema 的比例

3. **综合成功率**：475 / 512 = 92.8%
   - 整体 Tool Call 能力评估

## 🔍 对比分析

### 运行对比

运行 PowerShell 脚本后，会自动生成对比报告：

```
File: summary-deepseek-official.json
---
Model: deepseek-chat
Success Rate: 500/512 (97.66%)
Tool Call Trigger Rate: 490/500 (98.00%)
Tool Call Accuracy: 475/490 (96.94%)
Schema Validation Errors: 15

File: summary-vendor.json
---
Model: deepseek-chat
Success Rate: 495/512 (96.68%)
Tool Call Trigger Rate: 450/495 (90.91%)
Tool Call Accuracy: 405/450 (90.00%)
Schema Validation Errors: 45
```

### 判断标准

⚠️ **可能使用了量化模型的信号：**

| 指标 | 官方 | Vendor | 差异 | 结论 |
|------|------|--------|------|------|
| Tool Call 准确率 | 96.9% | 90.0% | -6.9% | ⚠️ 显著下降 |
| Schema 错误数 | 15 | 45 | +200% | ⚠️ 错误率大幅增加 |
| 触发率 | 98.0% | 90.9% | -7.1% | ⚠️ 识别能力下降 |

**结论示例：**
- ✅ 差异 < 5%：可能是网络抖动或随机性
- ⚠️ 差异 5-10%：需要进一步调查
- 🚨 差异 > 10%：很可能使用了量化或不同版本模型

## 💡 高级用法

### 增量测试模式

如果测试中断或需要重跑失败的请求：

```bash
uv run tool_calls_eval.py samples-deepseek.jsonl \
  --model deepseek-chat \
  --base-url YOUR_URL \
  --api-key YOUR_KEY \
  --filter-unsupported-roles \
  --incremental \
  --output results.jsonl \
  --summary summary.json
```

### 调整并发数

根据 API rate limit 调整：

```bash
# 高并发（适合无限制 API）
--concurrency 20

# 低并发（适合有限制的 API）
--concurrency 3
```

### 调整温度参数

```bash
uv run convert_dataset.py \
  --temperature 0.1 \
  --output samples-temp-0.1.jsonl
```

## 🐛 故障排查

### 认证错误
```
Error: Incorrect API key provided
```
**解决**：检查 API Key 是否正确，是否有多余的空格

### Rate Limit
```
Error: Rate limit exceeded
```
**解决**：降低 `--concurrency` 值，如 `--concurrency 3`

### Timeout
```
Error: Request timed out
```
**解决**：增加超时时间 `--timeout 900`（900秒）

### Schema 验证错误过多
```
schema_validation_error_count: 100+
```
**原因**：模型返回的 tool call 参数格式不正确
**影响**：说明模型质量可能有问题

## 📚 更多信息

- 详细文档：[DeepSeek Testing Guide](DOCUMENTS/deepseek-testing-guide.md)
- 主项目：[README.md](README.md)
- 数据集分析：运行 `uv run analyze_samples.py`

## 💪 下一步

1. ✅ 运行官方 API 测试（作为基准）
2. ✅ 运行至少 2 个第三方 vendor 测试
3. ✅ 对比结果，生成报告
4. ✅ 根据结果选择可靠的 API provider

祝测试顺利！🎉
