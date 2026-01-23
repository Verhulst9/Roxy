# CPU - Driver 模块

## 📋 目录
- [模块概述](#模块概述)
- [设计理念](#设计理念)
- [架构设计](#架构设计)
- [核心组件](#核心组件)
- [接口设计](#接口设计)
- [模型选型](#模型选型)
- [调用策略](#调用策略)
- [错误处理](#错误处理)
- [性能优化](#性能优化)
- [最佳实践](#最佳实践)

---

## 模块概述

### 职责定位
CPU 模块是 Nakari 的**核心处理单元**，负责驱动 LLM 进行推理和生成。该模块不直接与用户交互，而是通过统一的接口，接收来自上下文管理器的输入，调用 LLM API，并将结果返回给调用方。

### 设计目标
1. **模型抽象**：屏蔽不同 LLM 提供商的差异，提供统一的调用接口
2. **多模型支持**：支持 GPT-4、Claude 等多种模型，可灵活切换
3. **成本优化**：根据任务复杂度选择合适的模型，降低调用成本
4. **可靠性**：处理 API 限流、超时等异常情况，确保系统稳定运行
5. **可观测性**：记录每次调用的参数、结果、Token 使用量等信息

### 技术选型

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| OpenAI API | 1.0+ | 成熟稳定的 LLM API，支持 GPT-4 |
| Anthropic API | 0.1+ | 支持 Claude 系列，适合长文本任务 |
| LangChain | 0.1+ | 提供 LLM 调用的抽象层，简化集成 |
| HTTPX | 0.24+ | 异步 HTTP 客户端，支持并发调用 |

---

## 设计理念

### LLM 调用的生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM 调用生命周期                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ 预处理   │   │ 调用 LLM │   │ 后处理   │
    │Preprocess│   │  Invoke  │   │Postprocess│
    └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │
         ▼             ▼             ▼
    参数验证       发送请求       解析响应
    格式转换       等待响应       提取结果
    Token 预估     重试处理       Token 统计
```

### 模型选型策略

**基于任务复杂度的模型选择**：

| 任务类型 | 推荐模型 | 成本 | 响应速度 | 适用场景 |
|---------|---------|------|---------|---------|
| 简单对话 | GPT-3.5 | 低 | 快 | 闲聊、快速响应 |
| 复杂推理 | GPT-4 | 高 | 慢 | 需要深度思考的任务 |
| 长文本 | Claude 2 | 中 | 中 | 长上下文处理 |
| 代码生成 | GPT-4 / Claude 2 | 高 | 慢 | 编程辅助 |
| 摘要生成 | GPT-3.5 / Claude 2 | 中 | 中 | 文本压缩 |

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
│                      CPU Module                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Model Router │  │ API Client   │  │ Response     │     │
│  │ 模型路由器    │  │ API 客户端    │  │ Parser       │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                   │
│                           ▼                                   │
│                  LLM Client Pool                            │
│           ┌─────────────────────────────┐                   │
│           │ - OpenAI Client              │                   │
│           │ - Anthropic Client           │                   │
│           │ - Connection Pool            │                   │
│           │ - Rate Limiter               │                   │
│           └─────────────────────────────┘                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Providers                              │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│  │ OpenAI  │         │Anthropic│         │  Future │       │
│  │ GPT-4   │         │ Claude  │         │ Providers│       │
│  └─────────┘         └─────────┘         └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 调用流程

```
Context Manager
       │
       ▼
┌──────────────────┐
│  CPU Module      │
│ - 模型路由       │
│ - 参数准备       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  API Client     │
│ - 发送请求       │
│ - 错误处理       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  LLM Provider    │
│ - 推理           │
│ - 生成响应       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Response Parser │
│ - 解析响应       │
│ - Token 统计     │
└────────┬─────────┘
         │
         ▼
    返回结果
```

---

## 核心组件

### 1. Model Router（模型路由器）

**职责**：
- 根据任务类型选择合适的模型
- 处理模型切换逻辑
- 记录模型使用情况

**接口设计**：
```python
def select_model(
    task_type: TaskType,
    context_length: int,
    complexity_score: float = 0.5
) -> ModelConfig:
    """
    选择合适的模型

    参数:
        task_type: 任务类型（chat, reasoning, code, summary 等）
        context_length: 上下文长度
        complexity_score: 复杂度评分（0-1）

    返回:
        ModelConfig {
            provider: str,        # 提供商（openai/anthropic）
            model: str,            # 模型名称（gpt-4/claude-2）
            temperature: float,    # 温度参数
            max_tokens: int,      # 最大 Token 数
        }
    """
```

### 2. API Client（API 客户端）

**职责**：
- 封装 LLM API 调用
- 处理限流、超时、重试
- 管理连接池

**接口设计**：
```python
async def invoke_llm(
    model_config: ModelConfig,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> LLMResponse:
    """
    调用 LLM API

    参数:
        model_config: 模型配置
        prompt: 提示词
        system_prompt: 系统提示（可选）
        temperature: 温度参数（可选，覆盖模型配置）
        max_tokens: 最大 Token 数（可选，覆盖模型配置）

    返回:
        LLMResponse {
            content: str,              # 响应内容
            model: str,                # 使用的模型
            prompt_tokens: int,        # 输入 Token 数
            completion_tokens: int,    # 输出 Token 数
            total_tokens: int,         # 总 Token 数
            latency: float,            # 延迟（秒）
        }
    """
```

### 3. Response Parser（响应解析器）

**职责**：
- 解析 LLM 响应
- 提取关键信息
- 验证响应格式

**接口设计**：
```python
def parse_response(
    raw_response: Dict[str, Any],
    expected_format: Optional[ResponseFormat] = None
) -> ParsedResponse:
    """
    解析 LLM 响应

    参数:
        raw_response: 原始响应（JSON）
        expected_format: 期望的响应格式（可选）

    返回:
        ParsedResponse {
            content: str,              # 解析后的内容
            metadata: Dict[str, Any],  # 元数据
            is_valid: bool,             # 是否有效
            errors: List[str],          # 错误列表
        }
    """
```

---

## 接口设计

### CPU 模块接口

```python
class CPUModule:
    """
    CPU 模块
    统一的 LLM 调用接口
    """

    def __init__(
        self,
        default_model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        初始化 CPU 模块

        参数:
            default_model: 默认模型
            temperature: 温度参数
            max_tokens: 最大 Token 数
        """
        pass

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        对话接口

        参数:
            messages: 对话历史
            model: 模型名称（可选，覆盖默认值）
            temperature: 温度参数（可选，覆盖默认值）
            max_tokens: 最大 Token 数（可选，覆盖默认值）

        返回:
            LLMResponse: LLM 响应
        """
        pass

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        文本补全接口

        参数:
            prompt: 提示词
            model: 模型名称（可选，覆盖默认值）
            temperature: 温度参数（可选，覆盖默认值）
            max_tokens: 最大 Token 数（可选，覆盖默认值）

        返回:
            LLMResponse: LLM 响应
        """
        pass

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """
        流式对话接口

        参数:
            messages: 对话历史
            model: 模型名称（可选，覆盖默认值）
            temperature: 温度参数（可选，覆盖默认值）
            max_tokens: 最大 Token 数（可选，覆盖默认值）

        返回:
            AsyncIterator[str]: 流式响应
        """
        pass

    def get_token_usage(self) -> TokenUsage:
        """
        获取 Token 使用统计

        返回:
            TokenUsage {
                total_prompt_tokens: int,
                total_completion_tokens: int,
                total_tokens: int,
                total_cost: float,
                model_usage: Dict[str, int],  # 各模型的使用次数
            }
        """
        pass

    def reset_token_usage(self) -> None:
        """
        重置 Token 使用统计
        """
        pass
```

---

## 模型选型

### OpenAI 系列

| 模型 | 最大 Token | 速度 | 成本 | 适用场景 |
|------|-----------|------|------|---------|
| GPT-4 | 8192 | 慢 | 高 | 复杂推理、代码生成 |
| GPT-4-32K | 32768 | 慢 | 很高 | 长文本处理 |
| GPT-3.5-Turbo | 4096 | 快 | 低 | 日常对话、简单任务 |
| GPT-3.5-Turbo-16K | 16384 | 快 | 中 | 中等长度文本 |

### Anthropic 系列

| 模型 | 最大 Token | 速度 | 成本 | 适用场景 |
|------|-----------|------|------|---------|
| Claude 2 | 100000 | 中 | 中 | 超长文本处理 |
| Claude Instant | 100000 | 快 | 低 | 快速响应 |
| Claude 1.3 | 9000 | 中 | 中 | 通用任务 |

### 模型切换策略

**自动切换规则**：

| 条件 | 切换到模型 | 原因 |
|------|-----------|------|
| Context > 8192 Token | GPT-4-32K / Claude 2 | 超出 GPT-4 限制 |
| 简单闲聊 | GPT-3.5-Turbo | 降低成本 |
| 复杂推理 | GPT-4 | 提高质量 |
| 实时对话 | Claude Instant / GPT-3.5-Turbo | 快速响应 |

---

## 调用策略

### 限流策略

**并发限制**：
```python
# OpenAI API 限制
OPENAI_RATE_LIMIT = {
    "gpt-4": {"rpm": 200, "tpm": 40000},  # 请求/分钟, Token/分钟
    "gpt-3.5-turbo": {"rpm": 3500, "tpm": 90000},
}

# Anthropic API 限制
ANTHROPIC_RATE_LIMIT = {
    "claude-2": {"rpm": 1000, "tpm": 100000},
}
```

**动态调整**：
- 监控 API 调用频率
- 接近限流时自动降低并发度
- 触发限流时自动切换模型或延迟重试

### 重试策略

**指数退避重试**：
```python
retry_delays = [1, 2, 4, 8, 16]  # 秒
max_retries = 5
```

**重试条件**：
- 网络错误（连接超时、DNS 解析失败）
- 限流错误（429 状态码）
- 服务器错误（5xx 状态码）

**不重试条件**：
- 参数错误（400 状态码）
- 认证错误（401 状态码）
- 权限错误（403 状态码）

### 批量调用

**适用场景**：
- 批量原子提取
- 批量摘要生成
- 并发对话处理

**接口设计**：
```python
async def batch_invoke(
    requests: List[LLMRequest],
    max_concurrency: int = 5
) -> List[LLMResponse]:
    """
    批量调用 LLM

    参数:
        requests: 请求列表
        max_concurrency: 最大并发数

    返回:
        List[LLMResponse]: 响应列表
    """
    pass
```

---

## 错误处理

### 错误分类

| 错误类型 | 处理策略 | 重试 | 告警 |
|---------|---------|------|------|
| 网络错误 | 重试 | 是 | 否 |
| 限流错误 | 延迟重试 | 是 | 否 |
| 超时错误 | 重试 | 是 | 否 |
| 参数错误 | 返回错误 | 否 | 是 |
| 认证错误 | 返回错误 | 否 | 是 |
| 配额用尽 | 切换模型 | 否 | 是 |
| 服务器错误 | 重试 | 是 | 是 |

### 错误响应格式

```python
class LLMError:
    """
    LLM 调用错误
    """

    error_code: str          # 错误代码
    error_message: str       # 错误消息
    retry_after: int         # 建议重试时间（秒）
    can_retry: bool          # 是否可重试
    original_error: Exception  # 原始异常
```

### 降级策略

**模型降级**：
```python
if gpt4_quota_exceeded:
    fallback_to_model = "gpt-3.5-turbo"
```

**功能降级**：
```python
if llm_unavailable:
    use_cached_response = True
```

---

## 性能优化

### 连接池管理

```python
# HTTPX 连接池配置
connection_pool = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,      # 最大连接数
        max_keepalive_connections=20,  # 最大保持连接数
    ),
    timeout=httpx.Timeout(60.0),  # 超时时间
)
```

### 缓存策略

**响应缓存**：
```python
# 缓存键设计
cache_key = f"{model}:{prompt_hash}:{temperature}"
```

**缓存策略**：
- 对相同的 prompt + 参数，使用缓存响应
- 缓存有效期：1 小时
- 对话任务不缓存（依赖上下文）

### 并发优化

**异步调用**：
```python
# 使用 async/await 实现并发调用
tasks = [invoke_llm(request) for request in requests]
responses = await asyncio.gather(*tasks)
```

**并发控制**：
- 限制最大并发数（避免触发限流）
- 使用信号量控制并发

---

## 最佳实践

### 1. 模型选择

**根据任务选择模型**：
- 简单任务使用 GPT-3.5-Turbo
- 复杂任务使用 GPT-4
- 长文本使用 Claude 2

**成本优化**：
- 监控 Token 使用量和成本
- 定期评估模型使用效率

### 2. 参数调优

**Temperature**：
- 创意性任务（如故事创作）：0.7-1.0
- 确定性任务（如代码生成）：0.0-0.3
- 对话任务：0.5-0.7

**Max Tokens**：
- 预估输出长度，避免浪费 Token
- 设置合理的上限，控制成本

### 3. 错误处理

**优雅降级**：
- 当主要模型不可用时，自动切换到备用模型
- 提供降级后的体验反馈

**监控告警**：
- 监控 API 调用成功率
- 设置合理的告警阈值

### 4. 可观测性

**日志记录**：
- 记录每次调用的参数、结果、Token 使用量
- 记录错误和重试情况

**指标统计**：
- Token 使用量、成本、延迟
- API 调用成功率、错误率
- 各模型的使用频率

---

## 总结

CPU 模块是 Nakari 的核心处理单元，通过 OpenAI / Anthropic API 实现了：

1. **模型抽象**：统一的 LLM 调用接口，屏蔽不同提供商的差异
2. **智能路由**：根据任务类型自动选择合适的模型
3. **可靠性**：完善的限流、重试、降级机制
4. **性能优化**：连接池、缓存、异步调用等优化手段
5. **可观测性**：完整的日志和指标统计

该模块的设计充分考虑了 LLM API 的特点和限制，通过智能的路由和优化策略，在保证响应质量的同时，最大化调用效率和成本效益。
