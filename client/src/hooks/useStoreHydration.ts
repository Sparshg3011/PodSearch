'use client';

import { useEffect, useState } from 'react';
import { useStore } from '@/store/useStore';

export function useStoreHydration() {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {

    const unsubHydrate = useStore.persist.onHydrate(() => setIsHydrated(false));
    const unsubFinishHydration = useStore.persist.onFinishHydration(() => setIsHydrated(true));

    useStore.persist.rehydrate();

    return () => {
      unsubHydrate?.();
      unsubFinishHydration?.();
    };
  }, []);

  return isHydrated;
} 