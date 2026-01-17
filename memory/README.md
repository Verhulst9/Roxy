# Memory - 离散原子网络模块

## 📋 目录
- [模块概述](#模块概述)
- [设计理念](#设计理念)
- [架构设计](#架构设计)
- [核心组件](#核心组件)
- [接口设计](#接口设计)
- [原子管理](#原子管理)
- [图结构](#图结构)
- [检索机制](#检索机制)
- [反思与重构](#反思与重构)
- [性能优化](#性能优化)
- [最佳实践](#最佳实践)

---

## 模块概述

### 职责定位
Memory 模块是 Nakari 的**记忆存储与管理系统**，基于离散原子网络（Discrete Atom Network）实现长期记忆的存储、检索和管理。该模块不采用传统的实体-关系模型，而是通过灵活的原子结构和无信息的边连接，实现语义的"涌现"式推理。

### 设计目标
1. **灵活存储**：支持不等长的原子结构，不受预定义 schema 限制
2. **语义检索**：基于向量的语义检索，快速找到相关原子
3. **图遍历**：支持图的遍历和子图提取，发现原子间的隐含关系
4. **反思重构**：定期反思和重构图谱，模拟人类记忆固化过程
5. **社区发现**：自动发现图中的稠密子图，实现记忆压缩

### 技术选型

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| Neo4j | 5.0+ | 原生图数据库，支持向量索引和图算法 |
| Neo4j GDS | 2.0+ | 提供社区发现、图遍历等算法 |
| LangChain | 0.1+ | 集成向量检索和图遍历的抽象层 |

---

## 设计理念

### 离散原子网络核心思想

**与传统 ER 模型的区别**：

| 维度 | 传统 ER 模型 | 离散原子网络 |
|------|-------------|-------------|
| 边 | 有方向、类型、权重 | 无任何信息 |
| 语义 | 预先存储关系 | 从原子内容中"涌现" |
| Schema | 固定表结构 | 灵活的 key-value |
| 推理 | 关系查询 | 图遍历 + LLM 推断 |

### 原子设计理念

**核心原则**：
- **边无信息**：连接两个原子的边只是一个纯粹的连接
- **语义延迟推断**：不预先存储语义关系，只在需要时从原子内容中"涌现"
- **完全灵活的原子结构**：原子可以有不等长个数的 key-value 对

### 记忆的生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                    记忆的生命周期                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ 写入阶段 │   │ 读取阶段 │   │ 反思阶段 │
    │  Write  │   │  Read   │   │Reflect  │
    └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │
         ▼             ▼             ▼
    指代消解       语义检索       模式识别
    原子提取       图遍历扩展     创造高阶原子
    向量化        语义推断       图谱重构
    连接创建                    社区发现
```

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
│                      Memory Module                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Atom Manager │  │ Graph Query  │  │ Reflection   │     │
│  │ 原子管理器    │  │ 图查询引擎    │  │ 反思引擎      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                   │
│                           ▼                                   │
│                  Neo4j Graph Database                       │
│           ┌─────────────────────────────┐                   │
│           │ - Atom Nodes (with Vectors) │                   │
│           │ - Unlabeled Edges          │                   │
│           │ - Vector Index             │                   │
│           │ - Graph Algorithms          │                   │
│           └─────────────────────────────┘                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   Translation Middleware                       │
│              (Atomizer & Synthesizer)                        │
└─────────────────────────────────────────────────────────────┘
```

### 原子写入流程

```
用户输入
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
│ 原子提取 (LLM)    │
│ - 语义分割       │
│ - 去重判断       │
│ - 关系判断       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 向量化           │
│ - 生成 embedding │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 连接创建         │
│ - 创建原子连接   │
│ - 存入 Neo4j     │
└──────────────────┘
```

### 原子读取流程

```
用户查询
    │
    ▼
┌──────────────────┐
│ 向量检索         │
│ - Top-K 检索     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 图遍历扩展       │
│ - 向外扩展 N 层  │
│ - 构建子图       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 语义推断 (LLM)    │
│ - 分析子图结构   │
│ - 推断语义关系   │
│ - 生成自然语言   │
└────────┬─────────┘
         │
         ▼
    返回结果
```

---

## 核心组件

### 1. Atom Manager（原子管理器）

**职责**：
- 原子的创建、更新、删除
- 原子的向量化
- 原子的去重和合并

**接口设计**：
```python
def create_atom(
    content: str,
    extensions: Optional[Dict[str, Any]] = None,
    embeddings: Optional[List[float]] = None
) -> Atom:
    """
    创建原子

    参数:
        content: 原子内容
        extensions: 扩展属性（可选）
        embeddings: 向量表示（可选，未提供则自动生成）

    返回:
        Atom: 创建的原子对象
    """
    pass

def update_atom(
    atom_id: str,
    content: Optional[str] = None,
    extensions: Optional[Dict[str, Any]] = None
) -> Atom:
    """
    更新原子

    参数:
        atom_id: 原子 ID
        content: 新内容（可选）
        extensions: 扩展属性（可选）

    返回:
        Atom: 更新后的原子对象
    """
    pass

def delete_atom(atom_id: str) -> bool:
    """
    删除原子

    参数:
        atom_id: 原子 ID

    返回:
        是否删除成功
    """
    pass
```

### 2. Graph Query Engine（图查询引擎）

**职责**：
- 向量检索（语义检索）
- 图遍历（子图提取）
- 混合查询（向量 + 图遍历）

**接口设计**：
```python
def vector_search(
    query: str,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Atom]:
    """
    向量检索

    参数:
        query: 查询文本
        top_k: 返回结果数量
        filters: 过滤条件（可选）

    返回:
        List[Atom]: 检索到的原子列表
    """
    pass

def traverse_graph(
    start_atom_ids: List[str],
    max_depth: int = 2,
    max_nodes: int = 100
) -> Subgraph:
    """
    图遍历

    参数:
        start_atom_ids: 起始原子 ID 列表
        max_depth: 最大遍历深度
        max_nodes: 最大节点数

    返回:
        Subgraph: 子图结构
    """
    pass

def hybrid_search(
    query: str,
    top_k: int = 10,
    max_depth: int = 2
) -> Subgraph:
    """
    混合检索（向量 + 图遍历）

    参数:
        query: 查询文本
        top_k: 向量检索数量
        max_depth: 图遍历深度

    返回:
        Subgraph: 子图结构
    """
    pass
```

### 3. Reflection Engine（反思引擎）

**职责**：
- 模式识别（发现潜在的语义模式）
- 创造高阶原子（升维抽象）
- 图谱重构（优化图结构）

**接口设计**：
```python
def detect_patterns(
    time_range: Optional[Tuple[datetime, datetime]] = None,
    atom_ids: Optional[List[str]] = None
) -> List[Pattern]:
    """
    模式识别

    参数:
        time_range: 时间范围（可选）
        atom_ids: 指定原子 ID 列表（可选）

    返回:
        List[Pattern]: 检测到的模式列表
    """
    pass

def create_higher_order_atom(
    pattern: Pattern,
    related_atom_ids: List[str]
) -> Atom:
    """
    创造高阶原子

    参数:
        pattern: 模式对象
        related_atom_ids: 相关原子 ID 列表

    返回:
        Atom: 创建的高阶原子
    """
    pass

def restructure_graph(
    atoms_to_remove: List[str],
    atoms_to_add: List[Atom],
    edges_to_add: List[Tuple[str, str]]
) -> bool:
    """
    图谱重构

    参数:
        atoms_to_remove: 要删除的原子 ID 列表
        atoms_to_add: 要添加的原子列表
        edges_to_add: 要添加的边列表

    返回:
        是否重构成功
    """
    pass
```

---

## 接口设计

### Memory 模块接口

```python
class MemoryModule:
    """
    Memory 模块
    统一的记忆管理接口
    """

    def write(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Atom]:
        """
        写入记忆

        参数:
            text: 文本内容
            metadata: 元数据（可选）

        返回:
            List[Atom]: 创建的原子列表
        """
        pass

    def read(
        self,
        query: str,
        top_k: int = 10,
        max_depth: int = 2
    ) -> Subgraph:
        """
        读取记忆

        参数:
            query: 查询文本
            top_k: 向量检索数量
            max_depth: 图遍历深度

        返回:
            Subgraph: 子图结构
        """
        pass

    def reflect(self) -> ReflectionResult:
        """
        反思和重构

        返回:
            ReflectionResult {
                patterns_detected: int,
                higher_order_atoms_created: int,
                atoms_removed: int,
                communities_found: int,
            }
        """
        pass

    def get_atom(self, atom_id: str) -> Optional[Atom]:
        """
        获取单个原子

        参数:
            atom_id: 原子 ID

        返回:
            Atom: 原子对象（如果存在）
        """
        pass

    def get_stats(self) -> MemoryStats:
        """
        获取记忆统计

        返回:
            MemoryStats {
                total_atoms: int,
                total_edges: int,
                avg_connections: float,
                largest_community: int,
            }
        """
        pass
```

---

## 原子管理

### 原子结构

**基本属性**（必须包含）：
```python
class Atom:
    id: str                # 唯一标识符
    content: str           # 原子核心内容
    embedding: List[float] # 向量化表示
    timestamp: datetime     # 最新时间戳
```

**扩展属性**（可选，由 LLM 自由决定）：
```python
extensions: Dict[str, Any]  # 任意 key-value 对
```

**扩展属性示例**：
```json
{
  "tags": ["entity", "person"],
  "is_user": true,
  "confidence": 0.95,
  "previous_confidence": "0.9",
  "speaker": "nakari",
  "sentiment": "negative"
}
```

### 原子类型

| 类型 | Content 示例 | 典型 Tags | 用途 |
|------|-------------|----------|------|
| 实体原子 | "Wenki" | entity, person | 表示具体实体 |
| 事件原子 | "熬夜" | event, behavior | 表示事件或行为 |
| 概念原子 | "喜欢" | relation | 表示关系或概念 |
| 复合原子 | "我觉得你熬夜不好" | opinion, statement | 表示复杂概念 |
| 高阶原子 | "用户正在经历自我封闭期" | insight, pattern | 反思得出的抽象 |

### 指代消解

**功能**：
- 推断人称代词为具体实体
- 推断指代地点为具体地点
- 基于 LLM 对话上下文进行消解

**示例**：
```
输入: "他昨天去那里了"
消解后: "Wenki 在 2024-01-16 去了办公室"
```

### 时间绝对化

**功能**：
- 转换时间代词为具体时间戳
- 相对于当前对话时间进行计算

**示例**：
```
输入: "昨天"
当前时间: 2024-01-17
绝对化后: 2024-01-16
```

---

## 图结构

### 边的设计

**边无信息**：
- 无方向
- 无类型
- 无权重
- 仅表示两个原子之间存在连接

**边的创建规则**：
- 由 LLM 判断两个原子是否应该连接
- 连接不表示任何语义关系
- 语义关系从原子内容中"涌现"

### 子图提取

**遍历策略**：
- 从检索到的原子出发
- 向外扩展 N 层
- 限制最大节点数

**子图表示**：
```python
class Subgraph:
    atoms: List[Atom]          # 原子列表
    edges: List[Tuple[str, str]]  # 边列表（原子 ID 对）
```

### 社区发现

**算法**：Louvain 或 Leiden

**目的**：
- 发现图中的稠密子图
- 识别相关的原子簇
- 实现记忆压缩

**输出**：
- 每个社区包含的原子 ID
- 社区摘要原子

---

## 检索机制

### 向量检索

**流程**：
1. 将查询文本向量化
2. 在 Neo4j 中进行向量检索
3. 返回 Top-K 相关原子

**参数**：
- `top_k`: 返回结果数量（默认 10）
- `filters`: 过滤条件（如按 tags 过滤）

### 图遍历

**流程**：
1. 从检索到的原子出发
2. 广度优先遍历
3. 限制遍历深度和节点数

**参数**：
- `max_depth`: 最大遍历深度（默认 2）
- `max_nodes`: 最大节点数（默认 100）

### 混合检索

**流程**：
1. 先进行向量检索
2. 再对结果进行图遍历扩展
3. 返回最终的子图

**优势**：
- 结合语义检索和图遍历
- 提高检索的准确性和覆盖面

---

## 反思与重构

### 模式识别

**机制**：
- 定期扫描近期生成的原子
- 寻找潜在的模式和关联
- 识别可抽象的高阶概念

**示例**：
```
原始原子:
- Atom A: 熬夜
- Atom B: 吃泡面
- Atom C: 也不出门

模式识别:
- 三者在生活状态维度高度相关
- 暗示用户可能处于自我封闭期
```

### 创造高阶原子

**机制**：
- 基于识别的模式
- 创建新的高阶原子
- 将高阶原子与相关原子连接

**示例**：
```
创建的高阶原子:
- Atom D: "用户正在经历自我封闭期"
- 连接: D -- A, D -- B, D -- C
```

### 图谱重构

**机制**：
- 删除冗余或低质量原子
- 优化图结构
- 提高检索效率

**重构触发条件**：
- 定期触发（如每天）
- 原子数量超过阈值（如 10000）
- 检索性能下降

### 社区发现与摘要

**流程**：
1. 运行社区发现算法
2. 识别稠密子图
3. 为每个社区生成摘要原子

**示例**：
```
社区: {2023暑假旅行相关原子}
摘要原子: "2023年暑假，Wenki 和朋友去了日本旅行，主要去了东京和大阪"
```

---

## 性能优化

### 向量索引优化

**Neo4j 向量索引配置**：
```cypher
CREATE VECTOR INDEX atom_embedding_index
FOR (a:Atom)
ON (a.embedding)
OPTIONS {
  indexConfig: {
    `vector.similarity_function`: 'cosine'
  }
}
```

### 批量操作

**批量写入**：
```python
def batch_write_atoms(atoms: List[Atom]) -> bool:
    """
    批量写入原子

    参数:
        atoms: 原子列表

    返回:
        是否写入成功
    """
    pass
```

**批量向量化**：
- 使用批量 API 生成向量
- 减少网络开销

### 缓存策略

**缓存常用子图**：
```python
subgraph_cache = {}

def get_cached_subgraph(query: str) -> Optional[Subgraph]:
    """
    获取缓存的子图

    参数:
        query: 查询文本

    返回:
        Subgraph: 缓存的子图（如果存在）
    """
    pass
```

---

## 最佳实践

### 1. 原子设计

**灵活使用扩展属性**：
- 让 LLM 自由决定扩展字段
- 避免过度约束原子结构

**保持原子粒度适中**：
- 太细：原子数量爆炸
- 太粗：语义表达不精确

### 2. 边管理

**谨慎创建连接**：
- 由 LLM 判断是否需要连接
- 避免过度连接导致图过于稠密

**定期清理**：
- 删除孤立的原子
- 清理冗余的连接

### 3. 检索策略

**合理设置检索参数**：
- `top_k`: 根据任务需求调整（5-20）
- `max_depth`: 2-3 层足够
- `max_nodes`: 防止子图过大

**结合过滤条件**：
- 按 tags 过滤
- 按时间范围过滤
- 提高检索精度

### 4. 反思策略

**定期触发反思**：
- 每天触发一次
- 或原子数量达到阈值时触发

**渐进式重构**：
- 逐步优化图结构
- 避免一次性大规模重构

---

## 总结

Memory 模块是 Nakari 的记忆存储与管理系统，基于离散原子网络实现了：

1. **灵活存储**：支持不等长的原子结构，不受预定义 schema 限制
2. **语义检索**：基于向量的语义检索，快速找到相关原子
3. **图遍历**：支持图的遍历和子图提取，发现原子间的隐含关系
4. **反思重构**：定期反思和重构图谱，模拟人类记忆固化过程
5. **社区发现**：自动发现图中的稠密子图，实现记忆压缩

该模块的设计摒弃了传统的 ER 模型，通过无信息的边和灵活的原子结构，实现了语义的"涌现"式推理，为 Nakari 提供了一个强大而灵活的记忆系统。
