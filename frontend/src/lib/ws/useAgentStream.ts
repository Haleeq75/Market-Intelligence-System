"use client";
import { useEffect, useRef } from "react";
import { useAgentStore } from "@/store/agentStore";
import { useAuthStore } from "@/store/signalStore";
import type { WsEvent } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export function useAgentStream() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const { handleWsEvent, setWsConnected } = useAgentStore();

  // Pull token from auth store (localStorage-backed)
  const getToken = () => {
    try {
      const raw = localStorage.getItem("swarm-auth");
      if (!raw) return null;
      return JSON.parse(raw)?.state?.tokens?.access_token ?? null;
    } catch {
      return null;
    }
  };

  const connect = () => {
    const token = getToken();
    if (!token) return;

    const ws = new WebSocket(`${WS_URL}/ws/live?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      console.info("[WS] Connected to Adversarial Swarm live feed");
      // Start keepalive ping every 25s
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send("ping");
      }, 25_000);
      ws.onclose = () => {
        clearInterval(pingInterval);
        setWsConnected(false);
        scheduleReconnect();
      };
    };

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as WsEvent;
        if (event.type !== "connected") {
          handleWsEvent(event);
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  };

  const scheduleReconnect = () => {
    clearTimeout(reconnectTimer.current);
    reconnectTimer.current = setTimeout(connect, 3_000);
  };

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, []);
}
