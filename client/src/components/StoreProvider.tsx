'use client';

import React from 'react';
import { useStoreHydration } from '@/hooks/useStoreHydration';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface StoreProviderProps {
  children: React.ReactNode;
}

export function StoreProvider({ children }: StoreProviderProps) {
  const isHydrated = useStoreHydration();

  if (!isHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return <>{children}</>;
} 