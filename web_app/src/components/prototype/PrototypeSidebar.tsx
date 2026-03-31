import { BrandMark } from '@/components/foundation/BrandMark';
import type { PrototypeView } from '@/types/prototype';

const items: Array<{ key: PrototypeView; label: string; hint: string }> = [
  { key: 'dashboard', label: 'Dashboard', hint: 'Metrics, visuals, and system state' },
  { key: 'journal', label: 'Journal', hint: 'Executed trade records' },
  { key: 'trade-detail', label: 'Trade Detail', hint: 'Full trade breakdown' },
  { key: 'ai-insights', label: 'AI Insights', hint: 'Insight layer' },
  { key: 'missed-opportunities', label: 'Missed Opportunities', hint: 'Unexecuted setups' },
  { key: 'calendar', label: 'Calendar', hint: 'Daily result and platform time' },
  { key: 'position-sizer', label: 'Position Sizer', hint: 'Planning and discipline' },
  { key: 'demo-data', label: 'Data', hint: 'Seed and import' },
];

type PrototypeSidebarProps = {
  activeView: PrototypeView;
  order: PrototypeView[];
  collapsed: boolean;
  onSelect: (view: PrototypeView) => void;
  onReorder: (order: PrototypeView[]) => void;
  onReset: () => void;
  onToggleCollapse: () => void;
};

export function PrototypeSidebar({
  activeView,
  order,
  collapsed,
  onSelect,
  onReorder,
  onReset,
  onToggleCollapse,
}: PrototypeSidebarProps) {
  const orderedItems = order.map((key) => items.find((item) => item.key === key)).filter(Boolean) as typeof items;

  return (
    <aside
      className={`relative z-40 flex h-screen shrink-0 flex-col overflow-x-visible overflow-y-auto border-r border-black/10 bg-white px-3 py-5 transition-[width] duration-200 dark:border-white/10 dark:bg-[#050505] ${
        collapsed ? 'w-[108px]' : 'w-[298px]'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className={collapsed ? 'scale-95' : ''}>
          <BrandMark compact={collapsed} />
        </div>
        <button
          type="button"
          onClick={onToggleCollapse}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-black/10 bg-white text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <SidebarCollapseGlyph collapsed={collapsed} />
        </button>
      </div>

      {!collapsed ? (
        <div className="mt-7 flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-black/55 dark:text-white/55">Sidebar Layout</p>
          <button
            type="button"
            onClick={onReset}
            className="rounded-full border border-black/10 px-3 py-1.5 text-[11px] font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
          >
            Reset
          </button>
        </div>
      ) : null}

      <nav className="mt-8 space-y-2">
        {orderedItems.map((item, index) => {
          const isActive = item.key === activeView;

          if (collapsed) {
            return (
              <div key={item.key} className="group relative overflow-visible">
                <button
                  type="button"
                  draggable={false}
                  onClick={() => onSelect(item.key)}
                  title={item.label}
                  className={`relative w-full rounded-[20px] border px-0 py-3 text-center transition ${
                    isActive
                      ? 'border-black bg-black text-white dark:border-[#ff5900] dark:bg-[#111111]'
                      : 'border-black/10 bg-white text-black hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0a0a0a] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]'
                  }`}
                >
                  <div className="flex justify-center">
                    <SidebarItemIcon view={item.key} />
                  </div>
                </button>
                <div className="pointer-events-none absolute left-full top-1/2 z-[160] ml-3 -translate-y-1/2 whitespace-nowrap rounded-full bg-[#ff5900] px-3 py-1.5 text-[14px] font-semibold text-white opacity-0 shadow-[0_12px_28px_rgba(255,89,0,0.24)] transition-opacity duration-75 group-hover:opacity-100 group-focus-within:opacity-100">
                  {item.label}
                </div>
              </div>
            );
          }

          return (
            <button
              key={item.key}
              type="button"
              draggable
              onDragStart={(event) => {
                event.dataTransfer.setData('text/sidebar-index', String(index));
              }}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                const sourceIndex = Number(event.dataTransfer.getData('text/sidebar-index'));
                if (!Number.isFinite(sourceIndex) || sourceIndex === index) return;
                const next = [...order];
                const [moved] = next.splice(sourceIndex, 1);
                next.splice(index, 0, moved);
                onReorder(next);
              }}
              onClick={() => onSelect(item.key)}
              className={`w-full rounded-[20px] border px-4 py-4 text-left transition ${
                isActive
                  ? 'border-black bg-black text-white dark:border-[#ff5900] dark:bg-[#111111]'
                  : 'border-black/10 bg-white text-black hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0a0a0a] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]'
              }`}
            >
              <div className="flex items-center gap-3">
                <SidebarItemIcon view={item.key} />
                <div className="text-sm font-semibold">{item.label}</div>
              </div>
              <div className={`mt-1 text-xs ${isActive ? 'text-white/75' : 'text-black/65 dark:text-white/65'}`}>
                {item.hint}
              </div>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

function SidebarItemIcon({ view }: { view: PrototypeView }) {
  const common = 'h-[18px] w-[18px]';
  switch (view) {
    case 'dashboard':
      return <svg viewBox="0 0 24 24" className={common} fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 13h6V4H4zM14 20h6v-9h-6zM14 10h6V4h-6zM4 20h6v-3H4z" /></svg>;
    case 'journal':
      return <svg viewBox="0 0 24 24" className={common} fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M6 4h11a3 3 0 0 1 3 3v13H9a3 3 0 0 0-3 3z" /><path d="M6 4a3 3 0 0 0-3 3v13h3" /><path d="M9 9h7M9 13h7" /></svg>;
    case 'trade-detail':
      return <svg viewBox="0 0 24 24" className={common} fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M6 4h12v16H6z" /><path d="M9 8h6M9 12h6M9 16h3" /></svg>;
    case 'ai-insights':
      return <svg viewBox="0 0 24 24" className={common} fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 3a7 7 0 0 0-4 12.7V19a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3.3A7 7 0 0 0 12 3Z" /><path d="M10 22h4" /></svg>;
    case 'missed-opportunities':
      return <svg viewBox="0 0 24 24" className={common} fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="11" cy="11" r="6" /><path d="m20 20-4-4" /><path d="M11 8v3l2 2" /></svg>;
    case 'calendar':
      return <svg viewBox="0 0 24 24" className={common} fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M6 3v4M18 3v4M4 9h16" /><rect x="4" y="5" width="16" height="15" rx="2" /></svg>;
    case 'position-sizer':
      return <svg viewBox="0 0 24 24" className={common} fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M5 5h14v14H5z" /><path d="M9 9h6M9 12h6M9 15h3" /></svg>;
    case 'demo-data':
      return <svg viewBox="0 0 24 24" className={common} fill="none" stroke="currentColor" strokeWidth="1.8"><ellipse cx="12" cy="6" rx="7" ry="3" /><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" /><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" /></svg>;
  }
}

function SidebarCollapseGlyph({ collapsed }: { collapsed: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 6h5" />
      <path d="M6 12h13" />
      <path d="M14 18h5" />
      <path d={collapsed ? 'M9 8l4 4-4 4' : 'M10 8l-4 4 4 4'} />
    </svg>
  );
}
