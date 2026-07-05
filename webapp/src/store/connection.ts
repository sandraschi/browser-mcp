import { create } from 'zustand';

interface ConnectionState {
  state: 'connected' | 'connecting' | 'offline' | 'error';
  lastError: string | null;
  setState: (s: ConnectionState['state']) => void;
  setError: (e: string) => void;
}

export const useConnection = create<ConnectionState>((set) => ({
  state: 'connecting',
  lastError: null,
  setState: (state) => set({ state, lastError: state === 'connected' ? null : undefined }),
  setError: (lastError) => set({ state: 'error', lastError }),
}));
