'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';

// Force dynamic rendering to avoid NextRouter mounting issues during build
export const dynamic = 'force-dynamic';
import { useParams } from 'next/navigation';
import dynamicImport from 'next/dynamic';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge, FactCheckBadge } from '@/components/ui/Badge';
import { LoadingSpinner, PageLoading } from '@/components/ui/LoadingSpinner';
import { 
  useWorkspaceState, 
  useWorkspaceActions, 
  useUIActions,
  useSavedInsightsActions 
} from '@/store/useStore';
import { 
  transcriptApi, 
  ragApi, 
  factVerificationApi,
  utils 
} from '@/lib/api';
import { 
  ChatMessage,
  TranscriptSegment,
  ClaimVerification,
  RAGGenerateResponse
} from '@/types/api';
import { 
  Send, 
  MessageCircle,
  FileText,
  CheckCircle,
  Clock,
  Bookmark,
  Share,
  Copy,
  ExternalLink
} from 'lucide-react';
import toast from 'react-hot-toast';

// Dynamically import ReactPlayer to avoid SSR issues
const ReactPlayer = dynamicImport(() => import('react-player'), { ssr: false });

interface ChatMessageWithSources extends ChatMessage {
  ragResponse?: RAGGenerateResponse;
}

export default function WorkspacePage() {
  const params = useParams();
  const videoId = params?.videoId as string;
  
  const workspace = useWorkspaceState();
  const { 
    setCurrentVideo,
    setTranscript,
    setIsProcessing,
    setIsProcessed,
    setRagReady,
    addChatMessage,
    updateLastMessage,
    setFactChecking,
    setCurrentFactCheck
  } = useWorkspaceActions();
  const { setPlayerState } = useUIActions();
  const { addSavedInsight } = useSavedInsightsActions();

  const [chatInput, setChatInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isInitializing, setIsInitializing] = useState(false);
  const [currentTab, setCurrentTab] = useState<'chat' | 'transcript' | 'facts'>('chat');
  const [selectedClaim, setSelectedClaim] = useState<ClaimVerification | null>(null);
  const [playerReady, setPlayerReady] = useState(false);
  
  const playerRef = useRef<any>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Initialize workspace with video data
  useEffect(() => {
    if (videoId && !workspace.currentVideo) {
      initializeWorkspace();
    } else if (workspace.currentVideo && workspace.currentVideo.id === videoId) {
      setIsLoading(false);
    } else if (!videoId) {
      setIsLoading(false);
    }
  }, [videoId, workspace.currentVideo]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [workspace.chatMessages]);

  const initializeWorkspace = async () => {
    if (isInitializing) return;

    try {
      setIsInitializing(true);
      setIsLoading(true);
      
      const videoData = await fetchVideoData();
      if (!videoData) {
        throw new Error('Failed to fetch video data');
      }
      
      setCurrentVideo(videoData);
      await processTranscriptForRAG();
      
    } catch (error: any) {
      console.error('Workspace initialization error:', error);
      toast.error('Failed to initialize workspace');
      setCurrentVideo(null);
      setRagReady(false);
      setIsProcessed(false);
    } finally {
      setIsInitializing(false);
      setIsLoading(false);
    }
  };

  const fetchVideoData = async () => {
    try {
      const videoData = {
        id: videoId,
        title: 'Loading...',
        url: `https://www.youtube.com/watch?v=${videoId}`,
        uploader: '',
        view_count: 0,
        upload_date: '',
        duration: 0,
        description: '',
        thumbnail_url: `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`,
        has_captions: true,
        available_languages: []
      };
      
      const savedSearchResults = localStorage.getItem('recentSearchResults');
      if (savedSearchResults) {
        const results = JSON.parse(savedSearchResults);
        const foundVideo = results.find((v: any) => v.id === videoId);
        if (foundVideo) {
          return foundVideo;
        }
      }
      
      return videoData;
    } catch (error) {
      console.error('Error fetching video data:', error);
      return null;
    }
  };

  const processTranscriptForRAG = async () => {
    try {
      setIsProcessing(true);
      
      const transcriptResponse = await transcriptApi.getTranscript(videoId);
      
      if (!transcriptResponse.success) {
        throw new Error(transcriptResponse.metadata?.error || 'Failed to extract transcript');
      }
      
      if (!transcriptResponse.segments || transcriptResponse.segments.length === 0) {
        throw new Error('No transcript segments found');
      }
      
      setTranscript(transcriptResponse.segments);
      
      const ragResponse = await ragApi.processTranscript(videoId, { overwrite: false });
      
      if (ragResponse.success) {
        setRagReady(true);
        setIsProcessed(true);
        toast.success('Video processed successfully!');
      } else if (ragResponse.error?.includes('already processed')) {
        setRagReady(true);
        setIsProcessed(true);
        toast.success('Video is ready for chat!');
      } else {
        throw new Error(ragResponse.error || 'Failed to process transcript');
      }
      
    } catch (error: any) {
      console.error('Processing error:', error);
      if (error.response?.status === 404) {
        toast.error('Video transcript not found');
      } else if (error.message?.includes('transcript')) {
        toast.error(`Transcript error: ${error.message}`);
      } else {
        toast.error('Failed to process video for AI search');
      }
      setRagReady(false);
      setIsProcessed(false);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  };

  // Add a retry function for manual retries
  const retryProcessing = async () => {
    await initializeWorkspace();
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || !workspace.ragReady) return;

    const userMessage = chatInput.trim();
    setChatInput('');

    addChatMessage({
      type: 'user',
      content: userMessage,
    });

    addChatMessage({
      type: 'assistant',
      content: '',
      isTyping: true,
    });

    try {
      const ragResponse = await ragApi.generateResponse(videoId, {
        query: userMessage,
        top_k: 100,
      });

      if (ragResponse.success) {
        updateLastMessage({
          content: ragResponse.answer,
          sources: ragResponse.sources,
          isTyping: false,
        });

        if (ragResponse.answer) {
          await factCheckResponse(ragResponse.answer, ragResponse);
        }
      } else {
        throw new Error(ragResponse.error || 'Failed to generate response');
      }
    } catch (error: any) {
      console.error('Chat error:', error);
      updateLastMessage({
        content: 'Sorry, I encountered an error while processing your question. Please try again.',
        isTyping: false,
      });
      toast.error('Failed to get response');
    }
  };

  const factCheckResponse = async (answer: string, ragResponse: RAGGenerateResponse) => {
    try {
      setFactChecking(true);
      
      const factCheckResponse = await factVerificationApi.verifyClaims({
        claims: [answer],
        video_id: videoId,
        context: ragResponse.sources.map(s => s.text).join(' '),
        search_depth: 3,
        include_academic: true,
        include_news: true,
      });

      if (factCheckResponse.success && factCheckResponse.verifications.length > 0) {
        setCurrentFactCheck(factCheckResponse.verifications);
        
        updateLastMessage({
          factCheck: factCheckResponse.verifications,
        });
      }
    } catch (error) {
      console.error('Fact-check error:', error);
    } finally {
      setFactChecking(false);
    }
  };

  const jumpToTimestamp = (timestamp: number) => {
    if (playerRef.current) {
      playerRef.current.seekTo(timestamp, 'seconds');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  if (isLoading) {
    return (
      <Layout title="Loading Workspace">
        <PageLoading message="Preparing your workspace..." />
      </Layout>
    );
  }

  return (
    <Layout title={workspace.currentVideo?.title || 'Workspace'}>
      <div className="h-[calc(100vh-4rem)] flex">
        {/* Left Panel - Video Player */}
        <div className="flex-1 flex flex-col bg-black">
          {/* Video Player */}
          <div className="flex-1 relative">
            {workspace.currentVideo && (
              <ReactPlayer
                ref={playerRef}
                url={workspace.currentVideo.url}
                width="100%"
                height="100%"
                onReady={() => setPlayerReady(true)}
                controls
                config={{
                  youtube: {
                    playerVars: {
                      showinfo: 1,
                      controls: 1,
                    },
                  },
                }}
              />
            )}
          </div>

          {/* Video Info */}
          <div className="bg-gray-900 text-white p-4">
            <h2 className="text-lg font-semibold mb-2 line-clamp-2">
              {workspace.currentVideo?.title}
            </h2>
            <div className="flex items-center justify-between text-sm text-gray-300">
              <div className="flex items-center space-x-4">
                <span>{workspace.currentVideo?.uploader}</span>
                <span>•</span>
                <span>{workspace.currentVideo?.view_count?.toLocaleString()} views</span>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-white hover:text-gray-300"
                >
                  <Bookmark className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-white hover:text-gray-300"
                  onClick={() => workspace.currentVideo && copyToClipboard(workspace.currentVideo.url)}
                >
                  <Share className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Transcript & Chat */}
        <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
          <div className="flex border-b border-gray-200">
            {[
              { id: 'chat', label: 'Chat', icon: MessageCircle },
              { id: 'transcript', label: 'Transcript', icon: FileText },
              { id: 'facts', label: 'Facts', icon: CheckCircle },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id as any)}
                className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                  currentTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-hidden">
            {currentTab === 'chat' && (
              <div className="h-full flex flex-col">
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {workspace.chatMessages.length === 0 ? (
                    <div className="text-center text-gray-500 mt-8">
                      <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                      <p className="text-sm">Ask any question about this podcast!</p>
                      <p className="text-xs mt-2">Try: "What are the main points discussed?"</p>
                    </div>
                  ) : (
                    <>
                      {workspace.chatMessages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[80%] rounded-lg px-3 py-2 ${
                              message.type === 'user'
                                ? 'bg-primary-600 text-white'
                                : 'bg-gray-100 text-gray-900'
                            }`}
                          >
                            {message.isTyping ? (
                              <div className="flex items-center space-x-1">
                                <LoadingSpinner size="sm" />
                                <span className="text-sm">Thinking...</span>
                              </div>
                            ) : (
                              <>
                                <p className="text-sm">{message.content}</p>
                                
                                {message.sources && message.sources.length > 0 && (
                                  <div className="mt-2 pt-2 border-t border-gray-200">
                                    <p className="text-xs font-medium mb-1">Sources:</p>
                                    {message.sources.slice(0, 2).map((source, idx) => (
                                      <button
                                        key={idx}
                                        onClick={() => jumpToTimestamp(source.timestamp || 0)}
                                        className="block text-xs text-primary-600 hover:text-primary-800 mb-1"
                                      >
                                        <Clock className="h-3 w-3 inline mr-1" />
                                        {utils.formatTimestamp(source.timestamp || 0)} - 
                                        {utils.truncateText(source.text, 60)}
                                      </button>
                                    ))}
                                  </div>
                                )}

                                {message.factCheck && message.factCheck.length > 0 && (
                                  <div className="mt-2 pt-2 border-t border-gray-200">
                                    <div className="flex items-center justify-between mb-1">
                                      <p className="text-xs font-medium">Fact Check:</p>
                                      {workspace.factChecking && (
                                        <LoadingSpinner size="sm" />
                                      )}
                                    </div>
                                    {message.factCheck.map((fact, idx) => (
                                      <div key={idx} className="mb-1">
                                        <FactCheckBadge
                                          status={fact.status}
                                          confidence={fact.confidence}
                                          className="text-xs"
                                        />
                                      </div>
                                    ))}
                                  </div>
                                )}

                                {message.type === 'assistant' && !message.isTyping && (
                                  <div className="flex items-center space-x-2 mt-2">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => copyToClipboard(message.content)}
                                    >
                                      <Copy className="h-3 w-3" />
                                    </Button>
                                  </div>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                      <div ref={chatEndRef} />
                    </>
                  )}
                </div>

                <div className="p-4 border-t border-gray-200">
                  <form onSubmit={handleChatSubmit} className="flex space-x-2">
                    <Input
                      type="text"
                      placeholder="Ask about this podcast..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      disabled={workspace.isProcessing || !workspace.ragReady}
                      className="flex-1"
                    />
                    <Button
                      type="submit"
                      size="icon"
                      disabled={!chatInput.trim() || workspace.isProcessing || !workspace.ragReady}
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </form>
                  
                  {workspace.isProcessing && (
                    <p className="text-xs text-gray-500 mt-2">Processing transcript...</p>
                  )}
                  {!workspace.ragReady && !workspace.isProcessing && (
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-xs text-gray-500">Transcript not ready for chat</p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={retryProcessing}
                        disabled={isInitializing}
                        className="text-xs px-2 py-1"
                      >
                        {isInitializing ? (
                          <>
                            <LoadingSpinner size="sm" className="mr-1" />
                            Retrying...
                          </>
                        ) : (
                          'Retry'
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {currentTab === 'transcript' && (
              <div className="h-full overflow-y-auto p-4">
                {workspace.transcript.length > 0 ? (
                  <div className="space-y-2">
                    {workspace.transcript.map((segment, index) => (
                      <button
                        key={index}
                        onClick={() => jumpToTimestamp(segment.timestamp || 0)}
                        className="block w-full text-left p-2 rounded hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-start space-x-2">
                          <Badge variant="outline" className="text-xs">
                            {utils.formatTimestamp(segment.timestamp || 0)}
                          </Badge>
                          <p className="text-sm text-gray-700 flex-1">
                            {segment.text}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 mt-8">
                    <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-sm">No transcript available</p>
                  </div>
                )}
              </div>
            )}

            {currentTab === 'facts' && (
              <div className="h-full overflow-y-auto p-4">
                {workspace.currentFactCheck && workspace.currentFactCheck.length > 0 ? (
                  <div className="space-y-4">
                    {workspace.currentFactCheck.map((fact, index) => (
                      <Card
                        key={index}
                        className="cursor-pointer hover:shadow-md transition-shadow"
                        onClick={() => setSelectedClaim(fact)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between mb-2">
                            <FactCheckBadge
                              status={fact.status}
                              confidence={fact.confidence}
                            />
                          </div>
                          <p className="text-sm text-gray-700 mb-2">
                            {utils.truncateText(fact.claim, 120)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {fact.sources.length} source{fact.sources.length !== 1 ? 's' : ''}
                          </p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 mt-8">
                    <CheckCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-sm">No fact-checks available</p>
                    <p className="text-xs mt-2">Facts will appear here after asking questions</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Claim Detail Modal */}
      {selectedClaim && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedClaim(null)}
        >
          <div
            className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <CardTitle>Fact Check Details</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedClaim(null)}
                >
                  ×
                </Button>
              </div>
            </CardHeader>
              
            <CardContent className="p-6">
              <div className="space-y-4">
                <div>
                  <FactCheckBadge
                    status={selectedClaim.status}
                    confidence={selectedClaim.confidence}
                    className="mb-2"
                  />
                  <h3 className="font-semibold mb-2">Claim</h3>
                  <p className="text-gray-700">{selectedClaim.claim}</p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Explanation</h3>
                  <p className="text-gray-700">{selectedClaim.explanation}</p>
                </div>

                {selectedClaim.sources.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-2">Sources</h3>
                    <div className="space-y-2">
                      {selectedClaim.sources.map((source, idx) => (
                        <div key={idx} className="border rounded-lg p-3">
                          <div className="flex items-center justify-between mb-2">
                            <Badge variant="outline">
                              {source.source_type}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              Relevance: {Math.round(source.relevance_score * 100)}%
                            </span>
                          </div>
                          <h4 className="font-medium text-sm mb-1">
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary-600 hover:text-primary-800 flex items-center"
                            >
                              {source.title}
                              <ExternalLink className="h-3 w-3 ml-1" />
                            </a>
                          </h4>
                          <p className="text-xs text-gray-600">
                            {source.excerpt}
                          </p>
                          {source.author && (
                            <p className="text-xs text-gray-500 mt-1">
                              By {source.author}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </div>
        </div>
      )}
    </Layout>
  );
} 