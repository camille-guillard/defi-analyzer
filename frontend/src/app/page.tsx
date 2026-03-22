"use client";

import { useState } from "react";
import WalletProviders from "@/components/WalletProviders";
import WalletConnect from "@/components/WalletConnect";
import AddressInput from "@/components/AddressInput";
import TokenDashboard from "@/components/TokenDashboard";
import WalletDashboard from "@/components/WalletDashboard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type AnalysisMode = "token" | "wallet";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const [mode, setMode] = useState<AnalysisMode | null>(null);

  const handleAnalyze = async (
    address: string,
    chain: string,
    analysisMode: AnalysisMode
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setMode(analysisMode);

    const endpoint =
      analysisMode === "wallet"
        ? `${API_URL}/api/wallet/${chain}/${address}`
        : `${API_URL}/api/analyze/${chain}/${address}`;

    try {
      const res = await fetch(endpoint);
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `Error ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <WalletProviders>
      <div className="min-h-screen bg-gray-950 text-white">
        {/* Header */}
        <header className="border-b border-gray-800 px-6 py-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              DeFi Analyzer
            </h1>
            <span className="text-sm text-gray-500">
              Solana &middot; Ethereum
            </span>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
          {/* Wallet connection - always analyzes wallet */}
          <WalletConnect
            onAddressDetected={(addr, chain) =>
              handleAnalyze(addr, chain, "wallet")
            }
          />

          {/* Manual input - can choose token or wallet */}
          <AddressInput
            onSubmit={handleAnalyze}
            loading={loading}
          />

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent" />
              <span className="ml-3 text-gray-400">
                {mode === "wallet"
                  ? "Scanning wallet..."
                  : "Analyzing token..."}
              </span>
            </div>
          )}

          {/* Results */}
          {result && mode === "wallet" && <WalletDashboard data={result} />}
          {result && mode === "token" && <TokenDashboard data={result} />}
        </main>
      </div>
    </WalletProviders>
  );
}
