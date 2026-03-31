import Link from 'next/link';
import { useRouter } from 'next/router';

const links = [
  { href: '/', label: 'Overview' },
  { href: '/journal', label: 'Journal' },
  { href: '/performance', label: 'Performance' },
  { href: '/discipline', label: 'Discipline' },
  { href: '/risk', label: 'Risk' },
  { href: '/portfolio', label: 'Portfolio' },
  { href: '/ai', label: 'AI Insights' }
];

export function Sidebar() {
  const router = useRouter();

  return (
    <aside className="hidden w-72 shrink-0 flex-col border-r border-slate-800/60 bg-[#071019]/90 p-4 text-slate-200 backdrop-blur-xl lg:flex">
      <div className="mb-8 rounded-2xl border border-teal-900/60 bg-gradient-to-br from-[#0f1720] to-[#10282b] p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-teal-300">Trading Intelligence</p>
        <h1 className="font-display text-xl font-semibold">My Platform</h1>
        <p className="mt-2 text-sm text-slate-400">Terminal-grade analytics workspace</p>
      </div>

      <nav className="space-y-1">
        {links.map((link) => {
          const isActive = router.pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`block rounded-lg px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? 'bg-accent text-white shadow-lg shadow-teal-950/40'
                  : 'text-slate-300 hover:bg-slate-900 hover:text-white'
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-950/70 p-3">
        <p className="text-xs uppercase tracking-[0.16em] text-slate-500">API Base</p>
        <p className="truncate text-sm font-medium text-slate-200">
          {process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'}
        </p>
      </div>
    </aside>
  );
}
