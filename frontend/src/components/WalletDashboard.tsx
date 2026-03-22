"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from "recharts";

interface TokenInfo {
  name: string | null;
  symbol: string | null;
  address: string;
  chain: string | null;
  price_usd: number | null;
  logo_url: string | null;
}

interface WalletToken {
  token: TokenInfo;
  balance: number;
  value_usd: number | null;
}

interface ChainBalance {
  chain_id: string;
  chain_name: string;
  usd_value: number;
}

interface DefiPosition {
  protocol: string;
  chain: string;
  chain_name: string;
  total_supplied_usd: number;
  total_borrowed_usd: number;
  net_usd_value: number;
  health_factor: number | null;
  available_borrows_usd: number | null;
  ltv: number | null;
}

interface WalletAnalysis {
  chain: string;
  address: string;
  total_value_usd: number | null;
  chains: ChainBalance[];
  tokens: WalletToken[];
  defi_positions: DefiPosition[];
}

const COLORS = [
  "#8b5cf6", "#6366f1", "#3b82f6", "#06b6d4", "#14b8a6",
  "#22c55e", "#eab308", "#f97316", "#ef4444", "#ec4899",
];

function formatUsd(val: number | null | undefined): string {
  if (val == null) return "N/A";
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
  if (val >= 1_000) return `$${(val / 1_000).toFixed(2)}K`;
  return `$${val.toFixed(2)}`;
}

function HealthBadge({ factor }: { factor: number | null }) {
  if (factor == null) return null;
  let color = "bg-green-500/20 text-green-400";
  if (factor < 1.1) color = "bg-red-500/20 text-red-400";
  else if (factor < 1.5) color = "bg-yellow-500/20 text-yellow-400";
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      HF {factor.toFixed(2)}
    </span>
  );
}

export default function WalletDashboard({ data }: { data: WalletAnalysis }) {
  const { tokens, total_value_usd, address, chain, chains = [], defi_positions = [] } = data;

  const pieData = tokens
    .filter((t) => t.value_usd && t.value_usd > 0)
    .slice(0, 10)
    .map((t, i) => ({
      name: t.token.symbol || t.token.name || "Unknown",
      value: t.value_usd!,
      fill: COLORS[i % COLORS.length],
    }));

  const chainBarData = chains.map((c, i) => ({
    name: c.chain_name,
    value: c.usd_value,
    fill: COLORS[i % COLORS.length],
  }));

  return (
    <div className="space-y-6">
      {/* Wallet header */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">Wallet Overview</h2>
            <p className="text-sm text-gray-400 font-mono">
              {chain} &middot; {address.slice(0, 8)}...{address.slice(-8)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400">Total Value</p>
            <p className="text-3xl font-bold text-purple-400">
              {formatUsd(total_value_usd)}
            </p>
          </div>
        </div>

        <p className="text-sm text-gray-500">
          {tokens.length} token{tokens.length > 1 ? "s" : ""} across{" "}
          {chains.length} chain{chains.length > 1 ? "s" : ""}
          {defi_positions.length > 0 &&
            ` + ${defi_positions.length} DeFi position${defi_positions.length > 1 ? "s" : ""}`}
        </p>
      </div>

      {/* Chain breakdown */}
      {chains.length > 0 && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">Chain Breakdown</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
            {chains.map((c, i) => {
              const pct = total_value_usd ? ((c.usd_value / total_value_usd) * 100) : 0;
              return (
                <div
                  key={c.chain_id}
                  className="bg-gray-700/30 rounded-lg p-3 text-center"
                >
                  <p className="text-sm font-medium">{c.chain_name}</p>
                  <p className="text-lg font-bold" style={{ color: COLORS[i % COLORS.length] }}>
                    {formatUsd(c.usd_value)}
                  </p>
                  <p className="text-xs text-gray-500">{pct.toFixed(0)}%</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* DeFi Positions */}
      {defi_positions.length > 0 && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">DeFi Positions</h3>
          <div className="space-y-3">
            {defi_positions.map((pos, i) => (
              <div
                key={i}
                className="bg-gray-700/20 border border-gray-700 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold">{pos.protocol}</span>
                    <span className="text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded">
                      {pos.chain_name}
                    </span>
                    <HealthBadge factor={pos.health_factor} />
                  </div>
                  <span className="text-lg font-bold text-purple-400">
                    {formatUsd(pos.net_usd_value)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Supplied</p>
                    <p className="text-green-400 font-medium">
                      {formatUsd(pos.total_supplied_usd)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Borrowed</p>
                    <p className="text-red-400 font-medium">
                      {formatUsd(pos.total_borrowed_usd)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Allocation pie chart */}
        {pieData.length > 0 && (
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Token Allocation</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  label={(props: any) =>
                    `${props.name ?? ""} ${((props.percent ?? 0) * 100).toFixed(0)}%`
                  }
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any) => formatUsd(Number(value))}
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Token list */}
        <div className="md:col-span-2 bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">Holdings</h3>
          <div className="space-y-2">
            <div className="grid grid-cols-5 text-xs text-gray-500 uppercase tracking-wide pb-2 border-b border-gray-700">
              <span>Token</span>
              <span>Chain</span>
              <span className="text-right">Balance</span>
              <span className="text-right">Price</span>
              <span className="text-right">Value</span>
            </div>

            {tokens.map((t, i) => (
              <div
                key={i}
                className="grid grid-cols-5 items-center py-2 hover:bg-gray-700/30 rounded-lg px-1 transition-colors"
              >
                <div className="flex items-center gap-2">
                  {t.token.logo_url ? (
                    <img
                      src={t.token.logo_url}
                      alt=""
                      className="w-6 h-6 rounded-full"
                    />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center text-xs">
                      {(t.token.symbol || "?")[0]}
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-medium">
                      {t.token.symbol || "Unknown"}
                    </p>
                    <p className="text-xs text-gray-500 truncate max-w-[100px]">
                      {t.token.name || t.token.address.slice(0, 8) + "..."}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  {t.token.chain || "-"}
                </p>
                <p className="text-sm text-right text-gray-300">
                  {t.balance > 0
                    ? t.balance.toLocaleString(undefined, {
                        maximumFractionDigits: 4,
                      })
                    : "-"}
                </p>
                <p className="text-sm text-right text-gray-300">
                  {t.token.price_usd != null
                    ? `$${
                        t.token.price_usd < 0.01
                          ? t.token.price_usd.toExponential(2)
                          : t.token.price_usd.toFixed(2)
                      }`
                    : "-"}
                </p>
                <p className="text-sm text-right font-medium">
                  {t.value_usd != null ? formatUsd(t.value_usd) : "-"}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
