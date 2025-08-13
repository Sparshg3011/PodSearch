
export interface YouTubeVideo {
  id: string;
  title: string;
  duration?: number;
  view_count?: number;
  upload_date?: string;
  uploader?: string;
  description?: string;
  thumbnail_url?: string;
  available_languages: string[];
  has_captions: boolean;
  url: string;
}

export interface YouTubeSearchResponse {
  results: YouTubeVideo[];
  query: string;
}

export interface TranscriptSegment {
  text: string;
  timestamp?: number;
}

export interface TranscriptWithTimestampsResponse {
  success: boolean;
  video_id: string;
  segments: TranscriptSegment[];
  metadata: Record<string, any>;
}

export interface RAGSearchRequest {
  query: string;
  top_k: number;
}

export interface RAGSearchResult {
  text: string;
  timestamp?: number;
  segment_index: number;
  relevance_score: number;
  metadata: Record<string, any>;
}

export interface RAGSearchResponse {
  success: boolean;
  query: string;
  video_id: string;
  results: RAGSearchResult[];
  error?: string;
}

export interface RAGGenerateRequest {
  query: string;
  top_k: number;
}

export interface RAGGenerateResponse {
  success: boolean;
  query: string;
  video_id: string;
  answer: string;
  sources: RAGSearchResult[];
  retrieval_only: boolean;
  error?: string;
}

export interface RAGProcessRequest {
  overwrite: boolean;
}

export interface RAGProcessResponse {
  success: boolean;
  video_id: string;
  chunks_stored?: number;
  collection_name?: string;
  error?: string;
}

export interface RAGCollection {
  name: string;
  count: number;
  last_updated?: string;
}

export interface RAGListResponse {
  collections: RAGCollection[];
  count: number;
}

export interface VerifyRequest {
  video_id?: string;
  claim_text: string;
  start_ts?: number;
  end_ts?: number;
  max_sources?: number;
}

export interface VerificationSource {
  url: string;
  domain: string;
  title?: string;
  published_at?: string;
  snippet: string;
  screenshot_b64?: string;
  url_with_text_fragment?: string;
  similarity: number;
  entailment_score?: number;
}

export interface ClaimVerification {
  text: string;
  verdict: string;
  confidence: number;
  sources: VerificationSource[];
}

export interface VerifyResponse {
  success: boolean;
  claim: string;
  result?: ClaimVerification;
  error?: string;
}

export interface SearchState {
  query: string;
  results: YouTubeVideo[];
  loading: boolean;
  error: string | null;
}

export interface WorkspaceState {
  currentVideo: YouTubeVideo | null;
  transcript: TranscriptSegment[];
  isProcessing: boolean;
  isProcessed: boolean;
  ragReady: boolean;
  chatMessages: ChatMessage[];
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: RAGSearchResult[];
  isTyping?: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface TimestampedContent {
  text: string;
  timestamp: number;
  duration?: number;
} 