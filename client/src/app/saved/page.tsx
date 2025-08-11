'use client';

import React, { useState } from 'react';

export const dynamic = 'force-dynamic';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useSavedInsights, useSavedInsightsActions } from '@/store/useStore';
import { utils } from '@/lib/api';
import { 
  Bookmark, 
  Trash2, 
  ExternalLink, 
  Clock,
  Search,
  Share,
  Copy,
  Calendar,
  Play
} from 'lucide-react';
import toast from 'react-hot-toast';

const formatTimeAgo = (date: Date) => {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
};

export default function SavedPage() {
  const savedInsights = useSavedInsights();
  const { removeSavedInsight, clearSavedInsights } = useSavedInsightsActions();
  const [searchQuery, setSearchQuery] = useState('');

  const handleDelete = (id: string) => {
    removeSavedInsight(id);
    toast.success('Insight deleted');
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to delete all saved insights?')) {
      clearSavedInsights();
      toast.success('All insights cleared');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const shareInsight = (insight: any) => {
    const shareText = `"${insight.answer}" - From "${insight.videoTitle}"`;
    copyToClipboard(shareText);
  };

  const openInWorkspace = (videoId: string) => {
    window.open(`/workspace/${videoId}`, '_blank');
  };

  const filteredInsights = savedInsights.filter(insight => {
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      const matchesSearch = 
        insight.query.toLowerCase().includes(searchLower) ||
        insight.answer.toLowerCase().includes(searchLower) ||
        insight.videoTitle.toLowerCase().includes(searchLower);
      if (!matchesSearch) return false;
    }
    return true;
  });

    return (
    <Layout title="Saved Insights">
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="mb-10">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-3">Saved Insights</h1>
              <p className="text-xl text-gray-600">
                Your collection of podcast insights
              </p>
            </div>
            
            <div className="flex items-center justify-between mb-8">
              <div></div>
              
              {savedInsights.length > 0 && (
                <Button
                  variant="outline"
                  onClick={handleClearAll}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
              )}
            </div>

            {savedInsights.length > 0 && (
              <div className="max-w-2xl mx-auto mb-8">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search your insights..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white shadow-sm text-lg transition-all"
                  />
                </div>
              </div>
            )}

            {savedInsights.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-10">
                <Card className="bg-white border-0 shadow-lg">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-500 mb-1">Total Insights</p>
                        <p className="text-3xl font-bold text-gray-900">{savedInsights.length}</p>
                      </div>
                      <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
                        <Bookmark className="h-6 w-6 text-primary-600" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-white border-0 shadow-lg">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-500 mb-1">Videos</p>
                        <p className="text-3xl font-bold text-gray-900">
                          {new Set(savedInsights.map(i => i.videoId)).size}
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                        <Play className="h-6 w-6 text-green-600" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-white border-0 shadow-lg">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-500 mb-1">Recent</p>
                        <p className="text-3xl font-bold text-gray-900">
                          {savedInsights.filter(i => 
                            new Date().getTime() - new Date(i.timestamp).getTime() < 7 * 24 * 60 * 60 * 1000
                          ).length}
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                        <Calendar className="h-6 w-6 text-blue-600" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {savedInsights.length === 0 && (
            <div className="text-center py-20">
              <div className="w-24 h-24 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Bookmark className="h-12 w-12 text-gray-400" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                No saved insights yet
              </h3>
              <p className="text-lg text-gray-600 mb-8 max-w-lg mx-auto leading-relaxed">
                Start exploring podcasts and save interesting insights to build your personal knowledge collection.
              </p>
              <Button
                onClick={() => window.location.href = '/'}
                className="inline-flex items-center px-6 py-3 text-lg"
              >
                <Search className="h-5 w-5 mr-2" />
                Start Searching
              </Button>
            </div>
          )}

                    {filteredInsights.length > 0 && (
            <div className="space-y-8">
              {filteredInsights.map((insight) => (
                <Card key={insight.id} className="hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-0 shadow-lg bg-white rounded-2xl overflow-hidden">
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-xl font-bold mb-3 line-clamp-2 text-gray-900">
                          {insight.query}
                        </CardTitle>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span className="bg-gray-100 px-3 py-1 rounded-full">{formatTimeAgo(new Date(insight.timestamp))}</span>
                          <span>•</span>
                          <span className="truncate max-w-xs font-medium">{insight.videoTitle}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => shareInsight(insight)}
                          className="text-gray-500 hover:text-gray-700"
                        >
                          <Share className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(insight.id)}
                          className="text-gray-500 hover:text-red-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="pt-0">
                    <div className="mb-6">
                      <p className="text-gray-800 leading-relaxed text-lg">
                        {insight.answer}
                      </p>
                    </div>

                    {insight.sources && insight.sources.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">
                          Sources ({insight.sources.length})
                        </h4>
                        <div className="space-y-3">
                          {insight.sources.slice(0, 2).map((source, idx) => (
                            <button
                              key={idx}
                              onClick={() => openInWorkspace(insight.videoId)}
                              className="flex items-start space-x-3 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors w-full text-left border border-gray-100 hover:border-gray-200"
                            >
                              <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                                <Clock className="h-4 w-4 text-primary-600" />
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-2">
                                  <Badge variant="outline" className="text-xs font-medium">
                                    {utils.formatTimestamp(source.timestamp || 0)}
                                  </Badge>
                                </div>
                                <p className="text-sm text-gray-700 line-clamp-2 leading-relaxed">
                                  {source.text}
                                </p>
                              </div>
                            </button>
                          ))}
                          {insight.sources.length > 2 && (
                            <button
                              onClick={() => openInWorkspace(insight.videoId)}
                              className="text-sm text-primary-600 hover:text-primary-800"
                            >
                              +{insight.sources.length - 2} more sources
                            </button>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                      <div className="flex items-center space-x-3">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(insight.answer)}
                          className="border-2"
                        >
                          <Copy className="h-4 w-4 mr-2" />
                          Copy Answer
                        </Button>
                      </div>
                      
                      <Button
                        size="sm"
                        onClick={() => openInWorkspace(insight.videoId)}
                        className="bg-primary-600 hover:bg-primary-700 shadow-lg"
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Open Workspace
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {savedInsights.length > 0 && filteredInsights.length === 0 && (
            <div className="text-center py-16">
              <Search className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No insights found
              </h3>
              <p className="text-gray-600 mb-6">
                Try adjusting your search query
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  setSearchQuery('');
                }}
              >
                Clear Filters
              </Button>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
} 