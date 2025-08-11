# PodSearch

A web application for searching YouTube podcasts and chatting with their transcripts using AI.

## What it does

PodSearch allows users to:
- Search for YouTube podcast episodes by topic or keyword
- Import videos to analyze their transcripts
- Chat with AI about the podcast content and get timestamped answers
- Save insights for later reference

## Tech Stack

- **Frontend**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Video Player**: React Player
- **Icons**: Lucide React

## Prerequisites

- Node.js 18+
- npm or yarn
- PodSearch backend running on `localhost:8000`

## Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Environment configuration**
   Create `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   Visit `http://localhost:3000`

## Project Structure

```
src/
├── app/                     # Next.js App Router pages
│   ├── page.tsx            # Home page
│   ├── search/             # Search results
│   ├── workspace/[videoId]/ # Video workspace
│   └── saved/              # Saved insights
├── components/
│   ├── Layout.tsx          # Main layout
│   └── ui/                 # UI components
├── lib/
│   └── api.ts              # API client
├── store/
│   └── useStore.ts         # State management
└── types/
    └── api.ts              # TypeScript types
```

## API Endpoints

The frontend connects to these backend endpoints:

- `GET /api/youtube/search` - Search YouTube videos
- `GET /api/transcripts/transcript-supadata/{id}` - Get video transcript
- `POST /api/rag/process/{id}` - Process transcript for AI chat
- `POST /api/rag/generate/{id}` - Generate AI responses

## Development

### Build for production
```bash
npm run build
npm start
```

### Code structure
- Pages use the Next.js App Router pattern
- Components are organized by feature and reusability
- State management is centralized with Zustand
- API calls are abstracted in the lib/api module

## Features

### Search
- Search YouTube podcasts by keywords
- Filter by duration and sort by various criteria
- Preview video thumbnails and metadata

### Workspace
- Embedded YouTube video player
- AI chat interface for asking questions about content
- Transcript view with clickable timestamps
- Automatic transcript processing

### Saved Insights
- Save interesting Q&A pairs from chats
- Search and organize saved content
- View statistics about saved insights

## License

This project is part of the PodSearch platform.