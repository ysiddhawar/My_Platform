import { useMemo } from 'react';
import { useRouter } from 'next/router';

const pageTitles: Record<string, string> = {
  '/': 'Overview Dashboard',
  '/journal': 'Trade Journal',
  '/performance': 'Performance Analytics',
  '/discipline': 'Setup & Discipline',
  '/risk': 'Risk Analytics',
  '/portfolio': 'Portfolio Analytics',
  '/ai': 'AI Diagnostics'
};

export function Topbar() {
  const router = useRouter();

  const title = useMemo(() => pageTitles[router.pathname] || 'Dashboard', [router.pathname]);

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-800/60 bg-[#0b141d]/85 px-4 text-slate-100 backdrop-blur-xl md:px-6">
      <div>
        <h2 className="font-display text-xl font-semibold text-white">{title}</h2>
        <p className="text-xs text-slate-400">Live trading analytics workspace</p>
      </div>

      <div className="flex items-center gap-3">
        <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(74,222,128,0.8)]" />
        <span className="text-sm text-slate-300">Backend Connected</span>
      </div>
    </header>
  );
}
