// YouTube API Types
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

// Transcript Types
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

// RAG Types
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

// Fact Verification Types
export type VerificationStatus = "✅ Verified" | "⚠️ Partially Verified" | "❌ False" | "🔍 Unclear/Insufficient Evidence";

export type SourceType = "Wikipedia" | "PubMed" | "Semantic Scholar" | "News" | "Search Engine" | "Academic";

export interface VerificationSource {
  title: string;
  url: string;
  source_type: SourceType;
  relevance_score: number;
  excerpt: string;
  publication_date?: string;
  author?: string;
}

export interface ClaimVerification {
  claim: string;
  status: VerificationStatus;
  confidence: number;
  explanation: string;
  sources: VerificationSource[];
  verification_date: string;
  agent_reasoning: string;
}

export interface FactVerificationRequest {
  claims: string[];
  video_id?: string;
  context?: string;
  search_depth: number;
  include_academic: boolean;
  include_news: boolean;
}

export interface FactVerificationResponse {
  success: boolean;
  verifications: ClaimVerification[];
  total_claims: number;
  processing_time: number;
  error?: string;
}

export interface BatchVerificationRequest {
  transcript_id: string;
  auto_extract_claims: boolean;
  custom_claims: string[];
  max_claims: number;
  search_depth: number;
}

export interface BatchVerificationResponse {
  success: boolean;
  transcript_id: string;
  extracted_claims: string[];
  verifications: ClaimVerification[];
  summary: Record<string, number>;
  processing_time: number;
  error?: string;
}

export interface VerificationStatsResponse {
  total_verifications: number;
  verification_breakdown: Record<VerificationStatus, number>;
  source_breakdown: Record<SourceType, number>;
  average_confidence: number;
  most_recent_verification?: string;
}

// UI State Types
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
  factChecking: boolean;
  currentFactCheck: ClaimVerification[] | null;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: RAGSearchResult[];
  factCheck?: ClaimVerification[];
  isTyping?: boolean;
}

// Utility Types
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