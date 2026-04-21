"use client";
import { useState, useEffect } from "react";
import { getAssets, addAsset, deleteAsset } from "@/lib/api";
import { AssetBadge } from "@/components/shared";
import { cn } from "@/lib/utils";
import { Plus, Trash2, Settings2 } from "lucide-react";
import type { Asset } from "@/types";

export default function SettingsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [ticker, setTicker] = useState("");
  const [assetClass, setAssetClass] = useState("equity");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);

  const fetchAssets = async () => {
    try {
      const data = await getAssets();
      setAssets(data);
    } catch {}
    setFetching(false);
  };

  useEffect(() => { fetchAssets(); }, []);

  const handleAdd = async () => {
    if (!ticker.trim()) return;
    setLoading(true);
    try {
      await addAsset(ticker.toUpperCase(), undefined, assetClass);
      setTicker("");
      await fetchAssets();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteAsset(id);
      setAssets((prev) => prev.filter((a) => a.id !== id));
    } catch {}
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h1 className="text-xl font-semibold">Watchlist</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Manage the assets the swarm can analyse
        </p>
      </div>

      {/* Add asset */}
      <div className="glass-card p-5">
        <h2 className="text-sm font-medium mb-4 flex items-center gap-2">
          <Plus className="w-4 h-4 text-cyber" />
          Add Asset
        </h2>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="TSLA"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            className="flex-1 bg-surface-0 border border-border rounded-md px-3 py-2 text-sm font-mono outline-none focus:border-cyber/50 transition-colors"
          />
          <select
            value={assetClass}
            onChange={(e) => setAssetClass(e.target.value)}
            className="bg-surface-0 border border-border rounded-md px-3 py-2 text-sm outline-none focus:border-cyber/50 transition-colors text-muted-foreground"
          >
            {["equity", "crypto", "forex", "commodity"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <button
            onClick={handleAdd}
            disabled={!ticker.trim() || loading}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium transition-all",
              "bg-cyber/10 border border-cyber/30 text-cyber hover:bg-cyber/20",
              "disabled:opacity-40 disabled:cursor-not-allowed"
            )}
          >
            {loading ? "Adding…" : "Add"}
          </button>
        </div>
      </div>

      {/* Asset list */}
      <div className="glass-card overflow-hidden">
        <div className="px-5 py-3 border-b border-border flex items-center gap-2">
          <Settings2 className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Watchlist ({assets.length})
          </span>
        </div>

        {fetching ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading…</div>
        ) : assets.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">No assets yet</div>
        ) : (
          <div className="divide-y divide-border">
            {assets.map((asset) => (
              <div
                key={asset.id}
                className="flex items-center justify-between px-5 py-3 hover:bg-surface-2/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <AssetBadge ticker={asset.ticker} />
                  {asset.name && (
                    <span className="text-sm text-muted-foreground">{asset.name}</span>
                  )}
                  <span className="text-[10px] font-mono text-muted-foreground/50 border border-border rounded px-1.5 py-0.5">
                    {asset.asset_class}
                  </span>
                </div>
                <button
                  onClick={() => handleDelete(asset.id)}
                  className="p-1.5 rounded text-muted-foreground/40 hover:text-bear hover:bg-bear-bg transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
