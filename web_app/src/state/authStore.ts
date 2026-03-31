import { create } from 'zustand';

import { getStoredAuthToken, setStoredAuthToken } from '@/api/client';

type AuthMode = 'signup' | 'signin';

type AuthState = {
  mode: AuthMode;
  token: string | null;
  statusMessage: string | null;
  setMode: (mode: AuthMode) => void;
  setToken: (token: string | null) => void;
  setStatusMessage: (message: string | null) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  mode: 'signup',
  token: getStoredAuthToken(),
  statusMessage: null,
  setMode: (mode) => set({ mode }),
  setToken: (token) => {
    setStoredAuthToken(token);
    set({ token });
  },
  setStatusMessage: (statusMessage) => set({ statusMessage })
}));
