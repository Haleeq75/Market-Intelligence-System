// ─── store/agentStore.ts ─────────────────────────────────────────────────────
import { create } from "zustand";
import type { AgentStatus, DecisionStatus, SignalType, WsEvent } from "@/types";

interface AgentStore {
  // Map of ticker → AgentStatus for the live panel
  activeAgents: Record<string, AgentStatus>;
  // Rolling event log for the live feed
  eventLog: Array<{ id: string; ticker: string; message: string; timestamp: number }>;
  // Connection state
  wsConnected: boolean;

  setWsConnected: (v: boolean) => void;
  handleWsEvent: (event: WsEvent) => void;
  clearAgent: (ticker: string) => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  activeAgents: {},
  eventLog: [],
  wsConnected: false,

  setWsConnected: (v) => set({ wsConnected: v }),

  handleWsEvent: (event) =>
    set((state) => {
      const ticker = event.ticker ?? "UNKNOWN";
      const decision_id = event.decision_id ?? "";
      const now = Date.now();

      // Update active agent map
      const activeAgents = { ...state.activeAgents };
      if (event.type === "agent_status" || event.type === "final_signal") {
        const current = activeAgents[ticker];
        const statusMap: Record<string, DecisionStatus> = {
          pending: "pending",
          running_ear: "running_ear",
          running_bull: "running_bull",
          running_bear: "running_bear",
          running_arbiter: "running_arbiter",
          complete: "complete",
        };
        let newStatus: DecisionStatus = current?.status ?? "pending";
        for (const [k, v] of Object.entries(statusMap)) {
          if (event.message.toLowerCase().includes(k.replace("_", " "))) {
            newStatus = v;
          }
        }
        if (event.type === "final_signal") newStatus = "complete";

        activeAgents[ticker] = {
          ticker,
          decision_id,
          status: newStatus,
          last_message: event.message,
          signal: event.data?.signal,
          bull_confidence: event.data?.bull_confidence,
          bear_confidence: event.data?.bear_confidence,
          updated_at: now,
        };
      }

      // Append to event log (keep last 100)
      const eventLog = [
        { id: `${now}-${Math.random()}`, ticker, message: event.message, timestamp: now },
        ...state.eventLog,
      ].slice(0, 100);

      return { activeAgents, eventLog };
    }),

  clearAgent: (ticker) =>
    set((state) => {
      const activeAgents = { ...state.activeAgents };
      delete activeAgents[ticker];
      return { activeAgents };
    }),
}));
