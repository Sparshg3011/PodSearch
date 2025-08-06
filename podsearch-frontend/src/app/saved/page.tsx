'use client';

import React, { useState } from 'react';

// Force dynamic rendering to avoid NextRouter mounting issues during build
export const dynamic = 'force-dynamic';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge, FactCheckBadge } from '@/components/ui/Badge';
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
  Download,
  Filter,
  Calendar,
  Play
} from 'lucide-react';
import toast from 'react-hot-toast';

// Simple utility to replace date-fns
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
  const [filterBy, setFilterBy] = useState<'all' | 'verified' | 'unverified'>('all');

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

  // Filter insights based on search and filter criteria
  const filteredInsights = savedInsights.filter(insight => {
    // Search filter
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      const matchesSearch = 
        insight.query.toLowerCase().includes(searchLower) ||
        insight.answer.toLowerCase().includes(searchLower) ||
        insight.videoTitle.toLowerCase().includes(searchLower);
      
      if (!matchesSearch) return false;
    }

    // Fact-check filter
    if (filterBy !== 'all') {
      if (!insight.factCheck || insight.factCheck.length === 0) {
        return filterBy === 'unverified';
      }
      
      const hasVerified = insight.factCheck.some(fact => 
        fact.status === '✅ Verified'
      );
      
      return filterBy === 'verified' ? hasVerified : !hasVerified;
    }

    return true;
  });

  return (
    <Layout title="Saved Insights">
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Saved Insights</h1>
                <p className="text-gray-600 mt-2">
                  Your collection of podcast insights and fact-checked information
                </p>
              </div>
              
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

            {/* Search and Filters */}
            {savedInsights.length > 0 && (
              <div className="flex flex-col sm:flex-row gap-4 mb-6">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search insights..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <Filter className="h-4 w-4 text-gray-500" />
                  <select
                    value={filterBy}
                    onChange={(e) => setFilterBy(e.target.value as any)}
                    className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="all">All Insights</option>
                    <option value="verified">Fact-Checked</option>
                    <option value="unverified">Unverified</option>
                  </select>
                </div>
              </div>
            )}

            {/* Stats */}
            {savedInsights.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Total Insights</p>
                        <p className="text-2xl font-bold text-gray-900">{savedInsights.length}</p>
                      </div>
                      <Bookmark className="h-8 w-8 text-primary-600" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Fact-Checked</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {savedInsights.filter(i => i.factCheck && i.factCheck.length > 0).length}
                        </p>
                      </div>
                      <Badge className="h-8 w-8 rounded-full flex items-center justify-center" variant="success">
                        ✓
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Videos</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {new Set(savedInsights.map(i => i.videoId)).size}
                        </p>
                      </div>
                      <Play className="h-8 w-8 text-primary-600" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* Empty State */}
          {savedInsights.length === 0 && (
            <div className="text-center py-16">
              <Bookmark className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No saved insights yet
              </h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                Start exploring podcasts and save interesting insights to build your personal knowledge collection.
              </p>
              <Button
                onClick={() => window.location.href = '/'}
                className="inline-flex items-center"
              >
                <Search className="h-4 w-4 mr-2" />
                Start Searching
              </Button>
            </div>
          )}

          {/* Insights Grid */}
          {filteredInsights.length > 0 && (
            <div className="space-y-6">
              {filteredInsights.map((insight) => (
                <Card key={insight.id} className="hover:shadow-lg transition-shadow duration-300">
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg mb-2 line-clamp-2">
                          {insight.query}
                        </CardTitle>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            <span>{formatTimeAgo(new Date(insight.timestamp))}</span>
                          </div>
                          <div className="flex items-center">
                            <Play className="h-4 w-4 mr-1" />
                            <span className="truncate max-w-xs">{insight.videoTitle}</span>
                          </div>
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
                    {/* Answer */}
                    <div className="mb-4">
                      <p className="text-gray-700 leading-relaxed">
                        {insight.answer}
                      </p>
                    </div>

                    {/* Sources */}
                    {insight.sources && insight.sources.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">
                          Sources ({insight.sources.length})
                        </h4>
                        <div className="space-y-2">
                          {insight.sources.slice(0, 2).map((source, idx) => (
                            <button
                              key={idx}
                              onClick={() => openInWorkspace(insight.videoId)}
                              className="flex items-start space-x-2 p-2 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors w-full text-left"
                            >
                              <Clock className="h-4 w-4 text-primary-600 mt-0.5 flex-shrink-0" />
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-1">
                                  <Badge variant="outline" className="text-xs">
                                    {utils.formatTimestamp(source.timestamp || 0)}
                                  </Badge>
                                  <span className="text-xs text-gray-500">
                                    {Math.round(source.relevance_score * 100)}% relevant
                                  </span>
                                </div>
                                <p className="text-sm text-gray-700 line-clamp-2">
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

                    {/* Fact Check Results */}
                    {insight.factCheck && insight.factCheck.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">
                          Fact Check Results
                        </h4>
                        <div className="space-y-2">
                          {insight.factCheck.map((fact, idx) => (
                            <div key={idx} className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50">
                              <FactCheckBadge
                                status={fact.status}
                                confidence={fact.confidence}
                                className="mt-0.5"
                              />
                              <div className="flex-1">
                                <p className="text-sm text-gray-700 mb-1">
                                  {utils.truncateText(fact.claim, 120)}
                                </p>
                                <p className="text-xs text-gray-500">
                                  {fact.explanation}
                                </p>
                                {fact.sources.length > 0 && (
                                  <p className="text-xs text-gray-400 mt-1">
                                    Verified with {fact.sources.length} source{fact.sources.length !== 1 ? 's' : ''}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(insight.answer)}
                        >
                          <Copy className="h-4 w-4 mr-2" />
                          Copy Answer
                        </Button>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openInWorkspace(insight.videoId)}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Open in Workspace
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* No Results */}
          {savedInsights.length > 0 && filteredInsights.length === 0 && (
            <div className="text-center py-16">
              <Search className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No insights found
              </h3>
              <p className="text-gray-600 mb-6">
                Try adjusting your search query or filters
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  setSearchQuery('');
                  setFilterBy('all');
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