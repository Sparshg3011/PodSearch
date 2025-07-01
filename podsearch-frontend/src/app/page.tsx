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
                placeholder="Search podcasts..."
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


        </section>



        {/* How It Works */}
        <section className="py-20 bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 relative overflow-hidden">
          {/* Background decoration */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-100/20 via-transparent to-purple-100/20"></div>
          <div className="absolute top-10 left-10 w-32 h-32 bg-blue-200/30 rounded-full blur-xl"></div>
          <div className="absolute bottom-10 right-10 w-40 h-40 bg-purple-200/30 rounded-full blur-xl"></div>
          
          <div className="relative mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center mb-20">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl mb-6 shadow-lg">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl mb-6">
                How it works
              </h2>
              <p className="text-xl leading-8 text-gray-600">
                From search to verified insights in three simple steps
              </p>
            </div>

            <div className="grid grid-cols-1 gap-8 lg:gap-12 lg:grid-cols-3">
              {[
                {
                  step: '01',
                  title: 'Search & Discover',
                  description: 'Enter your question or topic. Our AI searches across thousands of podcast episodes to find relevant content.',
                  icon: Search,
                  gradient: 'from-blue-500 to-cyan-500',
                  bgGradient: 'from-blue-50 to-cyan-50',
                },
                {
                  step: '02',
                  title: 'Get Smart Answers',
                  description: 'Receive AI-generated answers with exact timestamps and source citations from the most relevant podcast segments.',
                  icon: Brain,
                  gradient: 'from-purple-500 to-pink-500',
                  bgGradient: 'from-purple-50 to-pink-50',
                },
                {
                  step: '03',
                  title: 'Verify Facts',
                  description: 'Every claim is automatically fact-checked against trusted sources with confidence scores and detailed explanations.',
                  icon: CheckCircle,
                  gradient: 'from-green-500 to-emerald-500',
                  bgGradient: 'from-green-50 to-emerald-50',
                },
              ].map((step, index) => (
                <div
                  key={step.step}
                  className="relative group"
                >
                  {/* Connecting line */}
                  {index < 2 && (
                    <div className="hidden lg:block absolute top-20 -right-6 xl:-right-8 w-12 xl:w-16 z-10">
                      <div className="flex items-center">
                        <div className="flex-1 h-0.5 bg-gradient-to-r from-gray-300 to-gray-200"></div>
                        <div className="w-2 h-2 bg-primary-400 rounded-full ml-2"></div>
                      </div>
                    </div>
                  )}
                  
                  <Card className="h-full border-0 shadow-xl group-hover:shadow-2xl transition-all duration-500 group-hover:-translate-y-2 bg-white/80 backdrop-blur-sm">
                    <CardContent className="p-8 relative overflow-hidden">
                      {/* Background gradient */}
                      <div className={`absolute inset-0 bg-gradient-to-br ${step.bgGradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}></div>
                      
                      {/* Step number */}
                      <div className="relative mb-6">
                        <div className={`inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br ${step.gradient} rounded-2xl shadow-lg transform group-hover:scale-110 transition-transform duration-300`}>
                          <span className="text-2xl font-bold text-white">{step.step}</span>
                        </div>
                      </div>
                      
                      {/* Icon */}
                      <div className="relative mb-6">
                        <div className={`inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br ${step.gradient} rounded-xl shadow-md transform group-hover:rotate-6 transition-all duration-300`}>
                          <step.icon className="h-6 w-6 text-white" />
                        </div>
                      </div>
                      
                      {/* Content */}
                      <div className="relative">
                        <h3 className="text-2xl font-bold text-gray-900 mb-4 group-hover:text-gray-800 transition-colors">
                          {step.title}
                        </h3>
                        <p className="text-gray-600 leading-relaxed text-lg group-hover:text-gray-700 transition-colors">
                          {step.description}
                        </p>
                      </div>
                      
                      {/* Decorative elements */}
                      <div className="absolute -top-4 -right-4 w-20 h-20 bg-gradient-to-br from-white/50 to-transparent rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                      <div className="absolute -bottom-4 -left-4 w-16 h-16 bg-gradient-to-br from-transparent to-white/30 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                    </CardContent>
                  </Card>
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