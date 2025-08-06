'use client';

import React, { useState, useCallback } from 'react';

// Force dynamic rendering to avoid NextRouter mounting issues during build
export const dynamic = 'force-dynamic';
import { useRouter } from 'next/navigation';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useSearchActions } from '@/store/useStore';
import { youtubeApi } from '@/lib/api';
import { 
  Search, 
  Play, 
  Headphones, 
  Video, 
  CheckCircle, 
  Clock,
  Mic,
  Brain,
  Shield
} from 'lucide-react';
import toast from 'react-hot-toast';





export default function HomePage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const { setSearchQuery: setStoreQuery, setSearchResults, setSearchLoading } = useSearchActions();

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setIsSearching(true);
    setSearchLoading(true);
    setStoreQuery(query);

    try {
      const results = await youtubeApi.searchVideos(query, 10);
      setSearchResults(results.results);
      router.push('/search');
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Failed to search. Please try again.');
    } finally {
      setIsSearching(false);
      setSearchLoading(false);
    }
  }, [router, setStoreQuery, setSearchResults, setSearchLoading]);



  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(searchQuery);
  };

  return (
    <Layout title="PodSearch - Podcast Search" showSearch={false}>
      <div className="min-h-screen bg-gray-50">
        {/* Hero Section */}
        <section className="px-6 pt-16 pb-12">
          <div className="max-w-4xl mx-auto text-center">
            <div className="flex justify-center items-center mb-8">
              <Headphones className="h-8 w-8 text-blue-600 mr-2" />
              <h1 className="text-3xl font-bold text-gray-900">PodSearch</h1>
            </div>
            
            <h2 className="text-2xl font-medium text-gray-800 mb-4">
              Search podcast episodes
            </h2>
            
            <p className="max-w-2xl mx-auto text-gray-600 mb-8">
              Find answers from YouTube podcast episodes with timestamps and transcripts.
            </p>
          </div>

          {/* Search Box */}
          <div className="max-w-lg mx-auto">
            <form onSubmit={handleSubmit} className="flex">
              <input
                type="text"
                placeholder="Search podcasts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
                disabled={isSearching}
              />
              <button
                type="submit"
                disabled={isSearching || !searchQuery.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-r-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </form>
          </div>


        </section>



        {/* How It Works */}
        <section className="py-16 bg-white">
          <div className="max-w-4xl mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                How it works
              </h2>
              <p className="text-gray-600">
                Search, get answers, and verify facts in three steps
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  step: '1',
                  title: 'Search',
                  description: 'Enter your question and we search podcast episodes for relevant content.',
                  icon: Search
                },
                {
                  step: '2',
                  title: 'Get Answers',
                  description: 'Get AI-generated answers with timestamps and source citations.',
                  icon: Brain
                },
                {
                  step: '3',
                  title: 'Verify Facts',
                  description: 'Claims are fact-checked against trusted sources with confidence scores.',
                  icon: CheckCircle
                },
              ].map((step) => (
                <div key={step.step} className="border border-gray-200 rounded-lg p-6 bg-white">
                  <div className="flex items-center mb-4">
                    <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium mr-3">
                      {step.step}
                    </div>
                    <step.icon className="h-5 w-5 text-gray-600" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {step.title}
                  </h3>
                  <p className="text-gray-600">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>

          </div>
        </section>


    </div>
    </Layout>
  );
}