// ─── store/authStore.ts ──────────────────────────────────────────────────────
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, AuthTokens } from "@/types";

interface AuthStore {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  setAuth: (user: User, tokens: AuthTokens) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      setAuth: (user, tokens) => set({ user, tokens, isAuthenticated: true }),
      clearAuth: () => set({ user: null, tokens: null, isAuthenticated: false }),
    }),
    { name: "swarm-auth" }
  )
);

// ─── store/signalStore.ts ────────────────────────────────────────────────────
import { create as createSignal } from "zustand";
import type { TradingSignal, DecisionSummary } from "@/types";

interface SignalStore {
  // Latest signal per ticker
  latestSignals: Record<string, TradingSignal>;
  // Recent journal entries for the dashboard preview
  recentDecisions: DecisionSummary[];

  setLatestSignal: (signal: TradingSignal) => void;
  setRecentDecisions: (decisions: DecisionSummary[]) => void;
  prependDecision: (decision: DecisionSummary) => void;
}

export const useSignalStore = createSignal<SignalStore>((set) => ({
  latestSignals: {},
  recentDecisions: [],

  setLatestSignal: (signal) =>
    set((s) => ({
      latestSignals: { ...s.latestSignals, [signal.ticker]: signal },
    })),

  setRecentDecisions: (decisions) => set({ recentDecisions: decisions }),

  prependDecision: (decision) =>
    set((s) => ({
      recentDecisions: [decision, ...s.recentDecisions].slice(0, 20),
    })),
}));
