# Modeling - 3D 建模模块

## 📋 目录
- [模块概述](#模块概述)
- [设计理念](#设计理念)
- [架构设计](#架构设计)
- [核心组件](#核心组件)
- [接口设计](#接口设计)
- [3D 模型设计](#3d-模型设计)
- [动画系统](#动画系统)
- [场景管理](#场景管理)
- [渲染优化](#渲染优化)
- [最佳实践](#最佳实践)

---

## 模块概述

### 职责定位
Modeling 模块是 Nakari 的**3D 形象系统**，负责 3D 模型的创建、动画和渲染。该模块让 Nakari 从平面的 2D 对话框中解放出来，拥有 3D 形象、动作、行为举止。

### 设计目标
1. **高保真模型**：创建高质量的 3D 模型，展现 Nakari 的独特形象
2. **自然动画**：实现自然的说话、表情、手势动画
3. **场景化**：支持多个生活场景，随时间或对话切换
4. **实时渲染**：实时渲染 3D 模型和动画
5. **个性化**：支持模型和场景的个性化定制

### 技术选型

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| Unity | 2022+ | 成熟的 3D 引擎，支持跨平台 |
| Three.js | 0.160+ | Web 端 3D 渲染 |
| Blender | 4.0+ | 开源的 3D 建模工具 |
| Mixamo | API | 自动化角色动画 |

---

## 设计理念

### 3D 形象的生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                    3D 形象的生命周期                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ 模型创建  │   │ 动画系统  │   │ 场景管理  │
    │ Modeling │   │Animation│   │  Scene  │
    └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │
         ▼             ▼             ▼
    ┌─────────────────────────────────────┐
    │        实时渲染 Real-time          │
    │            Rendering              │
    └─────────────────────────────────────┘
```

### 3D 形象的意义

**从平面到立体**：
- 2D 对话框 → 3D 虚拟形象
- 文字交流 → 动作和表情交流
- 静态展示 → 动态行为

**人格的外在表现**：
- 动作和行为举止也是人格的重要组成部分
- 提供更深厚的陪伴感
- 增强用户沉浸感

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Nakari Backend                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     Modeling Module                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Model Asset  │  │ Animation    │  │ Scene        │     │
│  │ Manager      │  │ System       │  │ Manager      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                   │
│                           ▼                                   │
│                  Rendering Engine                           │
│           ┌─────────────────────────────┐                   │
│           │ - 3D Model Rendering       │                   │
│           │ - Animation Blending       │                   │
│           │ - Scene Management        │                   │
│           │ - Lighting & Effects      │                   │
│           └─────────────────────────────┘                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Rendering Platform                        │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│  │ Unity   │         │Three.js │         │ Unreal  │       │
│  │ Engine  │         │ WebGL   │         │ Engine  │       │
│  └─────────┘         └─────────┘         └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. Model Asset Manager（模型资源管理器）

**职责**：
- 管理 3D 模型资源
- 模型加载和卸载
- 模型缓存

**接口设计**：
```python
async def load_model(
    model_id: str,
    model_path: str
) -> Model3D:
    """
    加载 3D 模型

    参数:
        model_id: 模型 ID
        model_path: 模型文件路径

    返回:
        Model3D: 3D 模型对象
    """
    pass

async def unload_model(
    model_id: str
) -> bool:
    """
    卸载 3D 模型

    参数:
        model_id: 模型 ID

    返回:
        是否卸载成功
    """
    pass
```

### 2. Animation System（动画系统）

**职责**：
- 管理动画资源
- 动画混合和过渡
- 唇形同步

**接口设计**：
```python
def play_animation(
    model_id: str,
    animation_name: str,
    loop: bool = False,
    blend_duration: float = 0.3
) -> None:
    """
    播放动画

    参数:
        model_id: 模型 ID
        animation_name: 动画名称
        loop: 是否循环播放
        blend_duration: 混合过渡时间（秒）
    """
    pass

def blend_animations(
    model_id: str,
    animations: List[Tuple[str, float]]
) -> None:
    """
    混合多个动画

    参数:
        model_id: 模型 ID
        animations: 动画列表（名称, 权重）
    """
    pass
```

### 3. Scene Manager（场景管理器）

**职责**：
- 管理场景资源
- 场景切换
- 场景状态管理

**接口设计**：
```python
async def load_scene(
    scene_id: str,
    scene_path: str
) -> Scene:
    """
    加载场景

    参数:
        scene_id: 场景 ID
        scene_path: 场景文件路径

    返回:
        Scene: 场景对象
    """
    pass

async def switch_scene(
    scene_id: str,
    transition: str = "fade"
) -> None:
    """
    切换场景

    参数:
        scene_id: 目标场景 ID
        transition: 过渡效果（fade/cut/slide）
    """
    pass
```

---

## 接口设计

### Modeling 模块接口

```python
class ModelingModule:
    """
    Modeling 模块
    统一的 3D 建模接口
    """

    def __init__(
        self,
        rendering_engine: str = "unity",
        default_model: str = "nakari_base",
        default_scene: str = "living_room"
    ):
        """
        初始化 Modeling 模块

        参数:
            rendering_engine: 渲染引擎（unity/threejs/unreal）
            default_model: 默认模型
            default_scene: 默认场景
        """
        pass

    async def load_model(
        self,
        model_id: str,
        model_path: str
    ) -> None:
        """
        加载 3D 模型
        """
        pass

    async def play_animation(
        self,
        animation_name: str,
        loop: bool = False
    ) -> None:
        """
        播放动画
        """
        pass

    async def speak(
        self,
        text: str,
        emotion: Optional[str] = None
    ) -> None:
        """
        说话动画

        参数:
            text: 说话文本
            emotion: 情感（可选）
        """
        pass

    async def set_expression(
        self,
        expression: str
    ) -> None:
        """
        设置表情

        参数:
            expression: 表情名称
        """
        pass

    async def switch_scene(
        self,
        scene_id: str
    ) -> None:
        """
        切换场景
        """
        pass

    def get_current_state(self) -> ModelState:
        """
        获取当前状态

        返回:
            ModelState {
                model_id: str,
                animation: str,
                expression: str,
                scene_id: str,
            }
        """
        pass
```

---

## 3D 模型设计

### 模型风格

**可选风格**：
- `anime`: 动漫风格
- `realistic`: 写实风格
- `cartoon`: 卡通风格
- `chibi`: Q 版风格

### 模型组件

**基础组件**：
- 头部（面部、眼睛、嘴巴）
- 身体（躯干、手臂、腿）
- 头发
- 服装

**可选组件**：
- 配饰（眼镜、帽子等）
- 道具（书本、咖啡杯等）

### 模型文件格式

**支持格式**：
- `.fbx`: 通用 3D 模型格式
- `.gltf` / `.glb`: Web 友好的 3D 格式
- `.obj`: 简单的 3D 格式

---

## 动画系统

### 动画类型

**基础动画**：
- `idle`: 待机动画
- `walk`: 行走动画
- `run`: 奔跑动画
- `jump`: 跳跃动画

**表情动画**：
- `happy`: 开心表情
- `sad`: 悲伤表情
- `angry`: 愤怒表情
- `surprise`: 惊讶表情
- `neutral`: 中性表情

**交互动画**：
- `greeting`: 打招呼
- `goodbye`: 再见
- `nod`: 点头
- `shake_head`: 摇头

### 唇形同步

**原理**：
- 根据语音生成唇形动画
- 使用音素映射表
- 实时同步语音和唇形

**实现方式**：
- 预定义的唇形关键帧
- 基于音素的关键帧插值
- 使用 OGG Lip Sync 或 Rhubarb Lip Sync

### 动画混合

**混合策略**：
- 基于权重的动画混合
- 平滑过渡（避免跳跃）
- 支持多个动画同时播放

---

## 场景管理

### 场景类型

**生活场景**：
- `living_room`: 客厅
- `bedroom`: 卧室
- `kitchen`: 厨房
- `garden`: 花园
- `cafe`: 咖啡馆

**季节场景**：
- `spring`: 春天
- `summer`: 夏天
- `autumn`: 秋天
- `winter`: 冬天

### 场景切换

**切换触发**：
- 时间变化（白天/黑夜）
- 季节变化
- 对话主题变化
- 用户主动切换

**切换效果**：
- `fade`: 渐变
- `cut`: 切换
- `slide`: 滑动
- `dissolve`: 溶解

---

## 渲染优化

### 模型优化

**LOD（Level of Detail）**：
- 根据距离使用不同细节的模型
- 近距离使用高精度模型
- 远距离使用低精度模型

**网格优化**：
- 减少面数
- 合并相似的面
- 移除不可见的面

### 材质优化

**纹理压缩**：
- 使用压缩纹理格式
- 减少纹理分辨率

**着色器优化**：
- 使用简化的着色器
- 减少计算复杂度

### 渲染优化

**批处理**：
- 批量渲染相似的对象
- 减少 draw call

**视锥剔除**：
- 只渲染视锥内的对象
- 提前剔除不可见对象

---

## 最佳实践

### 1. 模型设计

**保持一致性**：
- 统一的风格和比例
- 一致的材质和光照

**优化性能**：
- 控制模型面数（< 50K）
- 使用合理的纹理分辨率（<= 2048x2048）

### 2. 动画设计

**自然流畅**：
- 使用缓入缓出
- 避免生硬的过渡

**符合角色**：
- 动画要符合角色性格
- 表情要自然

### 3. 场景设计

**丰富多样**：
- 提供多个场景
- 场景之间有明显区别

**优化性能**：
- 控制场景复杂度
- 使用合理的光照和阴影

---

## 总结

Modeling 模块是 Nakari 的 3D 形象系统，通过 Unity / Three.js / Blender 等技术实现了：

1. **高保真模型**：创建高质量的 3D 模型，展现 Nakari 的独特形象
2. **自然动画**：实现自然的说话、表情、手势动画
3. **场景化**：支持多个生活场景，随时间或对话切换
4. **实时渲染**：实时渲染 3D 模型和动画
5. **个性化**：支持模型和场景的个性化定制

该模块让 Nakari 从平面的 2D 对话框中解放出来，拥有 3D 形象、动作、行为举止，能在一个虚拟空间中生活及移动，为用户提供更深厚的陪伴感。
