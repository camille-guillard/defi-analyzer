"use client";

import { useState } from "react";

type AnalysisMode = "token" | "wallet";

interface AddressInputProps {
  onSubmit: (address: string, chain: string, mode: AnalysisMode) => void;
  loading: boolean;
}

export default function AddressInput({ onSubmit, loading }: AddressInputProps) {
  const [address, setAddress] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [mode, setMode] = useState<AnalysisMode>("wallet");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim()) {
      onSubmit(address.trim(), chain, mode);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">
        Or enter an address manually
      </h3>

      {/* Mode toggle */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setMode("wallet")}
          className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            mode === "wallet"
              ? "bg-purple-600 text-white"
              : "bg-gray-800 text-gray-400 hover:text-white"
          }`}
        >
          Wallet
        </button>
        <button
          type="button"
          onClick={() => setMode("token")}
          className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            mode === "token"
              ? "bg-purple-600 text-white"
              : "bg-gray-800 text-gray-400 hover:text-white"
          }`}
        >
          Token
        </button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <select
          value={chain}
          onChange={(e) => setChain(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="ethereum">EVM (ETH, Base, Arb, OP, ...)</option>
          <option value="solana">Solana</option>
        </select>
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder={
            mode === "wallet"
              ? "Wallet address..."
              : "Token contract address..."
          }
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500 min-w-0"
        />
        <button
          type="submit"
          disabled={loading || !address.trim()}
          className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
        >
          {loading ? "Analyzing..." : mode === "wallet" ? "Scan Wallet" : "Analyze Token"}
        </button>
      </div>
    </form>
  );
}
