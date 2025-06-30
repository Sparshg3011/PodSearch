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
  TrendingUp,
  Mic,
  Brain,
  Shield
} from 'lucide-react';
import toast from 'react-hot-toast';

const popularSearches = [
  'What did Sam Altman say about AI safety?',
  'Joe Rogan on aliens and UAPs',
  'Naval Ravikant on wealth building',
  'Lex Fridman interviews about consciousness',
  'Tim Ferriss productivity tips',
  'Huberman Lab sleep optimization',
  'Y Combinator startup advice',
  'Elon Musk on Mars colonization',
];

const features = [
  {
    icon: Search,
    title: 'AI-Powered Search',
    description: 'Search across podcast transcripts using natural language. Find exactly what you\'re looking for.',
  },
  {
    icon: Brain,
    title: 'Smart Answers',
    description: 'Get AI-generated answers with timestamps and source citations from podcast episodes.',
  },
  {
    icon: Shield,
    title: 'Fact Verification',
    description: 'Automatic fact-checking of claims with trusted sources and confidence scores.',
  },
  {
    icon: Clock,
    title: 'Timestamped Navigation',
    description: 'Jump directly to relevant moments in podcasts with precise timestamp linking.',
  },
];

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

  const handlePopularSearch = (query: string) => {
    setSearchQuery(query);
    handleSearch(query);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(searchQuery);
  };

  return (
    <Layout title="PodSearch AI - Search Podcasts Like a Pro" showSearch={false}>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        {/* Hero Section */}
        <section className="relative px-6 pt-14 pb-16 sm:px-6 lg:px-8 lg:pt-20">
          <div className="mx-auto max-w-4xl text-center">
            <div className="flex justify-center mb-8">
              <div className="flex items-center space-x-2">
                <Headphones className="h-12 w-12 text-primary-600" />
                <span className="text-4xl font-bold gradient-text">PodSearch</span>
              </div>
            </div>
            
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl mb-6">
              Search podcasts like a{' '}
              <span className="gradient-text">pro</span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-lg leading-8 text-gray-600 mb-10">
              Ask anything, get answers from YouTube podcast episodes. 
              AI-powered search with timestamps, transcripts, and fact-checking.
            </p>
          </div>

          {/* Search Box */}
          <div className="mx-auto max-w-2xl mt-10">
            <form onSubmit={handleSubmit} className="relative">
              <Input
                type="text"
                size="xl"
                placeholder="e.g., What did Sam Altman say about AI safety?"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={<Search className="h-5 w-5" />}
                className="pr-32 shadow-lg"
                disabled={isSearching}
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                <Button
                  type="submit"
                  size="lg"
                  disabled={isSearching || !searchQuery.trim()}
                  loading={isSearching}
                  loadingText="Searching..."
                >
                  {!isSearching && <Play className="h-4 w-4 mr-2" />}
                  Search
                </Button>
              </div>
            </form>

            {/* Search Type Toggle */}
            <div className="flex items-center justify-center mt-4 space-x-4">
              <Badge variant="primary" className="cursor-pointer">
                <Headphones className="h-3 w-3 mr-1" />
                Audio Podcasts
              </Badge>
              <Badge variant="outline" className="cursor-pointer">
                <Video className="h-3 w-3 mr-1" />
                YouTube Shows
              </Badge>
              <Badge variant="outline" className="cursor-pointer">
                <Mic className="h-3 w-3 mr-1" />
                All Content
              </Badge>
            </div>
          </div>

          {/* Popular Searches */}
          <div className="mt-12">
            <div className="flex items-center justify-center mb-4">
              <TrendingUp className="h-4 w-4 text-gray-500 mr-2" />
              <span className="text-sm font-medium text-gray-500">Popular Searches</span>
            </div>
            <div className="flex flex-wrap justify-center gap-2 max-w-4xl mx-auto">
              {popularSearches.map((search, index) => (
                <button
                  key={index}
                  onClick={() => handlePopularSearch(search)}
                  className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-white text-gray-700 border border-gray-200 hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700 transition-all duration-200 shadow-sm hover:shadow-md"
                  disabled={isSearching}
                >
                  {search}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16 bg-white/50">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                Why PodSearch?
              </h2>
              <p className="mt-4 text-lg leading-8 text-gray-600">
                Unlock the full potential of podcast content with our AI-powered platform
              </p>
        </div>

            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature, index) => (
                <div
                  key={feature.title}
                >
                  <Card className="text-center h-full hover:shadow-lg transition-shadow duration-300">
                    <CardContent className="p-6">
                      <div className="flex justify-center mb-4">
                        <div className="rounded-lg bg-primary-100 p-3">
                          <feature.icon className="h-6 w-6 text-primary-600" />
                        </div>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {feature.description}
                      </p>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-16">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                How it works
              </h2>
              <p className="mt-4 text-lg leading-8 text-gray-600">
                From search to verified insights in three simple steps
              </p>
            </div>

            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
              {[
                {
                  step: '01',
                  title: 'Search & Discover',
                  description: 'Enter your question or topic. Our AI searches across thousands of podcast episodes to find relevant content.',
                  icon: Search,
                },
                {
                  step: '02',
                  title: 'Get Smart Answers',
                  description: 'Receive AI-generated answers with exact timestamps and source citations from the most relevant podcast segments.',
                  icon: Brain,
                },
                {
                  step: '03',
                  title: 'Verify Facts',
                  description: 'Every claim is automatically fact-checked against trusted sources with confidence scores and detailed explanations.',
                  icon: CheckCircle,
                },
              ].map((step, index) => (
                <div
                  key={step.step}
                  className="relative"
                >
                  <Card className="h-full">
                    <CardContent className="p-8">
                      <div className="flex items-center mb-4">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 text-primary-600 font-bold text-sm mr-4">
                          {step.step}
                        </div>
                        <step.icon className="h-6 w-6 text-primary-600" />
                      </div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-3">
                        {step.title}
                      </h3>
                      <p className="text-gray-600 leading-relaxed">
                        {step.description}
                      </p>
                    </CardContent>
                  </Card>
                  {index < 2 && (
                    <div className="hidden lg:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gray-300 transform -translate-y-1/2 z-10" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-primary-50">
          <div className="mx-auto max-w-4xl text-center px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl mb-4">
                Ready to search smarter?
              </h2>
              <p className="text-lg text-gray-600 mb-8">
                Join thousands of users who are already discovering insights from podcasts
              </p>
              <Button
                size="xl"
                onClick={() => document.querySelector('input')?.focus()}
                className="shadow-lg hover:shadow-xl transition-shadow duration-300"
              >
                <Search className="h-5 w-5 mr-2" />
                Start Searching Now
              </Button>
            </div>
          </div>
        </section>
    </div>
    </Layout>
  );
}