# Tasks - 任务调度系统

## 📋 目录
- [模块概述](#模块概述)
- [设计理念](#设计理念)
- [架构设计](#架构设计)
- [核心组件](#核心组件)
- [接口设计](#接口设计)
- [任务优先级策略](#任务优先级策略)\
- [错误处理与重试](#错误处理与重试)
- [分布式部署](#分布式部署)
- [性能优化](#性能优化)
- [可行性分析](#可行性分析)
- [最佳实践](#最佳实践)

---

## 模块概述

### 职责定位
Tasks 模块是 Nakari 的**并发控制中枢**，负责协调所有异步操作的调度、执行和监控。该模块不直接处理业务逻辑，而是提供统一的任务抽象层，让交互、反思、记忆读写等模块能够以声明式的方式定义并发行为。

### 设计目标
1. **任务抽象化**：所有功能模块通过统一的 Task 接口定义并发行为
2. **优先级管理**：确保关键任务（如用户对话）优先于后台任务（如反思）执行
3. **任务持久化**：即使 Worker 崩溃或重启，任务也不会丢失
4. **水平扩展**：支持单机多 Worker 和多机分布式部署
5. **解耦业务逻辑**：任务系统与具体业务逻辑完全解耦

### 技术选型

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| Celery | 5.3+ | 成熟的任务队列，支持 Redis broker，丰富的任务监控生态 |
| Redis | 7.0+ | 高性能消息代理，支持持久化，Celery 官方推荐 |
| beat | 内置 | 定时任务调度器，用于周期性触发反思任务 |

---

## 设计理念

### 任务化架构 (Task-Based Architecture)

**核心思想**：将 Nakari 的所有操作抽象为异步任务，而非同步函数调用。

#### 传统架构 vs 任务化架构

**传统架构**：1. 详细程度更深，理论上是这一个子模块的指导方针。2.不需要代码示例，但是需要向外暴露的接口设计。3.需要架构图 
```python
# 同步调用，阻塞主线程
response = chat_handler.process_message(message)
reflection_handler.update_memory(response)
audio_handler.synthesize_speech(response)
```

**任务化架构**：
```python
# 异步任务，非阻塞
chat_task.delay(message)  # 用户对话任务（高优先级）
# reflection_task.apply_async()  # 后台反思任务（低优先级，beat 触发）
# audio_task.delay(response)  # 语音合成任务（中优先级）
```

#### 任务化架构的优势

1. **并发隔离**：不同类型的任务互不阻塞
2. **故障隔离**：单个任务失败不影响其他任务
3. **资源调度**：可以针对不同任务类型分配不同资源
4. **弹性扩展**：根据负载动态调整 Worker 数量

### 优先级队列设计

Nakari 采用**三级优先级队列**，确保系统在资源有限时，优先保证用户体验。

#### 优先级定义

| 队列名称 | 优先级 | 典型任务 | 响应时间要求 |
|---------|--------|----------|--------------|
| `high` | 高 | 用户对话、紧急中断 | < 1s |
| `medium` | 中 | 语音合成、图像处理 | < 5s |
| `low` | 后台 | 反思、社区发现、日志清理 | 分钟级 |

#### 优先级调度策略

**Celery 配置示例**：
- 高优先级队列分配 60% Worker 资源
- 中优先级队列分配 30% Worker 资源
- 低优先级队列分配 10% Worker 资源

**动态调整**：
- 监控队列长度，当高优先级队列堆积时，自动降低中/低优先级任务的调度频率

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Nakari Application                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     Task Dispatcher                          │
│  (路由任务到不同优先级队列)                                    │
└───────┬───────────┬───────────────┬─────────────────────────┘
        │           │               │
   ┌────▼────┐  ┌───▼─────┐   ┌───▼──────┐
   │ High    │  │ Medium  │   │ Low      │
   │ Queue   │  │ Queue   │   │ Queue    │
   └────┬────┘  └───┬─────┘   └───┬──────┘
        │           │               │
        ▼           ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Celery Broker (Redis)                    │
│  - 任务持久化                                                  │
│  - 消息队列                                                   │
│  - 结果存储                                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     Celery Workers                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │
│  │Worker 1 │  │Worker 2 │  │Worker N │                      │
│  │(High)   │  │(Medium) │  │(Low)    │                      │
│  └────┬────┘  └────┬────┘  └────┬────┘                      │
│       │            │            │                            │
│       └────────────┴────────────┘                            │
│                    ▼                                          │
│         ┌─────────────────┐                                  │
│         │ Task Executor   │                                  │
│         │ - 调用业务逻辑   │                                  │
│         │ - 错误处理       │                                  │
│         │ - 重试机制       │                                  │
│         └─────────────────┘                                  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     Business Modules                         │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │ Chat   │  │ Audio  │  │ Vision │  │Reflect │            │
│  │ Thread │  │ Thread │  │ Thread │  │ Thread │            │
│  └────────┘  └────────┘  └────────┘  └────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 任务执行流程

```
用户输入/事件触发
       │
       ▼
┌──────────────────┐
│ Task Dispatcher │
│ - 任务类型识别   │
│ - 优先级分配     │
│ - 参数验证       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Celery Broker    │
│ - 任务持久化     │
│ - 队列路由       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Celery Worker    │
│ - 任务消费       │
│ - 执行业务逻辑   │
│ - 结果返回       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Result Backend   │
│ - 结果存储       │
│ - 状态查询       │
└──────────────────┘
```

---

## 核心组件

### 1. Task Dispatcher（任务分发器）

**职责**：
- 接收外部任务请求
- 验证任务参数
- 分配优先级和路由
- 返回任务 ID 和初始状态

**接口设计**：
```python
def dispatch_task(
    task_name: str,
    task_params: Dict[str, Any],
    priority: TaskPriority = TaskPriority.MEDIUM,
    callback_url: Optional[str] = None
) -> TaskResult:
    """
    分发任务到 Celery

    参数:
        task_name: 任务唯一标识（如 "chat.interaction"）
        task_params: 任务参数
        priority: 任务优先级
        callback_url: 任务完成回调地址（可选）

    返回:
        TaskResult 包含 task_id, status, queue
    """
```

### 2. Task Queue Manager（队列管理器）

**职责**：
- 监控队列长度和等待时间
- 动态调整 Worker 资源分配
- 识别任务堆积和瓶颈

**接口设计**：
```python
def get_queue_status(queue_name: str) -> QueueStatus:
    """
    获取队列状态

    返回:
        QueueStatus {
            length: int,           # 队列长度
            avg_wait_time: float,  # 平均等待时间（秒）
            throughput: float,     # 吞吐量（任务/秒）
        }
    """

def adjust_worker_pool(
    queue_name: str,
    target_worker_count: int
) -> bool:
    """
    动态调整 Worker 池大小

    返回:
        是否调整成功
    """
```

### 3. Task Monitor（任务监控器）

**职责**：
- 实时监控任务执行状态
- 检测任务失败和超时
- 触发告警和自动恢复

**接口设计**：
```python
def get_task_status(task_id: str) -> TaskStatus:
    """
    获取任务状态

    返回:
        TaskStatus {
            state: TaskState,       # PENDING, STARTED, SUCCESS, FAILURE
            progress: float,        # 进度（0-1）
            result: Any,            # 执行结果
            error: Optional[str],   # 错误信息
            start_time: datetime,
            end_time: Optional[datetime],
        }
    """

def cancel_task(task_id: str) -> bool:
    """
    取消任务执行

    返回:
        是否取消成功
    """
```

### 4. Task Scheduler（任务调度器）

**职责**：
- 定时触发周期性任务（如反思、社区发现）
- 管理任务依赖关系
- 处理任务链和任务组

**接口设计**：
```python
def schedule_periodic_task(
    task_name: str,
    schedule: str,  # cron 表达式
    task_params: Dict[str, Any]
) -> ScheduleResult:
    """
    调度周期性任务

    参数:
        schedule: cron 表达式（如 "0 */30 * * *" 每半小时）

    返回:
        ScheduleResult 包含 schedule_id, next_run_time
    """
```

---

## 接口设计

### 任务定义接口

所有任务必须遵循统一的接口规范：

```python
# 任务定义接口规范
class NakariTask:
    """
    Nakari 任务基类
    所有任务必须继承此类并实现核心方法
    """

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证任务参数

        返回:
            参数是否有效
        """
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> TaskResult:
        """
        执行任务逻辑

        返回:
            TaskResult 包含执行结果
        """
        pass

    @abstractmethod
    def on_failure(self, error: Exception) -> FailureHandler:
        """
        失败处理逻辑

        返回:
            FailureHandler 决定是否重试
        """
        pass

    @abstractmethod
    def get_metadata(self) -> TaskMetadata:
        """
        获取任务元数据

        返回:
            TaskMetadata {
                name: str,
                version: str,
                priority: TaskPriority,
                timeout: int,  # 超时时间（秒）
                max_retries: int,
            }
        """
        pass
```

### 任务执行接口

```python
# 外部调用接口
class TaskExecutor:
    """
    任务执行器
    供外部模块调用任务
    """

    def submit_task(
        self,
        task_type: TaskType,
        params: Dict[str, Any],
        options: Optional[TaskOptions] = None
    ) -> str:
        """
        提交任务

        参数:
            task_type: 任务类型枚举
            params: 任务参数
            options: 可选配置（优先级、回调等）

        返回:
            task_id: 任务唯一标识
        """
        pass

    def query_task(self, task_id: str) -> TaskStatus:
        """
        查询任务状态
        """
        pass

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        """
        pass

    def batch_submit_tasks(
        self,
        tasks: List[TaskSubmission]
    ) -> List[str]:
        """
        批量提交任务

        返回:
            task_ids: 任务 ID 列表
        """
        pass
```

### 任务回调接口

```python
# 任务回调接口
class TaskCallbackHandler:
    """
    任务完成后的回调处理
    """

    def on_success(
        self,
        task_id: str,
        result: TaskResult
    ) -> None:
        """
        任务成功回调
        """
        pass

    def on_failure(
        self,
        task_id: str,
        error: Exception
    ) -> None:
        """
        任务失败回调
        """
        pass

    def on_retry(
        self,
        task_id: str,
        retry_count: int,
        max_retries: int
    ) -> None:
        """
        任务重试回调
        """
        pass
```

---

## 任务优先级策略

### 优先级分配规则

**自动分配规则**：

| 任务来源 | 触发条件 | 优先级队列 |
|---------|---------|-----------|
| 用户主动输入 | 用户发送消息/语音/图像 | `high` |
| 交互线程响应 | 对话响应生成 | `high` |
| 语音合成 | 对话后 TTS | `medium` |
| 视觉处理 | 摄像头图像分析 | `medium` |
| 原子写入 | 新信息存入记忆 | `medium` |
| 原子读取 | 查询记忆 | `medium` |
| 反思任务 | 周期性触发 | `low` |
| 社区发现 | 周期性触发 | `low` |
| 图谱重构 | 周期性触发 | `low` |
| 日志清理 | 周期性触发 | `low` |

### 动态优先级调整

**场景 1：高优先级队列堆积**
- 检测条件：high 队列长度 > 阈值（如 100）
- 调整策略：暂停 low 队列调度，限制 medium 队列调度频率

**场景 2：系统负载过高**
- 检测条件：CPU 使用率 > 80% 或 内存使用率 > 90%
- 调整策略：动态降低所有队列的并发度

**场景 3：任务超时增加**
- 检测条件：任务平均执行时间 > 预期 2 倍
- 调整策略：检查 Worker 健康，必要时重启或扩容

---

## 错误处理与重试

### 错误分类

| 错误类型 | 处理策略 | 重试次数 | 重试间隔 |
|---------|---------|---------|---------|
| 临时性网络错误 | 立即重试 | 3 次 | 指数退避 |
| LLM API 限流 | 延迟重试 | 5 次 | 指数退避（基数 60s） |
| 数据库连接失败 | 延迟重试 | 3 次 | 固定间隔 5s |
| 任务超时 | 重试 | 2 次 | 超时时间翻倍 |
| 业务逻辑错误 | 不重试，告警 | 0 次 | - |
| 参数验证失败 | 不重试，返回错误 | 0 次 | - |

### 重试策略

**指数退避算法**：
```python
# 伪代码
retry_delay = base_delay * (2 ** retry_count)
max_delay = 300  # 最大 5 分钟
retry_delay = min(retry_delay, max_delay)
```

**重试限制**：
- 单任务最大重试次数：5 次
- 总重试时间上限：30 分钟
- 超过限制后标记为 `FAILURE`，并告警

### 失败任务处理

**死信队列（Dead Letter Queue）**：
- 所有失败超过重试限制的任务进入死信队列
- 死信队列定期检查，由人工或自动脚本分析

**失败告警**：
- 高优先级任务失败：立即告警（邮件/钉钉）
- 中优先级任务失败：批量告警（每小时汇总）
- 低优先级任务失败：每日日志汇总

---

## 分布式部署

### 单机多 Worker 部署

**场景**：开发环境或小规模部署

**架构**：
```
Single Server
├── Redis Server
├── Celery Worker (High Priority Queue) - 4 Concurrency
├── Celery Worker (Medium Priority Queue) - 2 Concurrency
└── Celery Worker (Low Priority Queue) - 1 Concurrency
```

**优势**：
- 部署简单
- 资源利用率高

**劣势**：
- 单点故障风险
- 扩展性受限

### 多机分布式部署

**场景**：生产环境或大规模部署

**架构**：
```
Load Balancer
      │
      ├─ Worker Server 1 (High Priority)
      │   └── 4 Workers
      │
      ├─ Worker Server 2 (Medium Priority)
      │   └── 2 Workers
      │
      ├─ Worker Server 3 (Low Priority)
      │   └── 2 Workers
      │
      └─ Redis Cluster
          ├─ Redis Master 1
          ├─ Redis Master 2
          └── Redis Slave (Replica)
```

**优势**：
- 高可用性
- 水平扩展
- 故障隔离

**挑战**：
- 部署复杂度增加
- 网络延迟

### Worker 配置策略

**CPU 密集型任务**（如 LLM 调用）：
- 并发度 = CPU 核心数
- 使用 `prefork` 模式

**IO 密集型任务**（如数据库查询）：
- 并发度 = CPU 核心数 × 2-4
- 使用 `gevent` 或 `eventlet` 模式

---

## 性能优化

### Celery 配置优化

**Broker 连接池**：
- 最大连接数 = Worker 数量 × 2
- 连接超时 = 30s

**结果存储优化**：
- 禁用不必要的任务结果存储
- 使用 Redis `result_expires` 自动过期

**任务序列化优化**：
- 优先使用 `json` 序列化（快）
- 避免使用 `pickle`（有安全风险）

### 任务批处理

**适用场景**：
- 原子批量写入
- 批量语音转文字
- 批量图像处理

**接口设计**：
```python
def batch_process_items(
    items: List[Dict[str, Any]],
    batch_size: int = 100
) -> List[TaskResult]:
    """
    批量处理任务

    参数:
        batch_size: 每批处理的数量

    返回:
        所有任务的结果列表
    """
    pass
```

### 任务预取

**优化点**：
- Worker 预取一定数量的任务，减少 broker 交互
- 预取量 = 并发度 × 2

---

## 可行性分析

### 技术可行性

**Celery + Redis 成熟度**：
- Celery 是 Python 生态中最成熟的任务队列框架
- Redis 是 Celery 官方推荐的 broker
- 大量生产环境验证（Instagram、Mozilla 等）

**性能指标**：
- 吞吐量：单 Worker 可处理 1000+ 任务/分钟（简单任务）
- 延迟：任务提交到开始执行 < 100ms（正常负载）
- 可靠性：任务持久化，99.9% 任务不丢失

### 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Redis 单点故障 | 中 | 高 | 使用 Redis Cluster 或 Sentinel |
| Celery 内存泄漏 | 低 | 中 | 定期重启 Worker，监控内存 |
| 任务积压 | 中 | 中 | 动态扩容 Worker |
| 任务重复执行 | 低 | 中 | 任务幂等性设计 |

### 扩展性分析

**水平扩展**：
- 增加 Worker 数量可线性提升吞吐量
- 预计支持 10000+ 并发任务

**垂直扩展**：
- 增加 Worker 服务器 CPU/内存可提升单机性能
- 预计单机支持 1000+ 并发任务

---

## 最佳实践

### 1. 任务设计原则

**单一职责**：
- 每个任务只做一件事
- 避免任务嵌套调用其他任务

**幂等性**：
- 任务多次执行结果一致
- 防止重复处理

**无状态**：
- 任务不依赖外部状态
- 所有必要参数通过参数传递

### 2. 监控指标

**关键指标**：
- 任务吞吐量（tasks/second）
- 任务延迟（P50, P95, P99）
- 任务成功率
- 队列长度
- Worker 资源利用率

**告警阈值**：
- 任务延迟 > 5s（P95）
- 任务失败率 > 5%
- 队列长度 > 1000

### 3. 测试策略

**单元测试**：
- 模拟任务执行逻辑
- 验证参数验证
- 测试错误处理

**集成测试**：
- 使用真实的 Celery broker
- 测试任务提交和查询
- 验证重试机制

**压力测试**：
- 模拟高负载场景
- 测试队列堆积情况
- 验证动态调整策略

---

## 总结

Tasks 模块是 Nakari 的并发控制中枢，通过 Celery + Redis 实现了：

1. **任务抽象化**：统一的任务定义和执行接口
2. **优先级管理**：三级队列确保关键任务优先
3. **高可用性**：任务持久化和分布式部署支持
4. **可观测性**：完整的监控和告警机制
5. **可扩展性**：水平扩展支持 10000+ 并发任务

该模块的设计充分考虑了 Nakari 的核心需求，技术选型成熟可靠，具备良好的可行性和扩展性。
