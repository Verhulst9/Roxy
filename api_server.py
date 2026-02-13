"""
Nakari Web API Server
提供 HTTP API 和 WebSocket 接口供前端调用
"""
import asyncio
import json
import uuid
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from tasks.interaction import process_user_input
from tasks.audio import transcribe_audio, synthesize_speech
from context.manager import context_manager


# FastAPI 应用
app = FastAPI(title="Nakari API", version="1.0.0")

# CORS 配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === 数据模型 ===

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    is_thinking: bool = False
    emotion: Optional[str] = None


class VoiceRequest(BaseModel):
    session_id: str


class StatusResponse(BaseModel):
    status: str
    is_reflecting: bool
    active_sessions: int
    last_activity: Optional[str] = None


# === WebSocket 连接管理 ===

class ConnectionManager:
    """管理 WebSocket 连接"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def broadcast(self, message: dict):
        """向所有连接广播消息"""
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


# === HTTP API 路由 ===

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "Nakari API Server",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "websocket": "/ws/{session_id}",
            "status": "/api/status",
            "voice": "/api/voice/tts"
        }
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    处理聊天请求
    """
    session_id = request.session_id or f"web_{uuid.uuid4().hex[:8]}"

    try:
        # 调用 Celery 任务处理用户输入
        response_text = process_user_input(request.message, session_id)

        # 获取历史中的情感信息（如果有的话）
        history = context_manager.get_context(session_id)
        emotion = None
        if history:
            last_msg = history[-1] if history else {}
            emotion = last_msg.get("emotion")

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            emotion=emotion
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """
    获取系统状态
    """
    return StatusResponse(
        status="online",
        is_reflecting=False,  # TODO: 从 Redis 获取实际状态
        active_sessions=len(manager.active_connections),
        last_activity=datetime.now().isoformat()
    )


@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """
    获取会话历史
    """
    history = context_manager.get_context(session_id)
    return {"session_id": session_id, "history": history}


@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str):
    """
    清空会话历史
    """
    context_manager.clear_context(session_id)
    return {"message": "History cleared", "session_id": session_id}


@app.post("/api/voice/stt")
async def speech_to_text(file):
    """
    语音转文字 (STT)
    """
    # 保存上传的音频文件
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = transcribe_audio(tmp_path)
        return {"text": text}
    finally:
        os.unlink(tmp_path)


@app.post("/api/voice/tts")
async def text_to_speech(request: VoiceRequest):
    """
    文字转语音 (TTS) - 返回音频流
    """
    # 获取最后一条助手回复
    history = context_manager.get_context(request.session_id)
    if not history:
        raise HTTPException(status_code=404, detail="No history found")

    # 找到最后一条 AI 消息
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            text = msg.get("content", "")
            break
    else:
        raise HTTPException(status_code=404, detail="No AI response found")

    # 调用 TTS
    tts_result = synthesize_speech(text, return_bytes=True)

    if isinstance(tts_result, dict) and "data" in tts_result:
        import base64
        audio_bytes = base64.b64decode(tts_result["data"])

        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="nakari_speech.mp3"'
            }
        )
    else:
        raise HTTPException(status_code=500, detail="TTS generation failed")


# === WebSocket 路由 ===

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket 端点 - 实时双向通信
    """
    await manager.connect(session_id, websocket)

    # 发送连接确认
    await manager.send_message(session_id, {
        "type": "connected",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "chat":
                # 处理聊天消息
                user_message = data.get("message", "")

                # 发送"正在思考"状态
                await manager.send_message(session_id, {
                    "type": "status",
                    "status": "thinking",
                    "message": "Nakari 正在思考..."
                })

                # 处理消息（异步）
                response_text = process_user_input(user_message, session_id)

                # 发送回复
                await manager.send_message(session_id, {
                    "type": "chat",
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": datetime.now().isoformat()
                })

            elif message_type == "audio":
                # 处理语音消息
                import tempfile
                import base64

                audio_data = data.get("audio", "")
                if audio_data:
                    # 解码 Base64 音频
                    audio_bytes = base64.b64decode(audio_data)

                    # 保存临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        tmp.write(audio_bytes)
                        tmp_path = tmp.name

                    try:
                        # STT
                        transcribed = transcribe_audio(tmp_path)

                        # 发送转录结果
                        await manager.send_message(session_id, {
                            "type": "transcription",
                            "text": transcribed
                        })

                        # 处理文本
                        response_text = process_user_input(transcribed, session_id)

                        # 发送回复
                        await manager.send_message(session_id, {
                            "type": "chat",
                            "role": "assistant",
                            "content": response_text,
                            "timestamp": datetime.now().isoformat()
                        })

                        # 如果需要 TTS，生成音频
                        tts_result = synthesize_speech(response_text, return_bytes=True)
                        if isinstance(tts_result, dict) and "data" in tts_result:
                            await manager.send_message(session_id, {
                                "type": "audio",
                                "audio": tts_result["data"],
                                "format": "mp3"
                            })

                    finally:
                        import os
                        os.unlink(tmp_path)

            elif message_type == "emotion":
                # 接收前端发送的情感状态（如果需要）
                emotion = data.get("emotion")
                print(f"Client emotion update: {emotion}")

            elif message_type == "ping":
                # 心跳检测
                await manager.send_message(session_id, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)


if __name__ == "__main__":
    import uvicorn

    print("[API] Starting Nakari API Server...")
    print("[API] HTTP API: http://localhost:8000")
    print("[API] WebSocket: ws://localhost:8000/ws/{session_id}")
    print("[API] API Docs: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
