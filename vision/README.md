# Vision - 视觉处理模块

## 📋 目录
- [模块概述](#模块概述)
- [设计理念](#设计理念)
- [架构设计](#架构设计)
- [核心组件](#核心组件)
- [接口设计](#接口设计)
- [图像处理](#图像处理)
- [视频流处理](#视频流处理)
- [摄像头交互](#摄像头交互)
- [错误处理](#错误处理)
- [性能优化](#性能优化)
- [最佳实践](#最佳实践)

---

## 模块概述

### 职责定位
Vision 模块是 Nakari 的**视觉感知系统**，负责图像处理、计算机视觉和摄像头交互。该模块让 Nakari 能够通过摄像头读取外部画面，实现双向的视觉交互。

### 设计目标
1. **实时视觉感知**：实时处理摄像头画面，延迟控制在 100ms 以内
2. **多场景识别**：支持人脸识别、物体检测、场景理解等多场景
3. **低延迟**：实时视频流处理，保证交互流畅性
4. **高精度**：准确识别和理解视觉信息
5. **隐私保护**：本地处理，不上传敏感图像数据

### 技术选型

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| OpenCV | 4.8+ | 成熟的计算机视觉库，功能全面 |
| MediaPipe | 0.10+ | 轻量级，支持人脸、手势识别 |
| CLIP | 1.0+ | 图像-文本跨模态理解 |
| FFmpeg | 5.0+ | 视频流处理和格式转换 |

---

## 设计理念

### 视觉交互流程

```
┌─────────────────────────────────────────────────────────────┐
│                    视觉交互流程                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
    ┌─────────┐                   ┌─────────┐
    │ 摄像头   │                   │ 视觉分析  │
    │ 采集     │                   │ 理解     │
    └────┬────┘                   └────┬────┘
         │                             │
         ▼                             ▼
    视频流输入                     视觉特征提取
    (摄像头)                      (视觉理解)
         │                             │
         ▼                             ▼
    ┌─────────────────────────────────────┐
    │      Nakari 视觉理解与响应           │
    └─────────────────────────────────────┘
```

### 双向视觉交互

**从 Nakari 看用户**：
- 人脸识别（用户身份）
- 表情识别（情绪状态）
- 手势识别（交互指令）

**从用户看 Nakari**：
- 显示 Nakari 的虚拟形象
- 视觉反馈和表情变化

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
│                      Vision Module                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Capture      │  │ Analysis     │  │ Understanding│     │
│  │ 视频采集     │  │ 视觉分析      │  │ 视觉理解      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                   │
│                           ▼                                   │
│                  Video Processor                             │
│           ┌─────────────────────────────┐                   │
│           │ - Frame Extraction         │                   │
│           │ - Color Correction        │                   │
│           │ - Noise Reduction         │                   │
│           │ - Frame Buffering         │                   │
│           └─────────────────────────────┘                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Libraries                        │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│  │ OpenCV  │         │MediaPipe│        │ CLIP    │       │
│  │         │         │         │        │         │       │
│  └─────────┘         └─────────┘         └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. Capture Engine（视频采集引擎）

**职责**：
- 从摄像头采集视频流
- 帧提取和缓冲
- 视频预处理

**接口设计**：
```python
async def start_camera(
    camera_id: int = 0,
    resolution: Tuple[int, int] = (1280, 720),
    fps: int = 30
) -> CameraStream:
    """
    启动摄像头

    参数:
        camera_id: 摄像头 ID
        resolution: 分辨率（宽, 高）
        fps: 帧率

    返回:
        CameraStream: 摄像头流对象
    """
    pass

async def capture_frame(
    camera_stream: CameraStream
) -> Optional[np.ndarray]:
    """
    采集一帧

    参数:
        camera_stream: 摄像头流对象

    返回:
        frame: 帧图像（BGR 格式），如果没有帧则返回 None
    """
    pass
```

### 2. Analysis Engine（视觉分析引擎）

**职责**：
- 人脸检测和识别
- 表情识别
- 手势识别
- 物体检测

**接口设计**：
```python
def detect_faces(
    frame: np.ndarray
) -> List[Face]:
    """
    检测人脸

    参数:
        frame: 帧图像

    返回:
        List[Face]: 检测到的人脸列表
    """
    pass

def recognize_faces(
    frame: np.ndarray
) -> List[FaceRecognition]:
    """
    识别人脸

    参数:
        frame: 帧图像

    返回:
        List[FaceRecognition]: 人脸识别结果
    """
    pass

def detect_emotions(
    frame: np.ndarray,
    face_boxes: List[BoundingBox]
) -> List[Emotion]:
    """
    识别表情

    参数:
        frame: 帧图像
        face_boxes: 人脸边界框列表

    返回:
        List[Emotion]: 表情识别结果
    """
    pass

def detect_gestures(
    frame: np.ndarray
) -> List[Gesture]:
    """
    检测手势

    参数:
        frame: 帧图像

    返回:
        List[Gesture]: 手势识别结果
    """
    pass
```

### 3. Understanding Engine（视觉理解引擎）

**职责**：
- 场景理解
- 图像描述生成
- 视觉问答

**接口设计**：
```python
async def understand_scene(
    image: np.ndarray
) -> SceneUnderstanding:
    """
    理解场景

    参数:
        image: 图像

    返回:
        SceneUnderstanding {
            scene_type: str,        # 场景类型
            objects: List[str],      # 检测到的物体
            description: str,       # 场景描述
            confidence: float,       # 置信度
        }
    """
    pass

async def describe_image(
    image: np.ndarray
) -> str:
    """
    描述图像

    参数:
        image: 图像

    返回:
        description: 图像描述
    """
    pass

async def visual_qa(
    image: np.ndarray,
    question: str
) -> str:
    """
    视觉问答

    参数:
        image: 图像
        question: 问题

    返回:
        answer: 答案
    """
    pass
```

---

## 接口设计

### Vision 模块接口

```python
class VisionModule:
    """
    Vision 模块
    统一的视觉处理接口
    """

    def __init__(
        self,
        camera_id: int = 0,
        resolution: Tuple[int, int] = (1280, 720),
        fps: int = 30,
        enable_analysis: bool = True
    ):
        """
        初始化 Vision 模块

        参数:
            camera_id: 摄像头 ID
            resolution: 分辨率
            fps: 帧率
            enable_analysis: 是否启用实时分析
        """
        pass

    async def start(
        self,
        on_frame: Optional[Callable[[np.ndarray], None]] = None
    ) -> None:
        """
        启动摄像头

        参数:
            on_frame: 帧回调函数
        """
        pass

    async def stop(self) -> None:
        """
        停止摄像头
        """
        pass

    async def capture_frame(self) -> Optional[np.ndarray]:
        """
        采集一帧

        返回:
            frame: 帧图像
        """
        pass

    async def analyze_frame(
        self,
        frame: np.ndarray
    ) -> AnalysisResult:
        """
        分析一帧

        参数:
            frame: 帧图像

        返回:
            AnalysisResult {
                faces: List[Face],
                emotions: List[Emotion],
                gestures: List[Gesture],
                objects: List[str],
            }
        """
        pass

    async def understand_scene(
        self,
        image: np.ndarray
    ) -> SceneUnderstanding:
        """
        理解场景
        """
        pass

    async def describe_image(
        self,
        image: np.ndarray
    ) -> str:
        """
        描述图像
        """
        pass

    async def visual_qa(
        self,
        image: np.ndarray,
        question: str
    ) -> str:
        """
        视觉问答
        """
        pass
```

---

## 图像处理

### 图像预处理

**预处理步骤**：
1. **颜色校正**：白平衡、曝光补偿
2. **降噪处理**：高斯滤波、双边滤波
3. **增强处理**：对比度增强、锐化
4. **归一化**：缩放到统一尺寸

```python
def preprocess_image(
    image: np.ndarray,
    target_size: Optional[Tuple[int, int]] = None
) -> np.ndarray:
    """
    预处理图像

    参数:
        image: 输入图像
        target_size: 目标尺寸（可选）

    返回:
        processed_image: 预处理后的图像
    """
    pass
```

### 人脸检测与识别

**检测算法**：
- Haar Cascade（快速，精度一般）
- MTCNN（中速，精度高）
- RetinaFace（慢，精度最高）

**识别算法**：
- FaceNet（基于深度学习）
- ArcFace（基于 Arc Loss）

### 表情识别

**支持的表情类型**：
- `happy`: 开心
- `sad`: 悲伤
- `angry`: 愤怒
- `surprise`: 惊讶
- `fear`: 恐惧
- `neutral`: 中性

### 手势识别

**支持的手势类型**：
- `open_palm`: 张开手掌
- `fist`: 握拳
- `thumbs_up`: 竖大拇指
- `thumbs_down`: 倒大拇指
- `peace`: 比心

---

## 视频流处理

### 帧提取与缓冲

**帧缓冲策略**：
- 环形缓冲区（避免内存泄漏）
- 缓冲区大小：30 帧（约 1 秒）
- 双缓冲机制（读写分离）

### 视频流处理流程

```
视频流输入
    │
    ▼
┌──────────────────┐
│ 帧提取           │
│ - 解码视频流     │
│ - 提取帧         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 帧缓冲           │
│ - 环形缓冲区     │
│ - 双缓冲         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 帧处理           │
│ - 预处理         │
│ - 视觉分析       │
└────────┬─────────┘
         │
         ▼
    输出结果
```

---

## 摄像头交互

### 摄像头配置

**支持的摄像头类型**：
- USB 摄像头
- 内置摄像头
- 网络摄像头（IP Camera）

**配置参数**：
```python
camera_config = {
    "camera_id": 0,            # 摄像头 ID
    "resolution": (1280, 720), # 分辨率
    "fps": 30,                 # 帧率
    "exposure": -1,             # 曝光（-1 为自动）
    "white_balance": -1,         # 白平衡（-1 为自动）
    "gain": 0,                  # 增益
}
```

### 实时视觉反馈

**视觉反馈类型**：
1. **人脸框绘制**：在图像上绘制检测到的人脸
2. **表情标注**：在人脸框上标注表情
3. **手势标注**：在图像上标注识别到的手势
4. **文字叠加**：在图像上叠加文字信息

---

## 错误处理

### 错误分类

| 错误类型 | 处理策略 | 重试 |
|---------|---------|------|
| 摄像头未连接 | 提示用户检查设备 | 否 |
| 图像格式错误 | 尝试格式转换 | 是 |
| 检测失败 | 跳过当前帧 | 否 |
| 理解失败 | 返回默认描述 | 是 |

---

## 性能优化

### 并行处理

**多线程处理**：
- 视频采集线程
- 视觉分析线程
- 结果处理线程

### GPU 加速

**CUDA 加速**：
- OpenCV CUDA 模块
- MediaPipe GPU 加速
- CLIP GPU 推理

### 缓存策略

**帧缓存**：
- 缓存最近处理的帧
- 避免重复处理

**模型缓存**：
- 缓存加载的模型
- 避免重复加载

---

## 最佳实践

### 1. 摄像头配置

**提升视频质量**：
- 使用高分辨率（>= 1280x720）
- 使用高帧率（>= 30 FPS）
- 调整曝光和白平衡

**优化性能**：
- 根据实际需求调整分辨率和帧率
- 使用 GPU 加速

### 2. 视觉分析

**提升识别准确率**：
- 使用高质量的摄像头
- 保证光线充足
- 减少背景干扰

**优化性能**：
- 选择合适的算法（速度 vs 精度）
- 启用 GPU 加速
- 使用并行处理

### 3. 隐私保护

**保护用户隐私**：
- 本地处理，不上传图像
- 提供隐私模式选项
- 及时释放图像数据

---

## 总结

Vision 模块是 Nakari 的视觉感知系统，通过 OpenCV / MediaPipe / CLIP 等技术实现了：

1. **实时视觉感知**：实时处理摄像头画面，延迟控制在 100ms 以内
2. **多场景识别**：支持人脸识别、表情识别、手势识别、物体检测等
3. **低延迟**：实时视频流处理，保证交互流畅性
4. **高精度**：准确识别和理解视觉信息
5. **隐私保护**：本地处理，不上传敏感图像数据

该模块为 Nakari 提供了完整的视觉感知能力，让 Nakari 能够通过摄像头看到用户，实现真正的双向视觉交互。
