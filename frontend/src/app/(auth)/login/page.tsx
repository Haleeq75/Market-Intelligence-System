"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, getMe } from "@/lib/api";
import { useAuthStore } from "@/store/signalStore";
import { cn } from "@/lib/utils";
import { Zap, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = await login(email, password);
      // Store tokens first so getMe() can use them
      localStorage.setItem(
        "swarm-auth",
        JSON.stringify({ state: { tokens, user: null, isAuthenticated: true } })
      );
      const user = await getMe();
      setAuth(user, tokens);
      router.replace("/dashboard");
    } catch {
      setError("Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      {/* Background grid */}
      <div
        className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: "linear-gradient(hsl(238 68% 65% / 1) 1px, transparent 1px), linear-gradient(90deg, hsl(238 68% 65% / 1) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="w-full max-w-sm relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-cyber/20 border border-cyber/40 flex items-center justify-center">
              <span className="text-cyber font-black font-mono">AS</span>
            </div>
            <div className="text-left">
              <p className="text-[10px] font-semibold tracking-widest text-muted-foreground uppercase">
                Adversarial
              </p>
              <p className="text-lg font-bold leading-none">Swarm</p>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">Market Intelligence System</p>
        </div>

        {/* Card */}
        <div className="glass-card p-6">
          <h1 className="text-base font-semibold mb-5">Sign in to your account</h1>

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-muted-foreground">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-surface-0 border border-border rounded-md px-3 py-2.5 text-sm outline-none focus:border-cyber/50 transition-colors"
                placeholder="you@example.com"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-muted-foreground">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-surface-0 border border-border rounded-md px-3 py-2.5 text-sm outline-none focus:border-cyber/50 transition-colors pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-muted-foreground"
                >
                  {showPw ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-xs text-bear">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className={cn(
                "w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium transition-all",
                "bg-cyber/15 border border-cyber/30 text-cyber hover:bg-cyber/25",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              <Zap className={cn("w-4 h-4", loading && "animate-pulse")} />
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-muted-foreground/40 mt-4">
          Adversarial Swarm v1.0 · Multi-Agent Market Intelligence
        </p>
      </div>
    </div>
  );
}
