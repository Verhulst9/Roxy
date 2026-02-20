# Live2D Frontend for nakari

Real-time Live2D anime avatar frontend for the nakari AI agent.

## Features

- **Live2D Model Rendering** - Using PixiJS and pixi-live2d-display
- **Real-time WebSocket Communication** - Connects to nakari backend API
- **Audio Playback & Lip-sync** - Synchronized mouth movement with TTS audio
- **Emotion Display** - Maps backend emotion analysis to Live2D parameters
- **Motion Control** - Trigger Live2D animations from backend
- **State Tracking** - Visual indicator for nakari's current state

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Configuration

Copy `.env.example` to `.env.local` and configure:

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```
VITE_API_URL=ws://localhost:8000/api/ws
VITE_MODEL_URL=/models/Haru/Haru.model3.json
```

### Live2D Models

Download Live2D Cubism models and place in `public/models/`:

```
public/
  models/
    Haru/
      Haru.model3.json
      Haru.2048/texture_00.png
      Haru.2048/texture_01.png
      ...
```

You can find free Live2D models at:
- [Live2D Cubism](https://www.live2d.com/download/cubism-sdk/)
- [VRoid](https://www.vroid.com/)

### Development

```bash
npm run dev
```

Visit http://localhost:5173

### Build

```bash
npm run build
```

Output: `dist/`

## Project Structure

```
src/
├── components/      # React components
├── hooks/           # Custom React hooks
│   └── useWebSocket.ts  # WebSocket connection hook
├── live2d/          # Live2D integration
│   └── Live2DRenderer.tsx
├── types/           # TypeScript type definitions
│   └── index.ts
├── utils/           # Utility functions
│   └── AudioProcessor.ts  # Audio playback & lip-sync
├── config.ts        # Configuration
├── App.tsx          # Main app component
└── main.tsx         # Entry point
```

## WebSocket Message Types

### Client → Server

| Type | Data | Description |
|------|------|-------------|
| `text` | `{ text: string, isUser: boolean }` | Send text message |

### Server → Client

| Type | Data | Description |
|------|------|-------------|
| `state` | `{ state: Live2DState }` | nakari state change |
| `audio` | `{ audio: string, format: string }` | Base64 audio chunk |
| `text` | `{ text: string, isUser: boolean }` | Text response |
| `emotion` | `{ emotion: Emotion, intensity: number }` | Emotion update |
| `motion` | `{ group: string, index: number }` | Motion trigger |
| `param` | `{ params: Live2DParam[] }` | Parameter update |

## Emotion Mapping

| Emotion | Eye Open | Brow Y | Brow Angle | Mouth |
|---------|----------|--------|------------|-------|
| neutral | 1.0 | 0 | 0 | 0 |
| happy | 1.0 | -0.3 | 0 | 0.5 |
| sad | 0.7 | 0.3 | ±0.2 | -0.3 |
| angry | 0.8 | 0.4 | ∓0.3 | -0.2 |
| surprised | 1.5 | -0.5 | 0 | 0.3 |

## License

MIT
