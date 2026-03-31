import { useThemeStore } from '@/state/themeStore';

export function ThemeToggle() {
  const mode = useThemeStore((state) => state.mode);
  const toggle = useThemeStore((state) => state.toggle);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle theme"
      className="inline-flex h-[26px] items-center gap-2 rounded-[12px] border border-[#ff5900] bg-[#ff5900] px-2.5 text-sm font-semibold leading-none text-white shadow-[0_12px_28px_rgba(255,89,0,0.18)] transition hover:-translate-y-[1px]"
    >
      <span className="relative flex h-4 w-9 items-center rounded-full border border-black/10 bg-white px-1 dark:border-white/10">
        <span
          className={`absolute h-2.5 w-2.5 rounded-full bg-black shadow-[0_6px_16px_rgba(15,23,42,0.18)] transition-transform dark:bg-black ${
            mode === 'dark' ? 'translate-x-4.5' : 'translate-x-0'
          }`}
        />
      </span>
      <span>{mode === 'dark' ? 'Dark' : 'Light'}</span>
    </button>
  );
}
