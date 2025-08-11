'use client';

import React, { useEffect, useState } from 'react';

export const dynamic = 'force-dynamic';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { PageLoading } from '@/components/ui/LoadingSpinner';
import { useSearchState, useSearchActions, useWorkspaceActions } from '@/store/useStore';
import { youtubeApi, utils } from '@/lib/api';
import { 
  Search, 
  Play, 
  Eye, 
  Calendar,
  Import,
  Filter,
  SortAsc,
  Video,
  User
} from 'lucide-react';
import toast from 'react-hot-toast';

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
    } catch {
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
      router.push(`/workspace/${video.id}`);
      toast.success(`Imported "${utils.truncateText(video.title, 50)}" to workspace`);
    } catch {
      toast.error('Failed to import video');
    } finally {
      setImporting(null);
    }
  };

  const getFilteredAndSortedResults = () => {
    let filtered = [...search.results];

    if (filterBy !== 'all') {
      filtered = filtered.filter(video => {
        const duration = video.duration || 0;
        switch (filterBy) {
          case 'short':
            return duration < 600;
          case 'medium':
            return duration >= 600 && duration < 1800;
          case 'long':
            return duration >= 1800;
          default:
            return true;
        }
      });
    }

    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'upload_date':
          return new Date(b.upload_date || 0).getTime() - new Date(a.upload_date || 0).getTime();
        case 'view_count':
          return (b.view_count || 0) - (a.view_count || 0);
        case 'duration':
          return (b.duration || 0) - (a.duration || 0);
        default:
          return 0;
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
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="mb-8">
            <form onSubmit={handleSubmit} className="max-w-2xl mx-auto mb-6">
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Search podcasts..."
                  value={newQuery}
                  onChange={(e) => setNewQuery(e.target.value)}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-gray-900 placeholder-gray-500"
                  disabled={search.loading}
                />
                <button
                  type="submit"
                  disabled={search.loading}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                >
                  {search.loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </form>

            <div className="mb-6">
              <h1 className="text-2xl font-semibold text-gray-900 mb-2">
                Results for "{search.query}"
              </h1>
              <p className="text-gray-600">
                {filteredResults.length} podcast{filteredResults.length !== 1 ? 's' : ''} found
              </p>
            </div>

            <div className="flex items-center justify-between mb-6 p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Filter className="h-4 w-4 text-gray-500" />
                  <select
                    value={filterBy}
                    onChange={(e) => setFilterBy(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-1 text-sm"
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
                    className="border border-gray-300 rounded px-3 py-1 text-sm"
                  >
                    {sortOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

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

          {filteredResults.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredResults.map((video) => (
                <div key={video.id}>
                  <Card className="h-full hover:shadow-lg transition-shadow duration-200 bg-white rounded-lg overflow-hidden border border-gray-200">
                    <CardContent className="p-0">
                      <div className="relative aspect-video bg-gray-100 overflow-hidden">
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
                          <Badge variant="default" className="bg-black/80 text-white text-xs px-2 py-1">
                            {video.duration ? utils.formatDuration(video.duration) : 'N/A'}
                          </Badge>
                        </div>
                      </div>

                      <div className="p-4">
                        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 leading-snug">
                          {video.title}
                        </h3>
                        
                        <div className="flex items-center text-sm text-gray-600 mb-3">
                          <User className="h-4 w-4 mr-2" />
                          <span className="truncate">{video.uploader || 'Unknown'}</span>
                        </div>

                        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                          <div className="flex items-center">
                            <Eye className="h-4 w-4 mr-1" />
                            <span>{video.view_count ? video.view_count.toLocaleString() : 'N/A'} views</span>
                          </div>
                          <span>{video.upload_date || 'N/A'}</span>
                        </div>

                        {video.description && (
                          <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                            {utils.truncateText(video.description, 100)}
                          </p>
                        )}

                        <div className="flex gap-2">
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
                            className="flex-1 bg-blue-600 hover:bg-blue-700"
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