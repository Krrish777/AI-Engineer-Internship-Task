# Personality-Driven AI Assistant

An AI assistant that adapts its communication style based on user emotional state. Built with AgentOS, Gemini, and Next.js.

## Features

- 🎭 **Adaptive Personalities**: Three distinct personalities (Calm Mentor, Witty Friend, Therapist)
- 🧠 **Memory System**: Remembers user preferences, facts, and emotional patterns across sessions
- 🔄 **Auto-Detection**: Automatically switches personality based on emotional cues in messages
- 💬 **Modern Chat UI**: Clean interface with real-time streaming support

## Project Structure

```
├── backend/           # Python backend (AgentOS + Gemini)
│   ├── src/
│   │   ├── personality/  # Personality engine & profiles
│   │   ├── memory/       # Memory extraction & storage
│   │   ├── pipeline/     # Response transformation
│   │   └── core/         # Config & logging
│   ├── main.py          # AgentOS entry point
│   └── pyproject.toml   # Python dependencies
├── frontend/          # Next.js frontend
│   └── src/
│       ├── app/         # Pages
│       ├── components/  # UI components
│       └── hooks/       # Custom hooks
├── .github/           # GitHub config
└── logs/              # Application logs
```

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Google Gemini API key

### Backend Setup

```bash
cd backend

# Create .env file with your API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env

# Install dependencies and run
uv sync
uv run python main.py
```

Backend runs at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at `http://localhost:3000`

## Personalities

| Personality | Style | Use Case |
|-------------|-------|----------|
| **Calm Mentor** | Grounded, wise, supportive | Default, guidance, learning |
| **Witty Friend** | Playful, clever, energetic | Casual chat, celebrations |
| **Therapist** | Warm, validating, reflective | Emotional support, frustration |

The AI automatically detects emotional cues and switches personalities:
- Joy/excitement → Witty Friend
- Frustration/sadness → Therapist
- Neutral/questions → Calm Mentor

## Tech Stack

**Backend:**
- [AgentOS](https://agno.com) - AI agent framework
- [Gemini 2.0 Flash](https://ai.google.dev) - Language model
- FastAPI - Web framework
- SQLite - Session & memory persistence

**Frontend:**
- Next.js 15 - React framework
- Tailwind CSS - Styling
- Zustand - State management
- Radix UI - Accessible components

## Author

**Krish Sharma**
- [GitHub](https://github.com/Krrish777)
- [LinkedIn](https://www.linkedin.com/in/krish-sharma-3375b927b/)

## License

MIT
