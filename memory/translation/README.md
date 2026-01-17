# Translation Middleware - 中转层模块

## 📋 目录
- [模块概述](#模块概述)
- [设计理念](#设计理念)
- [架构设计](#架构设计)
- [核心组件](#核心组件)
- [接口设计](#接口设计)
- [Atomizer - 正向编译](#atomizer---正向编译)
- [Synthesizer - 反向编译](#synthesizer---反向编译)
- [Prompt 管理](#prompt-管理)
- [错误处理](#错误处理)
- [性能优化](#性能优化)
- [最佳实践](#最佳实践)

---

## 模块概述

### 职责定位
Translation Middleware 是 Nakari 的**自然语言与离散原子网络之间的双向编译器**。该模块负责将自然语言转换为结构化的原子（正向编译），以及将原子网络转换为自然语言（反向编译）。通过将复杂的 Prompt 设计与核心业务逻辑解耦，实现 Prompt 的独立迭代和容错集中处理。

### 设计目标
1. **解耦 Prompt 设计**：Prompt 的优化不影响核心业务逻辑
2. **容错集中**：LLM 输出的格式清洗、校验和重试逻辑集中处理
3. **独立迭代**：Prompt 可以独立进行 A/B Testing
4. **灵活切换**：支持不同的 Prompt 策略和模型
5. **可观测性**：记录 Prompt 的使用情况和效果

### 技术选型

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| LangChain | 0.1+ | 提供 LLM 调用的抽象层，支持 Prompt 模板 |
| Pydantic | 2.0+ | 数据验证和序列化，确保 LLM 输出格式正确 |
| json-repair | 0.1+ | 修复 LLM 输出的格式错误 |

---

## 设计理念

### 双向编译模型

```
┌─────────────────────────────────────────────────────────────┐
│                    双向编译模型                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
    ┌─────────┐                   ┌─────────┐
    │ Atomizer│                   │Synthesizer│
    │ 正向编译  │                   │ 反向编译   │
    └────┬────┘                   └────┬────┘
         │                             │
         ▼                             ▼
  自然语言 → 原子网络                原子网络 → 自然语言
  (Text to Graph)                  (Graph to Text)
```

### 编译过程

**正向编译（Atomizer）**：
```
自然语言输入
    │
    ▼
┌──────────────────┐
│ Prompt Engineering │
│ - 选择 Prompt 模板  │
│ - 填充上下文信息   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ LLM 调用         │
│ - 语义分割       │
│ - 关系推断       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 格式清洗与验证    │
│ - JSON 修复      │
│ - Schema 验证    │
└────────┬─────────┘
         │
         ▼
    原子子图
```

**反向编译（Synthesizer）**：
```
原子子图
    │
    ▼
┌──────────────────┐
│ 序列化           │
│ - 转换为 JSON   │
│ - 格式化输出     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Prompt Engineering │
│ - 构建 Prompt    │
│ - 附加图结构信息  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ LLM 调用         │
│ - 语义推断       │
│ - 自然语言生成   │
└────────┬─────────┘
         │
         ▼
    自然语言输出
```

### 架构价值

| 价值点 | 说明 |
|--------|------|
| **Prompt 独立迭代** | 可以在不修改核心代码的情况下，独立优化 Prompt |
| **逻辑解耦** | 核心业务逻辑只处理结构化的原子子图，不直接处理非结构化文本 |
| **容错集中** | LLM 输出的格式清洗、校验和重试逻辑集中在此层 |
| **A/B Testing** | 可以同时测试不同的 Prompt 策略，选择最优方案 |

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Nakari Application                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 Translation Middleware                        │
│  ┌──────────────┐           ┌──────────────┐               │
│  │  Atomizer    │           │ Synthesizer  │               │
│  │ 正向编译器     │           │ 反向编译器    │               │
│  └──────┬───────┘           └──────┬───────┘               │
│         │                           │                         │
│         └───────────┬───────────────┘                         │
│                     ▼                                         │
│         ┌─────────────────────────────┐                       │
│         │ Prompt Manager             │                       │
│         │ - Prompt 模板管理           │                       │
│         │ - Prompt 版本控制           │                       │
│         │ - A/B Testing 支持         │                       │
│         └─────────────────────────────┘                       │
│                     ▼                                         │
│         ┌─────────────────────────────┐                       │
│         │ Output Validator            │                       │
│         │ - JSON 修复                 │                       │
│         │ - Schema 验证               │                       │
│         │ - 重试逻辑                 │                       │
│         └─────────────────────────────┘                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                          │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│  │  LLM    │         │ Memory  │         │ Context │       │
│  │  API    │         │ Module  │         │ Module  │       │
│  └─────────┘         └─────────┘         └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 数据流向

**写入流程（正向编译）**：
```
用户输入
    │
    ▼
Context Manager
    │
    ▼
Atomizer (Translation Middleware)
    │
    ├─> Prompt Manager (选择 Prompt)
    ├─> LLM API (语义分割)
    └─> Output Validator (格式验证)
    │
    ▼
Memory Module (写入原子)
```

**读取流程（反向编译）**：
```
用户查询
    │
    ▼
Context Manager
    │
    ▼
Memory Module (检索原子)
    │
    ▼
Synthesizer (Translation Middleware)
    │
    ├─> Prompt Manager (选择 Prompt)
    ├─> LLM API (语义推断)
    └─> Output Validator (格式验证)
    │
    ▼
自然语言响应
```

---

## 核心组件

### 1. Atomizer（正向编译器）

**职责**：
- 将自然语言转换为结构化的原子子图
- 进行语义分割和关系推断
- 判断新原子与已有原子的关系（新增/修改/删除）

**接口设计**：
```python
def atomize(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    prompt_version: Optional[str] = None
) -> AtomSubgraph:
    """
    正向编译：自然语言 → 原子子图

    参数:
        text: 自然语言输入
        context: 上下文信息（可选）
        prompt_version: Prompt 版本（可选）

    返回:
        AtomSubgraph {
            atoms: List[Atom],           # 原子列表
            edges: List[Tuple[str, str]], # 边列表（原子 ID 对）
            operations: List[Operation],  # 操作列表（新增/修改/删除）
            confidence: float,            # 置信度
        }
    """
    pass
```

### 2. Synthesizer（反向编译器）

**职责**：
- 将原子子图转换为自然语言
- 进行语义推断和关系解释
- 生成自然语言响应

**接口设计**：
```python
def synthesize(
    subgraph: AtomSubgraph,
    query: Optional[str] = None,
    prompt_version: Optional[str] = None
) -> NaturalLanguageResponse:
    """
    反向编译：原子子图 → 自然语言

    参数:
        subgraph: 原子子图
        query: 查询文本（可选）
        prompt_version: Prompt 版本（可选）

    返回:
        NaturalLanguageResponse {
            text: str,              # 自然语言响应
            confidence: float,       # 置信度
            sources: List[str],     # 使用的原子 ID
        }
    """
    pass
```

### 3. Prompt Manager（Prompt 管理器）

**职责**：
- 管理不同的 Prompt 模板
- 支持 Prompt 版本控制
- 支持 A/B Testing

**接口设计**：
```python
def get_prompt(
    task_type: PromptTaskType,
    version: Optional[str] = None
) -> PromptTemplate:
    """
    获取 Prompt 模板

    参数:
        task_type: 任务类型（atomize/synthesize）
        version: Prompt 版本（可选，默认最新版本）

    返回:
        PromptTemplate: Prompt 模板
    """
    pass

def register_prompt(
    task_type: PromptTaskType,
    version: str,
    template: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    注册新的 Prompt 模板

    参数:
        task_type: 任务类型
        version: 版本号
        template: Prompt 模板
        metadata: 元数据（可选）

    返回:
        是否注册成功
    """
    pass

def ab_test_prompt(
    task_type: PromptTaskType,
    versions: List[str],
    metrics: List[str]
) -> ABTestResult:
    """
    进行 Prompt A/B Testing

    参数:
        task_type: 任务类型
        versions: 参与测试的版本列表
        metrics: 评估指标列表

    返回:
        ABTestResult: A/B 测试结果
    """
    pass
```

### 4. Output Validator（输出验证器）

**职责**：
- 验证 LLM 输出的格式
- 修复常见的 JSON 格式错误
- 重试不合法的输出

**接口设计**：
```python
def validate_output(
    output: str,
    schema: BaseModel
) -> ValidationResult:
    """
    验证 LLM 输出

    参数:
        output: LLM 输出文本
        schema: 期望的数据结构（Pydantic 模型）

    返回:
        ValidationResult {
            is_valid: bool,        # 是否有效
            data: Any,             # 解析后的数据
            errors: List[str],     # 错误列表
        }
    """
    pass

def repair_json(
    json_str: str
) -> Optional[Dict[str, Any]]:
    """
    修复 JSON 格式错误

    参数:
        json_str: JSON 字符串

    返回:
        修复后的 JSON 对象（如果可修复）
    """
    pass
```

---

## 接口设计

### Translation Middleware 接口

```python
class TranslationMiddleware:
    """
    Translation Middleware
    双向编译器接口
    """

    def __init__(
        self,
        default_prompt_version: str = "latest",
        max_retries: int = 3
    ):
        """
        初始化中转层

        参数:
            default_prompt_version: 默认 Prompt 版本
            max_retries: 最大重试次数
        """
        pass

    def atomize(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        prompt_version: Optional[str] = None
    ) -> AtomSubgraph:
        """
        正向编译：自然语言 → 原子子图
        """
        pass

    def synthesize(
        self,
        subgraph: AtomSubgraph,
        query: Optional[str] = None,
        prompt_version: Optional[str] = None
    ) -> str:
        """
        反向编译：原子子图 → 自然语言
        """
        pass

    def get_prompt_stats(self) -> PromptStats:
        """
        获取 Prompt 使用统计

        返回:
            PromptStats {
                total_calls: int,
                success_rate: float,
                avg_latency: float,
                version_usage: Dict[str, int],
            }
        """
        pass

    def switch_prompt_version(
        self,
        task_type: PromptTaskType,
        version: str
    ) -> bool:
        """
        切换 Prompt 版本

        参数:
            task_type: 任务类型
            version: 目标版本

        返回:
            是否切换成功
        """
        pass
```

---

## Atomizer - 正向编译

### Prompt 模板

**提取 Prompt 模板**：
```
你是一个语义分析专家，负责将自然语言转换为结构化的原子网络。

任务：
1. 分析输入文本，识别其中的原子（实体、事件、概念等）
2. 判断原子之间的关系
3. 判断每个原子是新增、修改还是删除已有原子

输入：
{{ text }}

上下文：
{{ context }}

输出格式（JSON）：
{
  "atoms": [
    {
      "content": "原子内容",
      "extensions": {
        "tags": ["entity", "person"],
        "confidence": 0.95
      }
    }
  ],
  "edges": [
    ["atom_id_1", "atom_id_2"]
  ],
  "operations": [
    {
      "type": "create",
      "atom_id": "atom_id_1"
    }
  ],
  "confidence": 0.9
}
```

### 处理流程

```
输入文本
    │
    ▼
┌──────────────────┐
│ 指代消解          │
│ - 代词转换       │
│ - 时间绝对化     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 选择 Prompt      │
│ - 根据任务类型   │
│ - 选择版本       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 填充上下文        │
│ - 历史对话       │
│ - 已有原子       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 调用 LLM         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 格式验证          │
│ - JSON 解析      │
│ - Schema 验证    │
└────────┬─────────┘
         │
         ▼
    返回原子子图
```

### 错误处理

**常见错误及处理**：

| 错误类型 | 处理策略 |
|---------|---------|
| JSON 格式错误 | 尝试修复，修复失败则重试 |
| Schema 不匹配 | 提示 LLM 修正，最多重试 3 次 |
| 输出为空 | 检查输入文本，返回错误 |
| LLM 拒绝 | 使用备用 Prompt，或返回错误 |

---

## Synthesizer - 反向编译

### Prompt 模板

**推断 Prompt 模板**：
```
你是一个语义推断专家，负责从原子网络中推断出语义关系并生成自然语言。

任务：
1. 分析给定的原子网络，理解原子之间的关系
2. 推断原子之间的语义关系
3. 回答用户的问题或生成自然语言描述

原子网络（JSON）：
{{ subgraph }}

用户查询：
{{ query }}

输出格式：
基于这些原子的内容和连接关系，生成自然的语言描述，回答用户的问题。
```

### 处理流程

```
原子子图
    │
    ▼
┌──────────────────┐
│ 序列化           │
│ - 转换为 JSON   │
│ - 格式化输出     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 选择 Prompt      │
│ - 根据任务类型   │
│ - 选择版本       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 填充上下文        │
│ - 用户查询       │
│ - 历史对话       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 调用 LLM         │
└────────┬─────────┘
         │
         ▼
    返回自然语言
```

### 语义推断策略

**语义涌现**：
- 不预先存储语义关系
- 从原子内容和连接关系中"涌现"语义
- 由 LLM 推断原子之间的语义关系

**示例**：
```
原子网络:
- Atom A: "Wenki"
- Atom B: "熬夜"
- Atom C: "喜欢"

连接: A -- C, B -- C

LLM 推断: "Wenki 喜欢熬夜"
```

---

## Prompt 管理

### Prompt 版本控制

**版本命名规则**：
```
{task_type}_v{major}.{minor}.{patch}

示例:
- atomize_v1.0.0
- synthesize_v1.2.3
```

**版本发布策略**：
- `major`: 重大架构变更
- `minor`: 功能新增或优化
- `patch`: Bug 修复

### A/B Testing

**测试流程**：
1. 选择多个 Prompt 版本
2. 随机分配请求到不同版本
3. 收集指标（响应质量、成功率、延迟等）
4. 分析结果，选择最优版本

**指标定义**：
```python
class ABTestMetrics:
    success_rate: float        # 成功率
    avg_latency: float         # 平均延迟
    output_quality: float     # 输出质量（人工评分）
    user_satisfaction: float   # 用户满意度
```

---

## 错误处理

### 错误分类

| 错误类型 | 处理策略 | 重试 |
|---------|---------|------|
| JSON 格式错误 | 尝试修复 | 是 |
| Schema 不匹配 | 提示 LLM 修正 | 是 |
| LLM 调用失败 | 延迟重试 | 是 |
| 输出为空 | 检查输入 | 否 |
| LLM 拒绝 | 使用备用 Prompt | 是 |

### 重试策略

**指数退避重试**：
```python
retry_delays = [1, 2, 4]  # 秒
max_retries = 3
```

**重试条件**：
- JSON 格式错误且可修复
- Schema 不匹配
- LLM 调用失败（网络错误、限流等）

**不重试条件**：
- 输出为空
- 参数错误
- 超过最大重试次数

---

## 性能优化

### 缓存策略

**Prompt 缓存**：
```python
prompt_cache = {
    "atomize_v1.0.0": "prompt content...",
    "synthesize_v1.0.0": "prompt content...",
}
```

**输出缓存**：
```python
output_cache = {
    "input_hash": "output..."
}
```

### 批量处理

**批量原子化**：
```python
def batch_atomize(
    texts: List[str],
    context: Optional[Dict[str, Any]] = None
) -> List[AtomSubgraph]:
    """
    批量原子化

    参数:
        texts: 文本列表
        context: 上下文信息（可选）

    返回:
        List[AtomSubgraph]: 原子子图列表
    """
    pass
```

---

## 最佳实践

### 1. Prompt 设计

**清晰的指令**：
- 明确任务目标
- 提供具体的输出格式示例
- 避免歧义的表达

**上下文管理**：
- 提供足够的上下文信息
- 避免上下文过长导致 Token 浪费
- 动态调整上下文内容

### 2. 错误处理

**优雅降级**：
- 当主 Prompt 失败时，使用备用 Prompt
- 提供清晰的错误信息
- 记录详细的错误日志

**持续优化**：
- 分析错误模式
- 优化 Prompt 以减少错误率
- 定期更新 Prompt 模板

### 3. A/B Testing

**合理的指标**：
- 选择可量化的指标
- 避免主观评价
- 考虑用户体验

**渐进式上线**：
- 先在小流量下测试
- 观察指标变化
- 逐步扩大流量

---

## 总结

Translation Middleware 是 Nakari 的自然语言与离散原子网络之间的双向编译器，通过解耦 Prompt 设计与核心业务逻辑，实现了：

1. **Prompt 独立迭代**：Prompt 的优化不影响核心代码
2. **容错集中**：LLM 输出的格式清洗、校验和重试逻辑集中处理
3. **A/B Testing**：支持 Prompt 的 A/B Testing，选择最优方案
4. **灵活切换**：支持不同的 Prompt 策略和模型
5. **可观测性**：记录 Prompt 的使用情况和效果

该模块的设计充分体现了软件工程中的关注点分离原则，通过将 Prompt 管理、输出验证等非核心逻辑集中处理，让核心业务逻辑更加简洁和稳定。同时，通过 Prompt 版本控制和 A/B Testing，支持持续的优化和迭代。
