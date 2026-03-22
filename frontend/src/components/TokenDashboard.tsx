"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface TokenInfo {
  name: string | null;
  symbol: string | null;
  address: string;
  price_usd: number | null;
  price_change_24h: number | null;
  volume_24h: number | null;
  liquidity_usd: number | null;
  market_cap: number | null;
  logo_url: string | null;
}

interface RiskReport {
  score: number;
  warnings: string[];
}

interface HolderInfo {
  address: string;
  percentage: number;
}

interface PoolInfo {
  dex_name: string;
  pair: string;
  liquidity_usd: number;
  volume_24h: number;
  created_at: string | null;
}

interface TokenAnalysis {
  chain: string;
  token: TokenInfo;
  risk: RiskReport | null;
  top_holders: HolderInfo[];
  pools: PoolInfo[];
}

const COLORS = [
  "#8b5cf6",
  "#6366f1",
  "#3b82f6",
  "#06b6d4",
  "#14b8a6",
  "#22c55e",
  "#eab308",
  "#f97316",
  "#ef4444",
  "#ec4899",
];

function formatUsd(val: number | null | undefined): string {
  if (val == null) return "N/A";
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
  if (val >= 1_000) return `$${(val / 1_000).toFixed(2)}K`;
  return `$${val.toFixed(2)}`;
}

function RiskBadge({ score }: { score: number }) {
  let color = "bg-green-500/20 text-green-400";
  let label = "Low Risk";
  if (score > 60) {
    color = "bg-red-500/20 text-red-400";
    label = "High Risk";
  } else if (score > 30) {
    color = "bg-yellow-500/20 text-yellow-400";
    label = "Medium Risk";
  }
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${color}`}>
      {label} ({score}/100)
    </span>
  );
}

export default function TokenDashboard({ data }: { data: TokenAnalysis }) {
  const { token, risk, top_holders, pools } = data;

  const holderData = top_holders.map((h, i) => ({
    name: `${h.address.slice(0, 4)}...${h.address.slice(-4)}`,
    value: h.percentage,
    fill: COLORS[i % COLORS.length],
  }));

  const poolData = pools.map((p) => ({
    name: p.dex_name,
    liquidity: p.liquidity_usd,
    volume: p.volume_24h,
  }));

  return (
    <div className="space-y-6">
      {/* Token header */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center gap-4 mb-4">
          {token.logo_url && (
            <img
              src={token.logo_url}
              alt={token.symbol || ""}
              className="w-12 h-12 rounded-full"
            />
          )}
          <div>
            <h2 className="text-2xl font-bold">
              {token.name || "Unknown"}{" "}
              {token.symbol && (
                <span className="text-gray-400">${token.symbol}</span>
              )}
            </h2>
            <p className="text-sm text-gray-400 font-mono">
              {data.chain} &middot; {token.address.slice(0, 8)}...
              {token.address.slice(-8)}
            </p>
          </div>
          {risk && (
            <div className="ml-auto">
              <RiskBadge score={risk.score} />
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="Price" value={formatUsd(token.price_usd)} />
          <Stat
            label="24h Change"
            value={
              token.price_change_24h != null
                ? `${token.price_change_24h > 0 ? "+" : ""}${token.price_change_24h.toFixed(2)}%`
                : "N/A"
            }
            color={
              token.price_change_24h != null
                ? token.price_change_24h >= 0
                  ? "text-green-400"
                  : "text-red-400"
                : undefined
            }
          />
          <Stat label="Volume 24h" value={formatUsd(token.volume_24h)} />
          <Stat label="Liquidity" value={formatUsd(token.liquidity_usd)} />
        </div>
      </div>

      {/* Risk warnings */}
      {risk && risk.warnings.length > 0 && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-red-400 mb-3">Warnings</h3>
          <ul className="space-y-2">
            {risk.warnings.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                <span className="text-red-400 mt-0.5">!</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Holders pie chart */}
        {holderData.length > 0 && (
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Top Holders</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={holderData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(props: any) => `${props.name ?? ""} (${(props.value ?? 0).toFixed(1)}%)`}
                >
                  {holderData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Pools bar chart */}
        {poolData.length > 0 && (
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Pools</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={poolData}>
                <XAxis dataKey="name" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                    color: "#e5e7eb",
                  }}
                  labelStyle={{ color: "#9ca3af" }}
                  cursor={{ fill: "rgba(255,255,255,0.05)" }}
                />
                <Bar dataKey="liquidity" fill="#8b5cf6" name="Liquidity" />
                <Bar dataKey="volume" fill="#6366f1" name="Volume 24h" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div>
      <p className="text-sm text-gray-400">{label}</p>
      <p className={`text-lg font-semibold ${color || "text-white"}`}>
        {value}
      </p>
    </div>
  );
}
