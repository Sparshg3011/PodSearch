# 🎧 PodSearch AI - Frontend

A beautiful, modern NextJS frontend for the PodSearch AI platform that enables users to search YouTube podcasts using natural language, get timestamped answers from transcripts, and verify facts with trusted sources.

## ✨ Features

### 🏠 Landing Page
- **Beautiful Hero Section** with gradient backgrounds and animations
- **Smart Search Box** with placeholder suggestions
- **Popular Searches** as clickable chips
- **Feature Showcase** with icons and descriptions
- **How It Works** step-by-step guide
- **Responsive Design** for all devices

### 🔍 Search Results
- **YouTube Video Cards** with thumbnails, metadata, and descriptions
- **Advanced Filtering** by duration, upload date, view count
- **Sorting Options** for relevance, recency, popularity
- **Import to Workspace** functionality
- **Direct YouTube Links** for immediate viewing

### 🎯 Workspace
- **Embedded YouTube Player** with full controls
- **Three-Tab Interface**: Chat, Transcript, Facts
- **Real-time RAG Chat** with AI-powered answers
- **Clickable Transcript** with timestamp navigation
- **Automatic Fact-Checking** with confidence scores
- **Source Citations** with relevance ratings
- **Fact Detail Modals** with external source links

### 💾 Saved Insights
- **Personal Knowledge Collection** with search and filtering
- **Fact-Check Status** indicators and breakdowns
- **Source Preservation** with timestamp links
- **Export and Sharing** capabilities
- **Statistics Dashboard** for usage insights

### 🎨 UI/UX Excellence
- **Modern Component Library** with consistent design
- **Beautiful Animations** using Framer Motion
- **Responsive Layout** for mobile, tablet, desktop
- **Dark/Light Mode** theme switching
- **Toast Notifications** for user feedback
- **Loading States** and error handling
- **Accessibility Features** throughout

## 🛠️ Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand with persistent storage
- **UI Components**: Custom component library with CVA
- **Animations**: Framer Motion for smooth interactions
- **Video Player**: React Player for YouTube integration
- **Icons**: Lucide React for consistent iconography
- **HTTP Client**: Axios with interceptors
- **Notifications**: React Hot Toast
- **Date Handling**: date-fns for formatting

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running PodSearch backend on `localhost:8000`

### Installation

1. **Clone and Navigate**
   ```bash
   cd podsearch-frontend
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Environment Setup**
   Create `.env.local` (already created):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_APP_NAME=PodSearch AI
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   ```

4. **Start Development Server**
   ```bash
   npm run dev
   ```

5. **Open in Browser**
   Visit [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
src/
├── app/                          # Next.js App Router
│   ├── globals.css              # Global styles and Tailwind
│   ├── layout.tsx               # Root layout with metadata
│   ├── page.tsx                 # Landing page
│   ├── search/                  # Search results page
│   ├── workspace/[videoId]/     # Dynamic workspace pages
│   └── saved/                   # Saved insights page
├── components/
│   ├── Layout.tsx               # Main app layout
│   └── ui/                      # Reusable UI components
│       ├── Button.tsx           # Button variants
│       ├── Input.tsx            # Input with icons
│       ├── Card.tsx             # Card components
│       ├── Badge.tsx            # Status badges
│       └── LoadingSpinner.tsx   # Loading states
├── lib/
│   └── api.ts                   # API client and utilities
├── store/
│   └── useStore.ts              # Zustand state management
├── types/
│   └── api.ts                   # TypeScript type definitions
└── hooks/                       # Custom React hooks (future)
```

## 🔌 API Integration

The frontend seamlessly integrates with your backend APIs:

### YouTube API
- `GET /api/youtube/search` - Search videos
- `GET /api/youtube/video/{id}` - Get video details

### Transcript API  
- `GET /api/transcripts/transcript-supadata/{id}` - Get transcript
- `GET /api/transcripts/search/{id}` - Get from database

### RAG API
- `POST /api/rag/process/{id}` - Process for search
- `POST /api/rag/search/{id}` - Search transcript
- `POST /api/rag/generate/{id}` - Generate answers
- `GET /api/rag/list` - List processed videos

### Fact Verification API
- `POST /api/fact-verification/verify` - Verify claims
- `POST /api/fact-verification/batch/{id}` - Batch verify
- `GET /api/fact-verification/stats` - Get statistics

## 🎯 User Flow

1. **Landing**: User arrives and sees beautiful interface
2. **Search**: User searches for topics using natural language
3. **Results**: System displays relevant YouTube podcast episodes
4. **Import**: User imports interesting videos to workspace
5. **Process**: Backend processes transcript for AI search
6. **Chat**: User asks questions about the podcast content
7. **Answers**: AI provides timestamped answers with sources
8. **Fact-Check**: Claims are automatically verified
9. **Save**: User saves insights to personal collection
10. **Review**: User can review and share saved insights

## 🔧 Configuration

### Tailwind Customization
- Custom color palette with primary, success, warning, error
- Animation variants for smooth interactions  
- Component classes for consistent styling
- Responsive breakpoints and utilities

### State Management
- Search state for query results and loading
- Workspace state for current video and chat
- UI state for theme and navigation
- Persistent storage for saved insights

### API Configuration
- Axios interceptors for error handling
- Environment-based URL configuration
- Timeout and retry logic
- Response transformation utilities

## 🎨 Design System

### Colors
- **Primary**: Blue palette for main actions
- **Success**: Green for verified facts
- **Warning**: Yellow for partial verification  
- **Error**: Red for false claims
- **Gray**: Neutral tones for UI elements

### Typography
- **Headlines**: Bold, large text for impact
- **Body**: Readable font sizes and line heights
- **Code**: Monospace for technical content
- **Captions**: Small text for metadata

### Components
- **Buttons**: Multiple variants with loading states
- **Cards**: Elevated surfaces with hover effects
- **Badges**: Status indicators with color coding
- **Inputs**: Focus states and validation styling

## 🚀 Deployment

### Build for Production
```bash
npm run build
npm start
```

### Environment Variables
Ensure all `NEXT_PUBLIC_*` variables are set for production.

### Performance
- Optimized images with Next.js Image component
- Code splitting with dynamic imports
- Lazy loading for heavy components
- Efficient state management and re-renders

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is part of the PodSearch AI platform.

---

**Built with ❤️ using Next.js, TypeScript, and modern web technologies** 