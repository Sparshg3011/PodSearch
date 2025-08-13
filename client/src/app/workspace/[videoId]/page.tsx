'use client';

import React, { useEffect, useState, useRef } from 'react';

export const dynamic = 'force-dynamic';
import { useParams } from 'next/navigation';
import dynamicImport from 'next/dynamic';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner, PageLoading } from '@/components/ui/LoadingSpinner';
import { 
  useWorkspaceState, 
  useWorkspaceActions, 
  useUIActions
} from '@/store/useStore';
import { 
  transcriptApi, 
  ragApi,
  utils,
  verifyApi
} from '@/lib/api';
import { 
  TranscriptSegment
} from '@/types/api';
import { 
  Send, 
  MessageCircle,
  Clock,
  Bookmark,
  Share,
  User,
  Eye
} from 'lucide-react';
import toast from 'react-hot-toast';

const ReactPlayer = dynamicImport(() => import('react-player'), { ssr: false });

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
    clearWorkspace
  } = useWorkspaceActions();
  const { setPlayerState } = useUIActions();

  const [chatInput, setChatInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isInitializing, setIsInitializing] = useState(false);

  const [playerReady, setPlayerReady] = useState(false);
  const [initializationError, setInitializationError] = useState<string | null>(null);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [retryAttempts, setRetryAttempts] = useState(0);
  const [pendingSeek, setPendingSeek] = useState<number | null>(null);
  const [messageSelections, setMessageSelections] = useState<Record<string, {text: string, verifying: boolean, result: any}>>({});
  
  const playerRef = useRef<any>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (videoId && !workspace.currentVideo && !hasInitialized && !initializationError) {
      initializeWorkspace();
    } else if (workspace.currentVideo && workspace.currentVideo.id === videoId) {
      setIsLoading(false);
    } else if (!videoId) {
      setIsLoading(false);
    }
  }, [videoId, workspace.currentVideo, hasInitialized, initializationError]);

  useEffect(() => {
    if (
      videoId &&
      workspace.currentVideo &&
      workspace.currentVideo.id === videoId &&
      !workspace.ragReady &&
      !workspace.isProcessing
    ) {
      retryTranscriptProcessing();
    }
  }, [videoId, workspace.currentVideo, workspace.ragReady, workspace.isProcessing]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [workspace.chatMessages]);

  const initializeWorkspace = async () => {
    if (isInitializing) return;

    try {
      setIsInitializing(true);
      setIsLoading(true);
      setInitializationError(null);
      
      const videoData = await fetchVideoData();
      if (!videoData) {
        throw new Error('Failed to fetch video data');
      }
      
      setCurrentVideo(videoData);
      setHasInitialized(true);
      
      try {
        await processTranscriptForRAG();
      } catch (transcriptError: any) {
        setRagReady(false);
        setIsProcessed(false);
        
        if (retryAttempts < 3) {
          setTimeout(() => {
            if (!workspace.ragReady && !workspace.isProcessing) {
              setRetryAttempts(prev => prev + 1);
              retryTranscriptProcessing();
            }
          }, 2000 * (retryAttempts + 1));
        }
      }
      
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to initialize workspace';
      setInitializationError(errorMessage);
      toast.error('Could not load video information');
      setRagReady(false);
      setIsProcessed(false);
      setHasInitialized(true);
    } finally {
      setIsInitializing(false);
      setIsLoading(false);
    }
  };

  const retryInitialization = () => {
    setHasInitialized(false);
    setInitializationError(null);
    initializeWorkspace();
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
      
      const savedSearchResults = typeof localStorage !== 'undefined' ? localStorage.getItem('recentSearchResults') : null;
      if (savedSearchResults) {
        const results = JSON.parse(savedSearchResults);
        const foundVideo = results.find((v: any) => v.id === videoId);
        if (foundVideo) {
          return foundVideo;
        }
      }
      
      return videoData;
    } catch {
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
        setRetryAttempts(0);
        toast.success('Video processed successfully!');
      } else if (ragResponse.error?.includes('Video already processed')) {
        setRagReady(true);
        setIsProcessed(true);
        setRetryAttempts(0);
        toast.success('Video is ready for chat!');
      } else {
        throw new Error(ragResponse.error || 'Failed to process transcript');
      }
      
    } catch (error: any) {
      setRagReady(false);
      setIsProcessed(false);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  };

  const retryTranscriptProcessing = async () => {
    try {
      await processTranscriptForRAG();
    } catch {}
  };

  const manualRetry = async () => {
    setRetryAttempts(0);
    await retryTranscriptProcessing();
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || !workspace.ragReady || workspace.isProcessing) return;

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
      } else {
        throw new Error(ragResponse.error || 'Failed to generate response');
      }
    } catch (error: any) {
      updateLastMessage({
        content: 'Sorry, I encountered an error while processing your question. Please try again.',
        isTyping: false,
      });
      toast.error('Failed to get response');
    }
  };

  const jumpToTimestamp = (timestamp: number) => {
    if (timestamp < 0 || Number.isNaN(timestamp)) return;
    const trySeek = () => {
      try {
        if (playerRef.current && typeof playerRef.current.seekTo === 'function') {
          playerRef.current.seekTo(timestamp, 'seconds');
          return true;
        }
      } catch {}
      return false;
    };

    if (playerReady) {
      const ok = trySeek();
      if (!ok) setPendingSeek(timestamp);
    } else {
      setPendingSeek(timestamp);
      setTimeout(() => {
        if (playerReady) trySeek();
      }, 500);
    }
  };

  const renderAnswer = (text: string, messageId: string) => {
    const parts: React.ReactNode[] = [];
    const regex = /\[(?:\s*)(?:(\d{1,2}):)?(\d{1,3}):(\d{1,2})(?:\s*)\]|\((?:\s*)(?:(\d{1,2}):)?(\d{1,3}):(\d{1,2})(?:\s*)\)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    const pad2 = (n: number) => n.toString().padStart(2, '0');

    while ((match = regex.exec(text)) !== null) {
      const hoursRaw = (match[1] ?? match[4]);
      const minutesRaw = (match[2] ?? match[5]) as string;
      const secondsRaw = (match[3] ?? match[6]) as string;
      const startIndex = match.index;

      if (startIndex > lastIndex) {
        parts.push(text.slice(lastIndex, startIndex));
      }

      let hours = hoursRaw ? parseInt(hoursRaw as string, 10) : 0;
      let minutes = parseInt(minutesRaw, 10);
      const seconds = parseInt(secondsRaw, 10);

      if (!hoursRaw && minutes >= 60) {
        hours = Math.floor(minutes / 60);
        minutes = minutes % 60;
      }

      const totalSeconds = hours * 3600 + minutes * 60 + seconds;
      const label = hours > 0
        ? `[${hours}:${pad2(minutes)}:${pad2(seconds)}]`
        : `[${minutes}:${pad2(seconds)}]`;

      parts.push(
        <span
          key={`${startIndex}-${totalSeconds}`}
          role="link"
          tabIndex={0}
          onClick={() => jumpToTimestamp(totalSeconds)}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') jumpToTimestamp(totalSeconds); }}
          className="text-primary-600 hover:text-primary-800 underline cursor-pointer"
        >
          {label}
        </span>
      );

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return <span
      onMouseUp={() => {
        const sel = window.getSelection?.()?.toString() || '';
        const selectedText = sel.trim();
        if (selectedText) {
          setMessageSelections(prev => ({
            ...prev,
            [messageId]: {
              text: selectedText,
              verifying: false,
              result: null
            }
          }));
        }
      }}
    >{parts}</span>;
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const handleVerify = async (messageId: string) => {
    const selection = messageSelections[messageId];
    if (!selection?.text || selection.verifying) return;
    
    setMessageSelections(prev => ({
      ...prev,
      [messageId]: {
        ...prev[messageId],
        verifying: true,
        result: null
      }
    }));

    try {
      const res = await verifyApi.verifyClaim({
        claim_text: selection.text,
        max_sources: 3,
      });
      
      if (res.success) {
        setMessageSelections(prev => ({
          ...prev,
          [messageId]: {
            ...prev[messageId],
            verifying: false,
            result: res.result
          }
        }));
        toast.success('Claim verified!');
      } else {
        throw new Error(res.error || 'Verification failed');
      }
    } catch (e: any) {
      toast.error(e?.message || 'Verification failed');
      setMessageSelections(prev => ({
        ...prev,
        [messageId]: {
          ...prev[messageId],
          verifying: false,
          result: null
        }
      }));
    }
  };

  if (isLoading) {
    return (
      <Layout title="Loading Workspace">
        <PageLoading message="Preparing your workspace..." />
      </Layout>
    );
  }

  if (initializationError) {
    return (
      <Layout title="Workspace Error">
        <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
          <div className="text-center space-y-4 max-w-md">
            <div className="text-red-500 text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900">Failed to Load Workspace</h2>
            <p className="text-gray-600">{initializationError}</p>
            <Button 
              onClick={retryInitialization}
              disabled={isInitializing}
              className="mt-4"
            >
              {isInitializing ? 'Retrying...' : 'Try Again'}
            </Button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={workspace.currentVideo?.title || 'Workspace'}>
      <div className="h-[calc(100vh-4rem)] flex bg-gray-50">
        <div className="flex-1 flex flex-col">
          <div className="flex-1 relative bg-black rounded-lg m-4 overflow-hidden shadow-2xl">
            {workspace.currentVideo && (
              <ReactPlayer
                ref={playerRef}
                url={workspace.currentVideo.url}
                width="100%"
                height="100%"
                onReady={() => {
                  setPlayerReady(true);
                  if (pendingSeek !== null) {
                    try { playerRef.current?.seekTo(pendingSeek, 'seconds'); } catch {}
                    setPendingSeek(null);
                  }
                }}
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

          <div className="bg-white border-t border-gray-200 p-6 m-4 mt-0 rounded-b-lg shadow-lg">
            <h2 className="text-xl font-bold text-gray-900 mb-3 line-clamp-2 leading-tight">
              {workspace.currentVideo?.title}
            </h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-gray-500" />
                  </div>
                  <span className="font-medium">{workspace.currentVideo?.uploader}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Eye className="h-4 w-4 text-gray-400" />
                  <span>{workspace.currentVideo?.view_count?.toLocaleString()} views</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                >
                  <Bookmark className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                  onClick={() => workspace.currentVideo && copyToClipboard(workspace.currentVideo.url)}
                >
                  <Share className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
          <div className="bg-gray-50 border-b border-gray-200">
            <div className="flex p-2">
              <div className="flex-1 flex items-center justify-center space-x-2 py-3 px-4 text-sm font-medium rounded-lg bg-white text-primary-600 shadow-sm border border-gray-200">
                <MessageCircle className="h-4 w-4" />
                <span>Chat</span>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-hidden">
            <div className="h-full flex flex-col">
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {workspace.chatMessages.length === 0 ? (
                    <div className="text-center text-gray-500 mt-12">
                      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <MessageCircle className="h-8 w-8 text-gray-400" />
                      </div>
                      <h3 className="text-lg font-medium text-gray-700 mb-2">Start a conversation</h3>
                      <p className="text-sm text-gray-500 mb-4">Ask any question about this podcast!</p>
                      <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
                        Try: "What are the main points discussed?"
                      </div>
                    </div>
                  ) : (
                    <>
                      {workspace.chatMessages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                              message.type === 'user'
                                ? 'bg-primary-600 text-white shadow-lg'
                                : 'bg-gray-50 text-gray-900 border border-gray-200'
                            }`}
                          >
                            {message.isTyping ? (
                              <div className="flex items-center space-x-1">
                                <LoadingSpinner size="sm" />
                                <span className="text-sm">Thinking...</span>
                              </div>
                            ) : (
                              <>
                                <p className="text-sm">{renderAnswer(message.content, message.id)}</p>
                                
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
                                {messageSelections[message.id]?.text && (
                                  <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-xl">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="text-[11px] uppercase tracking-wide text-gray-500">Selected claim</span>
                                      <button
                                        onClick={() => setMessageSelections(prev => { const next = { ...prev }; delete next[message.id]; return next; })}
                                        className="text-xs text-gray-500 hover:text-gray-700"
                                      >
                                        Clear
                                      </button>
                                    </div>
                                    <div className="text-sm text-gray-900 bg-white border border-gray-200 rounded-lg px-3 py-2">
                                      {utils.truncateText(messageSelections[message.id].text, 120)}
                                    </div>
                                    <div className="flex items-center justify-end gap-2 mt-3">
                                      <Button
                                        size="sm"
                                        onClick={() => handleVerify(message.id)}
                                        disabled={messageSelections[message.id].verifying}
                                        className="text-xs px-3 py-1"
                                      >
                                        {messageSelections[message.id].verifying ? 'Verifying…' : 'Verify'}
                                      </Button>
                                    </div>
                                    {messageSelections[message.id].result && (
                                      <div className="mt-3 p-3 bg-white border rounded-lg">
                                        <div className="flex items-center justify-between">
                                          <Badge
                                            className={`text-[11px] ${
                                              messageSelections[message.id].result.verdict === 'Supported'
                                                ? 'fact-check-verified'
                                                : messageSelections[message.id].result.verdict === 'Contradicted'
                                                  ? 'fact-check-error'
                                                  : 'fact-check-unclear'
                                            }`}
                                          >
                                            {messageSelections[message.id].result.verdict}
                                          </Badge>
                                          <span className="text-xs text-gray-600">
                                            {Math.round(messageSelections[message.id].result.confidence * 100)}% confident
                                          </span>
                                        </div>
                                        <div className="mt-2 space-y-2">
                                          {messageSelections[message.id].result.sources?.map((source: any, idx: number) => (
                                            <div key={idx} className="rounded-lg border bg-gray-50 p-2">
                                              <div className="flex items-center justify-between">
                                                <a
                                                  href={source.url_with_text_fragment || source.url}
                                                  target="_blank"
                                                  rel="noopener noreferrer"
                                                  className="text-xs font-medium text-primary-600 hover:underline underline-offset-2"
                                                >
                                                  {source.domain}
                                                </a>
                                                <span className="text-[10px] text-gray-500">{Math.round(source.similarity * 100)}% match</span>
                                              </div>
                                              <p className="text-xs text-gray-700 mt-1">
                                                {utils.truncateText(source.snippet, 160)}
                                              </p>
                                              <a
                                                href={source.url_with_text_fragment || source.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-[11px] text-primary-600 hover:text-primary-700 mt-1 inline-block"
                                              >
                                                Open source
                                              </a>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}
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

                <div className="p-6 border-t border-gray-200 bg-gray-50">
                  <form onSubmit={handleChatSubmit} className="relative">
                    <input
                      type="text"
                      placeholder="Ask about this podcast..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      disabled={workspace.isProcessing || !workspace.ragReady}
                      className="w-full pr-12 pl-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white transition-all"
                    />
                    <button
                      type="submit"
                      disabled={!chatInput.trim() || workspace.isProcessing || !workspace.ragReady}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </form>
                  
                  {workspace.isProcessing && (
                    <div className="flex items-center justify-center mt-3 text-xs text-gray-500">
                      <LoadingSpinner size="sm" className="mr-2" />
                      Processing transcript...
                    </div>
                  )}
                  {!workspace.ragReady && !workspace.isProcessing && (
                    <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-yellow-700">Transcript not ready for chat</p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={manualRetry}
                          disabled={workspace.isProcessing}
                          className="text-xs px-3 py-1 border-yellow-300 text-yellow-700 hover:bg-yellow-100"
                        >
                          Retry
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
          </div>
        </div>
      </div>
    </Layout>
  );
} 