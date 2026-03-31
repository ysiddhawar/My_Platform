import type { AppProps } from 'next/app';
import { QueryClient, QueryClientProvider } from 'react-query';
import { useEffect, useState } from 'react';

import '@/styles/globals.css';
import { useThemeStore } from '@/state/themeStore';

function ThemeHydrator() {
  const mode = useThemeStore((state) => state.mode);
  const hydrate = useThemeStore((state) => state.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    document.documentElement.dataset.theme = mode;
    document.documentElement.classList.toggle('dark', mode === 'dark');
  }, [mode]);

  return null;
}

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false, refetchOnReconnect: false, staleTime: 15000 } } }));

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeHydrator />
      <Component {...pageProps} />
    </QueryClientProvider>
  );
}
