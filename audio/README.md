# Audio - 语音处理模块

## 📋 目录
- [模块概述](#模块概述)
- [设计理念](#设计理念)
- [架构设计](#架构设计)
- [核心组件](#核心组件)
- [接口设计](#接口设计)
- [STT 语音转文字](#stt-语音转文字)
- [TTS 文字转语音](#tts-文字转语音)
- [音色训练](#音色训练)
- [错误处理](#错误处理)
- [性能优化](#性能优化)
- [最佳实践](#最佳实践)

---

## 模块概述

### 职责定位
Audio 模块是 Nakari 的**语音交互系统**，负责语音识别（STT）和语音合成（TTS）。该模块让 Nakari 能够通过语音与用户进行自然交互，同时支持个性化音色的训练和应用。

### 设计目标
1. **高精度识别**：支持多语言、多口音的语音识别
2. **自然语音合成**：生成自然流畅的语音，支持情感表达
3. **个性化音色**：支持自定义音色训练，让 Nakari 拥有独特的声音
4. **低延迟**：实时语音交互，延迟控制在 1 秒以内
5. **跨语言支持**：支持多语言语音识别和合成

### 技术选型

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| OpenAI Whisper | 1.0+ | 高精度语音识别，支持多语言 |
| ElevenLabs | API | 高质量 TTS，支持音色克隆 |
| Azure Speech Service | 1.0+ | 企业级语音服务，稳定性高 |
| FFmpeg | 5.0+ | 音频格式转换和处理 |

---

## 设计理念

### 语音交互流程

```
┌─────────────────────────────────────────────────────────────┐
│                    语音交互流程                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
    ┌─────────┐                   ┌─────────┐
    │  STT    │                   │  TTS    │
    │ 语音→文字 │                   │ 文字→语音 │
    └────┬────┘                   └────┬────┘
         │                             │
         ▼                             ▼
    用户语音输入                  Nakari 语音输出
    (麦克风)                     (扬声器)
```

### 个性化音色设计

**音色训练流程**：
```
音频样本采集
    │
    ▼
音色特征提取
    │
    ▼
模型训练/微调
    │
    ▼
音色模型部署
    │
    ▼
个性化语音合成
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
│                      Audio Module                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ STT Engine   │  │ TTS Engine   │  │ Voice Trainer│     │
│  │ 语音识别引擎   │  │ 语音合成引擎   │  │ 音色训练引擎  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                   │
│                           ▼                                   │
│                  Audio Processor                             │
│           ┌─────────────────────────────┐                   │
│           │ - Audio Format Conversion   │                   │
│           │ - Noise Reduction          │                   │
│           │ - Audio Segmentation        │                   │
│           │ - Voice Activity Detection  │                   │
│           └─────────────────────────────┘                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                          │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│  │ Whisper │         │ElevenLabs│        │Azure    │       │
│  │ API     │         │ API      │        │Speech   │       │
│  └─────────┘         └─────────┘         └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. STT Engine（语音识别引擎）

**职责**：
- 将用户语音转换为文本
- 支持实时流式识别
- 处理多语言和多口音

**接口设计**：
```python
async def transcribe_audio(
    audio_data: bytes,
    language: str = "zh",
    model: str = "whisper-large-v3"
) -> TranscriptionResult:
    """
    语音识别

    参数:
        audio_data: 音频数据（PCM/WAV）
        language: 语言代码（zh/en/ja）
        model: 识别模型

    返回:
        TranscriptionResult {
            text: str,              # 识别的文本
            confidence: float,       # 置信度
            segments: List[Segment], # 分段结果
            language: str,          # 检测到的语言
        }
    """
    pass
```

### 2. TTS Engine（语音合成引擎）

**职责**：
- 将文本转换为语音
- 支持个性化音色
- 支持情感表达

**接口设计**：
```python
async def synthesize_speech(
    text: str,
    voice_id: str = "default",
    emotion: Optional[str] = None,
    speed: float = 1.0
) -> AudioResult:
    """
    语音合成

    参数:
        text: 要合成的文本
        voice_id: 音色 ID
        emotion: 情感（neutral/happy/sad/angry）
        speed: 语速（0.5-2.0）

    返回:
        AudioResult {
            audio_data: bytes,    # 音频数据
            format: str,          # 音频格式（mp3/wav）
            duration: float,      # 时长（秒）
        }
    """
    pass
```

### 3. Voice Trainer（音色训练引擎）

**职责**：
- 训练个性化音色模型
- 音色特征提取
- 模型微调

**接口设计**：
```python
async def train_voice(
    audio_samples: List[bytes],
    voice_name: str,
    base_model: str = "eleven_multilingual_v2"
) -> TrainingResult:
    """
    训练音色

    参数:
        audio_samples: 音频样本列表（需要 >= 10 分钟音频）
        voice_name: 音色名称
        base_model: 基础模型

    返回:
        TrainingResult {
            voice_id: str,        # 训练后的音色 ID
            status: str,           # 状态（training/completed/failed）
            progress: float,       # 进度（0-1）
            error: Optional[str], # 错误信息
        }
    """
    pass
```

---

## 接口设计

### Audio 模块接口

```python
class AudioModule:
    """
    Audio 模块
    统一的语音处理接口
    """

    def __init__(
        self,
        stt_model: str = "whisper-large-v3",
        tts_voice_id: str = "default",
        enable_streaming: bool = True
    ):
        """
        初始化 Audio 模块

        参数:
            stt_model: STT 模型
            tts_voice_id: 默认 TTS 音色
            enable_streaming: 是否启用流式识别
        """
        pass

    async def listen(
        self,
        duration: Optional[float] = None,
        on_result: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        监听用户语音

        参数:
            duration: 监听时长（秒，None 表示直到检测到静音）
            on_result: 结果回调函数（流式识别）

        返回:
            text: 识别的文本
        """
        pass

    async def speak(
        self,
        text: str,
        voice_id: Optional[str] = None,
        emotion: Optional[str] = None
    ) -> None:
        """
        语音输出

        参数:
            text: 要说的文本
            voice_id: 音色 ID（可选，使用默认音色）
            emotion: 情感（可选）
        """
        pass

    async def transcribe_file(
        self,
        file_path: str
    ) -> TranscriptionResult:
        """
        转录音频文件

        参数:
            file_path: 音频文件路径

        返回:
            TranscriptionResult: 转录结果
        """
        pass

    async def train_custom_voice(
        self,
        audio_samples: List[str],
        voice_name: str
    ) -> TrainingResult:
        """
        训练自定义音色

        参数:
            audio_samples: 音频样本文件路径列表
            voice_name: 音色名称

        返回:
            TrainingResult: 训练结果
        """
        pass

    def get_available_voices(self) -> List[VoiceInfo]:
        """
        获取可用音色列表

        返回:
            List[VoiceInfo]: 音色信息列表
        """
        pass
```

---

## STT 语音转文字

### 技术选型

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| OpenAI Whisper | 高精度、多语言、开源 | 需要 GPU | 通用场景 |
| Google STT | 高精度、稳定性好 | 成本高 | 生产环境 |
| Azure STT | 企业级、稳定性好 | 成本高 | 企业应用 |

### Whisper 模型选择

| 模型 | 参数量 | 速度 | 精度 | 适用场景 |
|------|-------|------|------|---------|
| tiny | 39M | 最快 | 低 | 实时对话 |
| base | 74M | 快 | 中 | 实时对话 |
| small | 244M | 中 | 中高 | 一般场景 |
| medium | 769M | 慢 | 高 | 高精度场景 |
| large-v3 | 1550M | 最慢 | 最高 | 离线转录 |

### 实时流式识别

**VAD（Voice Activity Detection）**：
- 检测语音活动，自动开始/停止录音
- 避免长段静音的浪费

**流式识别流程**：
```
音频流输入
    │
    ▼
┌──────────────────┐
│ VAD 检测         │
│ - 检测语音开始   │
│ - 检测语音结束   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 分段识别         │
│ - 每 500ms 识别  │
│ - 返回部分结果   │
└────────┬─────────┘
         │
         ▼
    累积结果
```

---

## TTS 文字转语音

### 技术选型

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| ElevenLabs | 高质量、支持音色克隆 | 成本高 | 个性化场景 |
| Azure TTS | 稳定、多语言 | 音色相对固定 | 企业应用 |
| Google TTS | 成本低、稳定性好 | 音色一般 | 通用场景 |

### 语音合成流程

```
文本输入
    │
    ▼
┌──────────────────┐
│ 文本预处理       │
│ - 标点处理       │
│ - 数字转文字     │
│ - 缩写扩展       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 语音合成         │
│ - 生成音频       │
│ - 应用音色       │
│ - 添加情感       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 后处理           │
│ - 音量标准化     │
│ - 降噪处理       │
│ - 格式转换       │
└────────┬─────────┘
         │
         ▼
    音频输出
```

### 情感表达

**支持的情感类型**：
- `neutral`: 中性
- `happy`: 开心
- `sad`: 悲伤
- `angry`: 愤怒
- `excited`: 兴奋
- `calm`: 平静

**情感调整参数**：
```python
emotion_params = {
    "pitch": 1.0,        # 音调（0.5-2.0）
    "speed": 1.0,        # 语速（0.5-2.0）
    "volume": 1.0,       # 音量（0.5-1.5）
}
```

---

## 音色训练

### 音色训练流程

**1. 音频样本采集**：
- 需要 >= 10 分钟的高质量音频
- 音频需要清晰、无背景噪音
- 音频内容需要包含多种语音（不同语调、情感）

**2. 音色特征提取**：
- 提取声学特征（MFCC、Mel-spectrogram）
- 提取韵律特征（语调、节奏、语速）

**3. 模型训练/微调**：
- 使用预训练模型（如 ElevenLabs base model）
- 基于音频样本进行微调
- 训练时间：约 30-60 分钟

**4. 音色模型部署**：
- 生成音色 ID
- 集成到 TTS 引擎

### 音色质量评估

**评估指标**：
- 相似度（与原始音频的相似度）
- 自然度（语音的自然程度）
- 情感表达能力

**优化方向**：
- 增加训练样本数量
- 提高音频质量
- 调整训练参数

---

## 错误处理

### 错误分类

| 错误类型 | 处理策略 | 重试 |
|---------|---------|------|
| 音频格式错误 | 尝试格式转换 | 是 |
| 网络错误 | 延迟重试 | 是 |
| 识别失败 | 提示用户重说 | 否 |
| 合成失败 | 使用备用音色 | 是 |
| 训练失败 | 检查音频质量 | 否 |

---

## 性能优化

### 音频预处理

**降噪处理**：
- 使用 AI 降噪算法
- 提高识别准确率

**音频分段**：
- 基于 VAD 进行智能分段
- 避免长段音频处理

### 缓存策略

**语音缓存**：
```python
speech_cache = {
    "text_hash": "audio_data"
}
```

**TTS 缓存**：
- 缓存常用短语的语音
- 减少重复合成

---

## 最佳实践

### 1. STT 优化

**提升识别准确率**：
- 使用高质量的麦克风
- 减少背景噪音
- 清晰地说出每个词

**实时性优化**：
- 使用较小的模型（tiny/base）
- 启用 VAD 避免长时间录音

### 2. TTS 优化

**提升语音质量**：
- 选择合适的音色
- 调整语速和音调
- 添加适当的情感

**个性化优化**：
- 训练高质量的音色
- 提供足够的音频样本

### 3. 音色训练

**训练建议**：
- 提供清晰、无噪音的音频
- 音频内容需要多样化
- 训练时长 >= 10 分钟

---

## 总结

Audio 模块是 Nakari 的语音交互系统，通过 Whisper / ElevenLabs 等技术实现了：

1. **高精度识别**：支持多语言、多口音的语音识别
2. **自然语音合成**：生成自然流畅的语音，支持情感表达
3. **个性化音色**：支持自定义音色训练，让 Nakari 拥有独特的声音
4. **低延迟**：实时语音交互，延迟控制在 1 秒以内
5. **跨语言支持**：支持多语言语音识别和合成

该模块为 Nakari 提供了完整的语音交互能力，让用户能够通过语音与 Nakari 进行自然、流畅的交互。
