import { create } from 'zustand';

type ThemeMode = 'light' | 'dark';

const STORAGE_KEY = 'my_platform_theme_mode';

const readStoredTheme = (): ThemeMode => {
  if (typeof window === 'undefined') {
    return 'light';
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === 'dark' ? 'dark' : 'light';
};

type ThemeState = {
  mode: ThemeMode;
  hydrated: boolean;
  hydrate: () => void;
  toggle: () => void;
  setMode: (mode: ThemeMode) => void;
};

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: 'light',
  hydrated: false,
  hydrate: () => {
    const mode = readStoredTheme();
    set({ mode, hydrated: true });
  },
  toggle: () => {
    const next = get().mode === 'light' ? 'dark' : 'light';
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, next);
    }
    set({ mode: next, hydrated: true });
  },
  setMode: (mode) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, mode);
    }
    set({ mode, hydrated: true });
  }
}));
