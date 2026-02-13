# Nakari Web 前端

## 功能特性

### 🎨 2D 桌宠形象
- 纯 CSS 实现的 2D 角色
- 浮动动画效果
- 自动眨眼动画
- 鼠标跟随效果（眼睛跟随鼠标）

### 😊 表情系统
四种表情状态：
- **Happy** - 开心（默认回复时）
- **Sad** - 悲伤
- **Surprised** - 惊讶
- **Thinking** - 思考中

### 💬 聊天功能
- 文字输入对话
- 消息历史显示
- 自动滚动到最新消息
- 清除对话按钮

### 🎤 语音交互
- 按住说话（Push-to-Talk）
- 语音转文字（STT）
- 文字转语音（TTS）播放
- 唇形同步动画

### ⚡ 实时通信
- WebSocket 双向通信
- 自动重连机制
- 心跳保持连接

## 启动方式

### 方式一：完整启动（推荐）
双击 `start_nakari.bat`，会自动启动：
1. Redis 容器
2. Celery Worker
3. API Server
4. 前端页面

### 方式二：仅启动 Web 界面
如果 Redis 和 Celery Worker 已在运行，双击 `start_web.bat` 启动：
1. API Server
2. 前端页面

### 方式三：手动启动

**终端 1 - Celery Worker**
```cmd
D:\anaconda\envs\nakari\python.exe -m celery -A tasks.app worker --loglevel=info --pool=solo
```

**终端 2 - API Server**
```cmd
D:\anaconda\envs\nakari\python.exe api_server.py
```

**浏览器 - 前端页面**
打开 `frontend/index.html`

## API 接口

### HTTP API
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | API 根路径 |
| POST | `/api/chat` | 发送聊天消息 |
| GET | `/api/status` | 获取系统状态 |
| GET | `/api/history/{session_id}` | 获取对话历史 |
| DELETE | `/api/history/{session_id}` | 清除对话历史 |
| POST | `/api/voice/stt` | 语音转文字 |
| POST | `/api/voice/tts` | 文字转语音 |

### WebSocket
```
ws://localhost:8000/ws/{session_id}
```

**消息格式：**
```json
{
  "type": "chat",       // chat, audio, emotion, ping
  "message": "你好",
  "audio": "base64...",
  "emotion": "happy"
}
```

## 技术栈

- **后端**: FastAPI + WebSocket
- **前端**: 纯 HTML/CSS/JavaScript
- **动画**: CSS Animations
- **通信**: WebSocket

## 文件结构

```
nakari/
├── api_server.py          # FastAPI 服务器
├── frontend/
│   ├── index.html        # 前端页面
│   └── WEB_README.md    # 本文档
├── start_nakari.bat      # 完整启动脚本
└── start_web.bat         # Web 启动脚本
```

## 浏览器要求

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

需要支持：
- WebSocket
- MediaRecorder API（语音功能）
- ES6+ JavaScript

## 自定义

### 修改颜色主题
编辑 `frontend/index.html` 中的 CSS 变量：
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### 替换 2D 形象
将 `.nakari-character` 部分替换为你的图片或 Live2D 模型

### 添加新表情
1. 添加 CSS 类 `.expression-xxx`
2. 在 `setExpression()` 函数中添加映射

## 故障排查

### WebSocket 连接失败
- 确认 API Server 已启动（检查 http://localhost:8000）
- 检查防火墙设置

### 语音功能无法使用
- 确认浏览器有麦克风权限
- 检查 `tasks/audio` 模块是否正常工作

### Celery 任务无响应
- 检查 Redis 是否运行：`docker ps`
- 查看 Celery Worker 日志窗口
