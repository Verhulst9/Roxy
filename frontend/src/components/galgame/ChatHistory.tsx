/**
 * ChatHistory - Container for chat message bubbles
 */

import type { DialogState } from '../../types';
import { ChatBubble } from './ChatBubble';

interface ChatHistoryProps {
  messages: DialogState[];
  containerRef: React.RefObject<HTMLDivElement | null>;
}

export function ChatHistory({ messages, containerRef }: ChatHistoryProps) {
  if (messages.length === 0) return null;

  return (
    <div ref={containerRef} className="chat-history-container">
      <div className="chat-history-list">
        {messages.map((msg, index) => (
          <div
            key={`${msg.timestamp}-${index}`}
            className={`chat-message-row ${msg.isUser ? 'user' : 'ai'}`}
          >
            <ChatBubble message={msg} />
          </div>
        ))}
      </div>
    </div>
  );
}
