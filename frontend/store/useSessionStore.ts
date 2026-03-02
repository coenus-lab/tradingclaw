import { create } from 'zustand';

type SessionState = {
  mode: 'training' | 'mastery';
  sessionStarted: boolean;
  pnlVisible: boolean;
  environment: 'demo' | 'prod';
  setMode: (mode: 'training' | 'mastery') => void;
  toggleSession: (next: boolean) => void;
  revealPnl: () => void;
  setEnvironment: (env: 'demo' | 'prod') => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  mode: 'training',
  sessionStarted: false,
  pnlVisible: false,
  environment: 'demo',
  setMode: (mode) => set({ mode }),
  toggleSession: (next) => set({ sessionStarted: next, pnlVisible: !next ? true : false }),
  revealPnl: () => set({ pnlVisible: true }),
  setEnvironment: (environment) => set({ environment })
}));
