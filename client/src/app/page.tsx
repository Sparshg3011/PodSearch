'use client';

import React, { useState, useCallback } from 'react';

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
  Headphones, 
  Video, 
  Brain
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
    } catch {
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
    <Layout title="PodSearch - Podcast Search">
      <div className="min-h-screen bg-white">
        <section className="px-4 pt-16 pb-12">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-10">
              <div className="flex justify-center items-center mb-8">
                <Headphones className="h-7 w-7 text-blue-600 mr-3" />
                <h1 className="text-3xl font-semibold text-gray-900">PodSearch</h1>
              </div>
            </div>

            <div className="max-w-xl mx-auto">
              <form onSubmit={handleSubmit}>
                <div className="flex gap-3">
                  <input
                    type="text"
                    placeholder="Search podcasts..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-gray-900 placeholder-gray-500"
                    disabled={isSearching}
                  />
                  <button
                    type="submit"
                    disabled={isSearching || !searchQuery.trim()}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                  >
                    {isSearching ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </section>



        <section className="py-16 bg-gray-50">
          <div className="max-w-5xl mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                How it works
              </h2>
              <p className="text-gray-600">
                Three simple steps to get started
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  step: '1',
                  title: 'Search',
                  description: 'Find podcast episodes by searching for topics or questions.',
                  icon: Search
                },
                {
                  step: '2',
                  title: 'Import',
                  description: 'Import episodes to your workspace to analyze transcripts.',
                  icon: Video
                },
                {
                  step: '3',
                  title: 'Chat',
                  description: 'Ask questions and get answers with timestamps.',
                  icon: Brain
                },
              ].map((step) => (
                <div key={step.step} className="bg-white p-6 rounded-lg border border-gray-200">
                  <div className="flex items-center mb-4">
                    <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium mr-3">
                      {step.step}
                    </div>
                    <step.icon className="h-5 w-5 text-gray-500" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {step.title}
                  </h3>
                  <p className="text-gray-600 text-sm">
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