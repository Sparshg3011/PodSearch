import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from 'react-hot-toast';
import { StoreProvider } from '@/components/StoreProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  metadataBase: new URL('http://localhost:3000'),
  title: 'PodSearch AI - Search Podcasts Like a Pro',
  description: 'Ask anything, get answers from YouTube podcast episodes with AI-powered search, transcript navigation, and fact-checking.',
  keywords: 'podcast search, AI, YouTube, transcripts, fact-checking, semantic search',
  authors: [{ name: 'PodSearch Team' }],
  creator: 'PodSearch AI',
  publisher: 'PodSearch AI',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://podsearch.ai',
    title: 'PodSearch AI - Search Podcasts Like a Pro',
    description: 'Ask anything, get answers from YouTube podcast episodes with AI-powered search, transcript navigation, and fact-checking.',
    siteName: 'PodSearch AI',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PodSearch AI - Search Podcasts Like a Pro',
    description: 'Ask anything, get answers from YouTube podcast episodes with AI-powered search, transcript navigation, and fact-checking.',
    creator: '@podsearchai',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <StoreProvider>
          {children}
        </StoreProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#fff',
              color: '#333',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
            },
            success: {
              iconTheme: {
                primary: '#10B981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#EF4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </body>
    </html>
  );
} 