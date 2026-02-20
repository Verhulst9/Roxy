/**
 * Main App component - Live2D frontend for nakari
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Live2DRenderer, setModelEmotion, setModelParams } from './live2d/Live2DRenderer';
import { useWebSocket } from './hooks/useWebSocket';
import { AudioProcessor } from './utils/AudioProcessor';
import { config } from './config';
import type { Live2DState, Emotion, Live2DParam, WSMessage } from './types';

function App() {
  const [connectionState, setConnectionState] = useState<string>('disconnected');
  const [currentState, setCurrentState] = useState<Live2DState>('idle');
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean }>>([]);
  const [showConnectionStatus] = useState(true);

  const modelRef = useRef<any>(null);
  const audioProcessorRef = useRef<AudioProcessor | null>(null);
  const isSpeakingRef = useRef(false);

  // Initialize audio processor
  useEffect(() => {
    audioProcessorRef.current = new AudioProcessor((mouthParam) => {
      // Update mouth parameter on Live2D model
      if (modelRef.current) {
        setModelParams(modelRef.current, [{ name: 'ParamMouthOpenY', value: mouthParam }]);
      }
    });

    return () => {
      audioProcessorRef.current?.dispose();
    };
  }, []);

  // WebSocket message handler
  const handleWSMessage = useCallback((message: WSMessage) => {
    switch (message.type) {
      case 'state':
        const stateData = message.data as { state: Live2DState };
        setCurrentState(stateData.state);
        break;

      case 'audio':
        if (audioProcessorRef.current) {
          const audioData = message.data as { audio: string; format: string };
          audioProcessorRef.current.play(audioData.audio);
          isSpeakingRef.current = true;
        }
        break;

      case 'text':
        const textData = message.data as { text: string; isUser: boolean };
        setMessages(prev => [...prev, { text: textData.text, isUser: textData.isUser }]);
        break;

      case 'emotion':
        const emotionData = message.data as { emotion: Emotion; intensity: number };
        if (modelRef.current) {
          setModelEmotion(modelRef.current, emotionData.emotion);
        }
        break;

      case 'motion':
        const motionData = message.data as { group: string; index: number };
        if (modelRef.current) {
          modelRef.current.motion(motionData.group, motionData.index);
        }
        break;

      case 'param':
        const paramData = message.data as { params: Live2DParam[] };
        if (modelRef.current) {
          setModelParams(modelRef.current, paramData.params);
        }
        break;

      default:
        break;
    }
  }, []);

  // WebSocket connection handler
  const handleStateChange = useCallback((state: string) => {
    setConnectionState(state);
  }, []);

  // Initialize WebSocket
  const { sendText, connect } = useWebSocket(
    config.wsUrl,
    {
      autoReconnect: true,
      reconnectInterval: 3000,
      onMessage: handleWSMessage,
      onStateChange: handleStateChange,
    }
  );

  // Auto-connect on mount
  useEffect(() => {
    connect();
  }, [connect]);

  // Handle model loaded
  const handleModelLoaded = useCallback(() => {
    console.log('Live2D model loaded');

    // Make model globally accessible for parameter control
    if ((window as any).live2dModel) {
      modelRef.current = (window as any).live2dModel;
    }
  }, []);

  // Handle model error
  const handleModelError = useCallback((error: Error) => {
    console.error('Live2D model error:', error);
  }, []);

  // Handle user input
  const handleSendMessage = useCallback((text: string) => {
    if (text.trim()) {
      sendText(text, true);
      setMessages(prev => [...prev, { text, isUser: true }]);
    }
  }, [sendText]);

  // Get connection status color
  const getConnectionColor = () => {
    switch (connectionState) {
      case 'connected': return 'text-green-500';
      case 'connecting': case 'reconnecting': return 'text-yellow-500';
      case 'error': case 'disconnected': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="app-container">
      {/* Connection status indicator */}
      {showConnectionStatus && (
        <div className={`connection-status ${getConnectionColor()}`}>
          <span className="status-dot"></span>
          {connectionState}
        </div>
      )}

      {/* Live2D Canvas */}
      <Live2DRenderer
        config={config.modelConfig}
        onModelLoaded={handleModelLoaded}
        onError={handleModelError}
      />

      {/* Message display */}
      <div className="messages-container">
        {messages.slice(-3).map((msg, i) => (
          <div key={i} className={`message ${msg.isUser ? 'user' : 'assistant'}`}>
            {msg.text}
          </div>
        ))}
      </div>

      {/* Input area */}
      <div className="input-container">
        <input
          type="text"
          placeholder="Type a message..."
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSendMessage((e.target as HTMLInputElement).value);
              (e.target as HTMLInputElement).value = '';
            }
          }}
          disabled={connectionState !== 'connected'}
        />
        <button
          onClick={() => {
            const input = document.querySelector('input') as HTMLInputElement;
            handleSendMessage(input.value);
            input.value = '';
          }}
          disabled={connectionState !== 'connected'}
        >
          Send
        </button>
      </div>

      {/* State indicator */}
      <div className="state-indicator">
        State: {currentState}
      </div>
    </div>
  );
}

export default App;
