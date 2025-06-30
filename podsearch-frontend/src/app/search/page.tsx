'use client';

import React, { useEffect, useState } from 'react';

// Force dynamic rendering to avoid NextRouter mounting issues during build
export const dynamic = 'force-dynamic';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner, PageLoading } from '@/components/ui/LoadingSpinner';
import { useSearchState, useSearchActions, useWorkspaceActions } from '@/store/useStore';
import { youtubeApi } from '@/lib/api';
import { utils } from '@/lib/api';
import { 
  Search, 
  Play, 
  Clock, 
  Eye, 
  Calendar,
  Import,
  Filter,
  SortAsc,
  Video,
  User
} from 'lucide-react';
import toast from 'react-hot-toast';
import { YouTubeVideo } from '@/types/api';

interface SortOption {
  value: string;
  label: string;
}

const sortOptions: SortOption[] = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'upload_date', label: 'Upload Date' },
  { value: 'view_count', label: 'View Count' },
  { value: 'duration', label: 'Duration' },
];

const filterOptions = [
  { value: 'all', label: 'All Durations' },
  { value: 'short', label: '< 10 min' },
  { value: 'medium', label: '10-30 min' },
  { value: 'long', label: '30+ min' },
];

export default function SearchPage() {
  const router = useRouter();
  const search = useSearchState();
  const { setSearchQuery, setSearchResults, setSearchLoading, setSearchError } = useSearchActions();
  const { setCurrentVideo } = useWorkspaceActions();
  
  const [newQuery, setNewQuery] = useState(search.query);
  const [sortBy, setSortBy] = useState('relevance');
  const [filterBy, setFilterBy] = useState('all');
  const [importing, setImporting] = useState<string | null>(null);

  useEffect(() => {
    setNewQuery(search.query);
  }, [search.query]);

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setSearchLoading(true);
    setSearchError(null);
    setSearchQuery(query);

    try {
      const results = await youtubeApi.searchVideos(query, 20);
      setSearchResults(results.results);
    } catch (error) {
      console.error('Search error:', error);
      setSearchError('Failed to search. Please try again.');
      toast.error('Search failed. Please try again.');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(newQuery);
  };

  const handleImportVideo = async (video: any) => {
    setImporting(video.id);
    setCurrentVideo(video);
    
    try {
      // Navigate to workspace
      router.push(`/workspace/${video.id}`);
      toast.success(`Imported "${utils.truncateText(video.title, 50)}" to workspace`);
    } catch (error) {
      console.error('Import error:', error);
      toast.error('Failed to import video');
    } finally {
      setImporting(null);
    }
  };

  const getFilteredAndSortedResults = () => {
    let filtered = [...search.results];

    // Apply duration filter
    if (filterBy !== 'all') {
      filtered = filtered.filter(video => {
        const duration = video.duration || 0;
        switch (filterBy) {
          case 'short':
            return duration < 600; // < 10 minutes
          case 'medium':
            return duration >= 600 && duration < 1800; // 10-30 minutes
          case 'long':
            return duration >= 1800; // 30+ minutes
          default:
            return true;
        }
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'upload_date':
          return new Date(b.upload_date || 0).getTime() - new Date(a.upload_date || 0).getTime();
        case 'view_count':
          return (b.view_count || 0) - (a.view_count || 0);
        case 'duration':
          return (b.duration || 0) - (a.duration || 0);
        default:
          return 0; // Keep original relevance order
      }
    });

    return filtered;
  };

  const filteredResults = getFilteredAndSortedResults();

  if (search.loading) {
    return (
      <Layout title="Searching...">
        <PageLoading message="Searching podcasts..." />
      </Layout>
    );
  }

  return (
    <Layout title="Search Results">
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Search Header */}
          <div className="mb-8">
            <form onSubmit={handleSubmit} className="max-w-2xl mx-auto mb-6">
              <div className="relative">
                <Input
                  type="text"
                  size="lg"
                  placeholder="Search podcasts..."
                  value={newQuery}
                  onChange={(e) => setNewQuery(e.target.value)}
                  leftIcon={<Search className="h-5 w-5" />}
                  className="pr-24"
                />
                <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                  <Button
                    type="submit"
                    size="md"
                    disabled={search.loading}
                    loading={search.loading}
                  >
                    Search
                  </Button>
                </div>
              </div>
            </form>

            {/* Results Summary */}
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Search Results for "{search.query}"
              </h2>
              <p className="text-gray-600">
                Found {filteredResults.length} podcast{filteredResults.length !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Filters and Sort */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Filter className="h-4 w-4 text-gray-500" />
                  <select
                    value={filterBy}
                    onChange={(e) => setFilterBy(e.target.value)}
                    className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                  >
                    {filterOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="flex items-center space-x-2">
                  <SortAsc className="h-4 w-4 text-gray-500" />
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                  >
                    {sortOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <Badge variant="primary" className="flex items-center">
                <Video className="h-3 w-3 mr-1" />
                YouTube Podcasts
              </Badge>
            </div>
          </div>

          {/* Error State */}
          {search.error && (
            <div className="max-w-2xl mx-auto mb-8">
              <Card variant="outline" className="border-red-200 bg-red-50">
                <CardContent className="p-6 text-center">
                  <p className="text-red-600">{search.error}</p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => handleSearch(search.query)}
                  >
                    Try Again
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Results Grid */}
          {filteredResults.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredResults.map((video) => (
                <div key={video.id}>
                  <Card className="h-full hover:shadow-lg transition-all duration-300">
                    <CardContent className="p-0">
                      {/* Thumbnail */}
                      <div className="relative aspect-video bg-gray-200 rounded-t-xl overflow-hidden">
                        {video.thumbnail_url ? (
                          <Image
                            src={video.thumbnail_url}
                            alt={video.title}
                            fill
                            className="object-cover"
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                          />
                        ) : (
                          <div className="flex items-center justify-center h-full">
                            <Video className="h-12 w-12 text-gray-400" />
                          </div>
                        )}
                        <div className="absolute bottom-2 right-2">
                          <Badge variant="default" className="bg-black/70 text-white">
                            {video.duration ? utils.formatDuration(video.duration) : 'N/A'}
                          </Badge>
                        </div>
                      </div>

                      {/* Content */}
                      <div className="p-4">
                        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 leading-tight">
                          {video.title}
                        </h3>
                        
                        <div className="flex items-center text-sm text-gray-600 mb-2">
                          <User className="h-4 w-4 mr-1" />
                          <span className="truncate">{video.uploader || 'Unknown'}</span>
                        </div>

                        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                          <div className="flex items-center">
                            <Eye className="h-4 w-4 mr-1" />
                            <span>{video.view_count ? video.view_count.toLocaleString() : 'N/A'} views</span>
                          </div>
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            <span>{video.upload_date || 'N/A'}</span>
                          </div>
                        </div>

                        {video.description && (
                          <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                            {utils.truncateText(video.description, 120)}
                          </p>
                        )}

                        <div className="flex space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1"
                            onClick={() => window.open(video.url, '_blank')}
                          >
                            <Play className="h-4 w-4 mr-1" />
                            Watch
                          </Button>
                          <Button
                            size="sm"
                            className="flex-1"
                            onClick={() => handleImportVideo(video)}
                            loading={importing === video.id}
                            disabled={importing === video.id}
                          >
                            <Import className="h-4 w-4 mr-1" />
                            Import
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          )}

          {/* No Results */}
          {!search.loading && filteredResults.length === 0 && search.query && (
            <div className="max-w-2xl mx-auto text-center">
              <Card>
                <CardContent className="p-12">
                  <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    No podcasts found
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Try adjusting your search terms or filters
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setFilterBy('all');
                      setSortBy('relevance');
                    }}
                  >
                    Clear Filters
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
} 