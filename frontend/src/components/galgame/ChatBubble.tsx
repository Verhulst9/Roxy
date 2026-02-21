/**
 * ChatBubble - Individual chat message bubble
 */

import type { DialogState } from '../../types';

interface ChatBubbleProps {
  message: DialogState;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.isUser;

  return (
    <div className={`chat-bubble ${isUser ? 'user' : 'ai'}`}>
      <span className="chat-bubble-text">{message.text}</span>
    </div>
  );
}
