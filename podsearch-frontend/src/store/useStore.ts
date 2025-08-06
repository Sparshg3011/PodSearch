import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  YouTubeVideo,
  TranscriptSegment,
  ChatMessage,
  ClaimVerification,
  RAGSearchResult,
  SearchState,
  WorkspaceState,
} from '@/types/api';

interface AppState {
  // Search State
  search: SearchState;
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: YouTubeVideo[]) => void;
  setSearchLoading: (loading: boolean) => void;
  setSearchError: (error: string | null) => void;
  clearSearch: () => void;

  // Workspace State  
  workspace: WorkspaceState;
  setCurrentVideo: (video: YouTubeVideo | null) => void;
  setTranscript: (transcript: TranscriptSegment[]) => void;
  setIsProcessing: (processing: boolean) => void;
  setIsProcessed: (processed: boolean) => void;
  setRagReady: (ready: boolean) => void;
  addChatMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  updateLastMessage: (updates: Partial<ChatMessage>) => void;
  clearChat: () => void;
  setFactChecking: (checking: boolean) => void;
  setCurrentFactCheck: (factCheck: ClaimVerification[] | null) => void;
  clearWorkspace: () => void;

  // UI State
  ui: {
    theme: 'light' | 'dark';
    sidebarOpen: boolean;
    currentPlayer: {
      isPlaying: boolean;
      currentTime: number;
      duration: number;
    };
  };
  setTheme: (theme: 'light' | 'dark') => void;
  setSidebarOpen: (open: boolean) => void;
  setPlayerState: (state: Partial<AppState['ui']['currentPlayer']>) => void;

  // Saved Content (persisted)
  savedInsights: {
    id: string;
    videoId: string;
    videoTitle: string;
    query: string;
    answer: string;
    sources: RAGSearchResult[];
    factCheck?: ClaimVerification[];
    timestamp: string;
  }[];
  addSavedInsight: (insight: Omit<AppState['savedInsights'][0], 'id' | 'timestamp'>) => void;
  removeSavedInsight: (id: string) => void;
  clearSavedInsights: () => void;
}

const initialSearchState: SearchState = {
  query: '',
  results: [],
  loading: false,
  error: null,
};

const initialWorkspaceState: WorkspaceState = {
  currentVideo: null,
  transcript: [],
  isProcessing: false,
  isProcessed: false,
  ragReady: false,
  chatMessages: [],
  factChecking: false,
  currentFactCheck: null,
};

export const useStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Search State
        search: initialSearchState,
        setSearchQuery: (query) =>
          set((state) => ({ search: { ...state.search, query } })),
        setSearchResults: (results) =>
          set((state) => ({ search: { ...state.search, results } })),
        setSearchLoading: (loading) =>
          set((state) => ({ search: { ...state.search, loading } })),
        setSearchError: (error) =>
          set((state) => ({ search: { ...state.search, error } })),
        clearSearch: () => set({ search: initialSearchState }),

        // Workspace State
        workspace: initialWorkspaceState,
        setCurrentVideo: (currentVideo) =>
          set((state) => ({ workspace: { ...state.workspace, currentVideo } })),
        setTranscript: (transcript) =>
          set((state) => ({ workspace: { ...state.workspace, transcript } })),
        setIsProcessing: (isProcessing) =>
          set((state) => ({ workspace: { ...state.workspace, isProcessing } })),
        setIsProcessed: (isProcessed) =>
          set((state) => ({ workspace: { ...state.workspace, isProcessed } })),
        setRagReady: (ragReady) =>
          set((state) => ({ workspace: { ...state.workspace, ragReady } })),
        addChatMessage: (message) => {
          const newMessage: ChatMessage = {
            ...message,
            id: Date.now().toString(),
            timestamp: new Date(),
          };
          set((state) => ({
            workspace: {
              ...state.workspace,
              chatMessages: [...state.workspace.chatMessages, newMessage],
            },
          }));
        },
        updateLastMessage: (updates) => {
          set((state) => {
            const messages = [...state.workspace.chatMessages];
            if (messages.length > 0) {
              messages[messages.length - 1] = { ...messages[messages.length - 1], ...updates };
            }
            return {
              workspace: { ...state.workspace, chatMessages: messages },
            };
          });
        },
        clearChat: () =>
          set((state) => ({ workspace: { ...state.workspace, chatMessages: [] } })),
        setFactChecking: (factChecking) =>
          set((state) => ({ workspace: { ...state.workspace, factChecking } })),
        setCurrentFactCheck: (currentFactCheck) =>
          set((state) => ({ workspace: { ...state.workspace, currentFactCheck } })),
        clearWorkspace: () => set({ workspace: initialWorkspaceState }),

        // UI State
        ui: {
          theme: 'light',
          sidebarOpen: false,
          currentPlayer: {
            isPlaying: false,
            currentTime: 0,
            duration: 0,
          },
        },
        setTheme: (theme) =>
          set((state) => ({ ui: { ...state.ui, theme } })),
        setSidebarOpen: (sidebarOpen) =>
          set((state) => ({ ui: { ...state.ui, sidebarOpen } })),
        setPlayerState: (playerState) =>
          set((state) => ({
            ui: { ...state.ui, currentPlayer: { ...state.ui.currentPlayer, ...playerState } },
          })),

        // Saved Content
        savedInsights: [],
        addSavedInsight: (insight) => {
          const newInsight = {
            ...insight,
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
          };
          set((state) => ({
            savedInsights: [newInsight, ...state.savedInsights],
          }));
        },
        removeSavedInsight: (id) =>
          set((state) => ({
            savedInsights: state.savedInsights.filter((insight) => insight.id !== id),
          })),
        clearSavedInsights: () => set({ savedInsights: [] }),
      }),
      {
        name: 'podsearch-storage',
        partialize: (state) => ({
          savedInsights: state.savedInsights,
          ui: { theme: state.ui.theme },
        }),
        skipHydration: true,
      }
    ),
    { name: 'PodSearch Store' }
  )
);

// Selectors for better performance
export const useSearchState = () => useStore((state) => state.search);
export const useWorkspaceState = () => useStore((state) => state.workspace);
export const useUIState = () => useStore((state) => state.ui);
export const useSavedInsights = () => useStore((state) => state.savedInsights);

// Actions
export const useSearchActions = () => ({
  setSearchQuery: useStore((state) => state.setSearchQuery),
  setSearchResults: useStore((state) => state.setSearchResults),
  setSearchLoading: useStore((state) => state.setSearchLoading),
  setSearchError: useStore((state) => state.setSearchError),
  clearSearch: useStore((state) => state.clearSearch),
});

export const useWorkspaceActions = () => ({
  setCurrentVideo: useStore((state) => state.setCurrentVideo),
  setTranscript: useStore((state) => state.setTranscript),
  setIsProcessing: useStore((state) => state.setIsProcessing),
  setIsProcessed: useStore((state) => state.setIsProcessed),
  setRagReady: useStore((state) => state.setRagReady),
  addChatMessage: useStore((state) => state.addChatMessage),
  updateLastMessage: useStore((state) => state.updateLastMessage),
  clearChat: useStore((state) => state.clearChat),
  setFactChecking: useStore((state) => state.setFactChecking),
  setCurrentFactCheck: useStore((state) => state.setCurrentFactCheck),
  clearWorkspace: useStore((state) => state.clearWorkspace),
});

export const useUIActions = () => ({
  setTheme: useStore((state) => state.setTheme),
  setSidebarOpen: useStore((state) => state.setSidebarOpen),
  setPlayerState: useStore((state) => state.setPlayerState),
});

export const useSavedInsightsActions = () => ({
  addSavedInsight: useStore((state) => state.addSavedInsight),
  removeSavedInsight: useStore((state) => state.removeSavedInsight),
  clearSavedInsights: useStore((state) => state.clearSavedInsights),
}); 