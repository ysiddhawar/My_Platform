import { create } from 'zustand';

type UiState = {
  sidebarOpen: boolean;
  activePage: string;
  setSidebarOpen: (value: boolean) => void;
  setActivePage: (page: string) => void;
};

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  activePage: 'Overview',
  setSidebarOpen: (value) => set({ sidebarOpen: value }),
  setActivePage: (page) => set({ activePage: page })
}));
