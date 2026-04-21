"use client";
import { useAgentStream } from "@/lib/ws/useAgentStream";

export function WsProvider({ children }: { children: React.ReactNode }) {
  useAgentStream();
  return <>{children}</>;
}
