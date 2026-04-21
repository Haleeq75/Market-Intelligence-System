// ─── Signal & Decision types ────────────────────────────────────────────────

export type SignalType = "BUY" | "HOLD" | "SELL";
export type ConfidenceLabel = "HIGH" | "MEDIUM" | "LOW";
export type DecisionStatus =
  | "pending"
  | "running_ear"
  | "running_bull"
  | "running_bear"
  | "running_arbiter"
  | "complete"
  | "error";

export interface TradingSignal {
  id: string;
  ticker: string;
  signal: SignalType;
  bull_confidence: number;
  bear_confidence: number;
  net_confidence: number;
  price_at_signal: number | null;
  currency: string;
  created_at: string;
}

export interface SourceCitation {
  title: string;
  source: string;
  url?: string;
  relevance?: string;
  sentiment?: number;
}

export interface DecisionSummary {
  id: string;
  ticker: string;
  status: DecisionStatus;
  signal: SignalType | null;
  bull_confidence: number | null;
  bear_confidence: number | null;
  net_confidence: number | null;
  confidence_label: ConfidenceLabel | null;
  created_at: string;
  completed_at: string | null;
}

export interface DecisionDetail extends DecisionSummary {
  error_message: string | null;
  bull_thesis: string;
  bear_thesis: string;
  arbiter_reasoning: string;
  bull_sources: SourceCitation[];
  bear_sources: SourceCitation[];
  market_context: Record<string, unknown>;
  price_at_signal: number | null;
}

// ─── Agent / WebSocket event types ──────────────────────────────────────────

export type WsEventType = "connected" | "agent_status" | "final_signal" | "pipeline_error";

export interface WsEvent {
  type: WsEventType;
  decision_id?: string;
  ticker?: string;
  message: string;
  data?: {
    signal?: SignalType;
    bull_confidence?: number;
    bear_confidence?: number;
    net_confidence?: number;
    confidence_label?: ConfidenceLabel;
    decision_id?: string;
    status?: string;
  };
}

export interface AgentStatus {
  ticker: string;
  decision_id: string;
  status: DecisionStatus;
  last_message: string;
  signal?: SignalType;
  bull_confidence?: number;
  bear_confidence?: number;
  updated_at: number; // timestamp
}

// ─── Asset types ─────────────────────────────────────────────────────────────

export interface Asset {
  id: string;
  ticker: string;
  name: string | null;
  asset_class: string;
  created_at: string;
}

// ─── Auth types ───────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ─── API response types ───────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AnalysisStartedResponse {
  decision_id: string;
  ticker: string;
  status: string;
  message: string;
}
