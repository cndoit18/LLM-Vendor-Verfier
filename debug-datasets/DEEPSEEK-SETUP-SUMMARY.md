# DeepSeek 测试环境配置总结

## ✅ 完成的工作

### 1. 数据准备与清洗 ✨

#### 原始数据
- **来源**: `glaive_toolcall_zh` 数据集
- **原始数量**: 1,000 条对话样本
- **位置**: `Z:\works\huggingface.co\datasets\glaive_toolcall_zh\glaive_toolcall_zh_1k.json`

#### 数据转换
- **转换后数量**: 512 条有效测试样本
- **跳过数量**: 488 条（不符合测试要求的样本）
- **输出文件**: `samples-deepseek.jsonl` (472 KB)

#### 筛选标准
✅ 包含至少一次 function call  
✅ 有用户输入（human 消息）  
✅ 工具定义完整且可解析  
❌ 跳过没有 function call 的纯对话  
❌ 跳过工具定义缺失或格式错误的样本  

#### 数据统计
```
📊 基础统计
  - 总样本数: 512
  - 独特工具类型: 122
  - 单轮对话: 323 (63.09%)
  - 多轮对话: 189 (36.91%)
  - 平均参数数: 2.05 per tool

🔝 最常见的工具 (Top 5)
  1. calculate_age          - 29 samples (5.66%)
  2. convert_currency       - 28 samples (5.47%)
  3. calculate_distance     - 27 samples (5.27%)
  4. generate_password      - 26 samples (5.08%)
  5. generate_qr_code       - 25 samples (4.88%)
```

### 2. 创建的工具脚本 🛠️

#### `convert_dataset.py`
**功能**: 将原始数据集转换为测试格式
```bash
uv run convert_dataset.py \
  --input path/to/dataset.json \
  --output samples-deepseek.jsonl \
  --model deepseek-chat \
  --temperature 0.0
```

**转换规则**:
- `human` → `user`
- `gpt` → `assistant`
- `function_call` → 期望输出（保存在 `_expected_function_call`）
- `observation` → 移除（DeepSeek 不支持 `tool` role）

#### `analyze_samples.py`
**功能**: 分析测试集的统计信息
```bash
uv run analyze_samples.py samples-deepseek.jsonl
```

**输出**:
- 样本总数和工具类型统计
- 对话轮次分布
- 参数复杂度分析
- 最常见工具排名

#### `test-deepseek.ps1` (Windows)
**功能**: 自动化测试脚本（PowerShell）
```powershell
$env:DEEPSEEK_API_KEY = "your-key"
$env:VENDOR_API_KEY = "vendor-key"
$env:VENDOR_BASE_URL = "https://vendor-url/v1"
.\test-deepseek.ps1
```

**特性**:
- 自动测试官方和 vendor API
- 生成对比报告
- 彩色输出和进度提示

#### `test-deepseek.sh` (Linux/Mac)
**功能**: 自动化测试脚本（Bash）
```bash
export DEEPSEEK_API_KEY="your-key"
./test-deepseek.sh
```

### 3. 核心功能增强 🚀

#### `tool_calls_eval.py` 的新特性

##### `--filter-unsupported-roles` 标志
**目的**: 兼容 DeepSeek 等不支持 `tool` role 的模型

**功能**:
- 移除 `tool` role 消息（observation）
- 移除 `_input` role 消息（系统提示）
- 过滤带有 `tool_calls` 的 assistant 历史消息
- 移除 `user` 字段（部分 API 不支持）

**使用场景**:
- ✅ DeepSeek（不支持 tool role）
- ✅ 某些第三方 vendor API
- ✅ 测试首轮 tool call 生成能力

**原理说明**:
```python
# 过滤前（包含完整对话历史）
messages = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "tool_calls": [...]},  # ← 会被过滤
    {"role": "tool", "content": "..."},          # ← 会被过滤
    {"role": "user", "content": "..."}
]

# 过滤后（只保留导致 tool call 的消息）
messages = [
    {"role": "user", "content": "..."}
]
```

### 4. 文档完善 📚

#### `DOCUMENTS/deepseek-testing-guide.md`
**内容**:
- 数据集准备详解
- 测试命令示例
- 结果分析方法
- 故障排查指南
- 增量测试模式说明

#### `QUICKSTART-DEEPSEEK.md`
**内容**:
- 3 步快速开始
- 结果解读示例
- 对比分析方法
- 常见问题解决

#### `README.md` 更新
**新增章节**:
- "Testing DeepSeek Models"
- 快速开始指南
- 关键指标说明
- 量化模型识别标准

### 5. 项目结构 📁

```
LLM-Vendor-Verfier/
├── tool_calls_eval.py              # 核心评估脚本（已增强）
├── convert_dataset.py              # 数据集转换脚本（新）
├── analyze_samples.py              # 数据分析脚本（新）
├── test-deepseek.ps1               # Windows 自动化脚本（新）
├── test-deepseek.sh                # Linux/Mac 自动化脚本（新）
├── samples-deepseek.jsonl          # 转换后的测试数据（新，512条）
├── README.md                       # 项目说明（已更新）
├── QUICKSTART-DEEPSEEK.md          # 快速开始指南（新）
├── DEEPSEEK-SETUP-SUMMARY.md       # 本文件（新）
└── DOCUMENTS/
    ├── call-llm.md                 # 原有文档
    └── deepseek-testing-guide.md   # DeepSeek 测试详细指南（新）
```

## 🎯 使用流程

### 方案 A: 快速测试（推荐）

```powershell
# 1. 设置环境变量
$env:DEEPSEEK_API_KEY = "your-deepseek-key"
$env:VENDOR_API_KEY = "your-vendor-key"
$env:VENDOR_BASE_URL = "https://vendor-url/v1"

# 2. 运行自动化测试
.\test-deepseek.ps1

# 3. 查看结果
Get-Content summary-deepseek-official.json
Get-Content summary-vendor.json
```

### 方案 B: 手动测试（高级）

```bash
# 1. 查看数据统计
uv run analyze_samples.py samples-deepseek.jsonl

# 2. 测试官方 API
uv run tool_calls_eval.py samples-deepseek.jsonl \
  --model deepseek-chat \
  --base-url https://api.deepseek.com/v1 \
  --api-key $DEEPSEEK_API_KEY \
  --filter-unsupported-roles \
  --output results-official.jsonl \
  --summary summary-official.json

# 3. 测试 Vendor API
uv run tool_calls_eval.py samples-deepseek.jsonl \
  --model deepseek-chat \
  --base-url $VENDOR_BASE_URL \
  --api-key $VENDOR_API_KEY \
  --filter-unsupported-roles \
  --output results-vendor.jsonl \
  --summary summary-vendor.json

# 4. 对比结果
# 查看 summary-*.json 文件中的关键指标
```

## 📊 关键评估指标

### 指标定义

| 指标名称 | 计算公式 | 说明 |
|---------|---------|------|
| **Success Rate** | `success_count / total_samples` | API 调用成功率 |
| **Tool Call Trigger Rate** | `finish_tool_calls / success_count` | 模型识别需要调用工具的准确性 |
| **Tool Call Accuracy** | `successful_tool_call_count / finish_tool_calls` | 生成的工具参数符合 schema 的比例 |
| **Overall Success Rate** | `successful_tool_call_count / total_samples` | 综合 Tool Call 能力 |

### 判断标准

#### ✅ 正常情况
- Tool Call Accuracy 差异 < 5%
- Schema 错误数差异 < 10 个
- Trigger Rate 差异 < 3%

#### ⚠️ 需要关注
- Tool Call Accuracy 差异 5-10%
- Schema 错误数增加 50-100%
- 某些特定工具成功率显著下降

#### 🚨 可能使用量化模型
- Tool Call Accuracy 差异 > 10%
- Schema 错误数增加 > 100%
- Trigger Rate 差异 > 10%
- 参数类型错误频繁（如 string vs integer）

### 示例对比

```
官方 API 结果:
  Tool Call Trigger Rate: 490/500 (98.0%)
  Tool Call Accuracy: 475/490 (96.9%)
  Schema Errors: 15

Vendor A 结果:
  Tool Call Trigger Rate: 485/500 (97.0%)  [-1.0%] ✅
  Tool Call Accuracy: 470/485 (96.9%)      [+0.0%] ✅
  Schema Errors: 15                        [±0]    ✅
结论: Vendor A 质量良好，接近官方

Vendor B 结果:
  Tool Call Trigger Rate: 450/500 (90.0%)  [-8.0%] 🚨
  Tool Call Accuracy: 400/450 (88.9%)      [-8.0%] 🚨
  Schema Errors: 50                        [+233%] 🚨
结论: Vendor B 可能使用了量化模型或不同版本
```

## 🔧 高级功能

### 增量测试模式
```bash
# 如果测试中断，使用 --incremental 继续
uv run tool_calls_eval.py samples-deepseek.jsonl \
  --incremental \
  ... 其他参数
```
**作用**: 跳过已成功的请求，只重跑失败的

### 自定义数据集
```bash
# 使用自己的数据集
uv run convert_dataset.py \
  --input your-dataset.json \
  --output your-samples.jsonl \
  --model deepseek-chat \
  --temperature 0.0
```

### 调试模式
```bash
# 查看详细日志
$env:LOGURU_LEVEL = "DEBUG"
uv run tool_calls_eval.py ...
```

## 📝 注意事项

### API 成本估算
- **单次完整测试**: 512 个请求
- **对比测试**: 512 × 2 = 1024 个请求
- **建议**: 先用小样本测试（如前 50 条）验证配置

### Rate Limit 管理
- **默认并发**: 5
- **高吞吐 API**: 可增加到 10-20
- **受限 API**: 降低到 2-3

### 测试可靠性
- **重复测试**: 建议运行 2-3 次取平均值
- **Temperature**: 使用 0.0 确保一致性
- **时间间隔**: 避免在 API 高峰期测试

## 🎉 总结

你现在拥有：
1. ✅ **512 条高质量中文 tool call 测试样本**
2. ✅ **完整的测试工具链**（转换、分析、测试、对比）
3. ✅ **自动化测试脚本**（Windows + Linux）
4. ✅ **详细的文档和指南**
5. ✅ **DeepSeek 兼容模式**（`--filter-unsupported-roles`）

### 下一步行动
1. 🔑 准备 API Keys（官方 + Vendor）
2. 🧪 运行快速测试验证环境
3. 📊 执行完整对比测试
4. 📈 分析结果，生成报告
5. ✅ 选择可靠的 API Provider

### 需要帮助？
- 查看 `QUICKSTART-DEEPSEEK.md` 快速开始
- 参考 `DOCUMENTS/deepseek-testing-guide.md` 详细说明
- 运行 `uv run tool_calls_eval.py --help` 查看所有参数

祝测试顺利！🚀
