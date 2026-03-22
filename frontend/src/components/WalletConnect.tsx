"use client";

import { useWallet } from "@solana/wallet-adapter-react";
import { useAccount, useConnect, useDisconnect } from "wagmi";

interface WalletConnectProps {
  onAddressDetected: (address: string, chain: string) => void;
}

export default function WalletConnect({
  onAddressDetected,
}: WalletConnectProps) {
  // Solana
  const { publicKey: solanaKey, connect: solanaConnect, disconnect: solanaDisconnect, wallet: solanaWallet, select, wallets } = useWallet();

  // EVM (MetaMask, Rabby, etc.)
  const { address: evmAddress, isConnected: evmConnected } = useAccount();
  const { connect: evmConnect, connectors } = useConnect();
  const { disconnect: evmDisconnect } = useDisconnect();

  const handleSolanaConnect = () => {
    if (solanaKey) {
      onAddressDetected(solanaKey.toString(), "solana");
    } else {
      // Select Phantom if available, otherwise first wallet
      const phantom = wallets.find((w) => w.adapter.name === "Phantom");
      if (phantom) {
        select(phantom.adapter.name);
      }
      solanaConnect().catch(() => {});
    }
  };

  const handleEvmConnect = () => {
    if (evmConnected && evmAddress) {
      onAddressDetected(evmAddress, "ethereum");
    } else {
      const injectedConnector = connectors.find((c) => c.id === "injected");
      if (injectedConnector) {
        evmConnect({ connector: injectedConnector });
      }
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">
        Connect Wallet
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* EVM */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2">
            <svg width="20" height="20" viewBox="0 0 256 417" fill="none"><path d="M127.961 0l-2.795 9.5v275.668l2.795 2.79 127.962-75.638z" fill="#343434"/><path d="M127.962 0L0 212.32l127.962 75.639V154.158z" fill="#8C8C8C"/><path d="M127.961 312.187l-1.575 1.92V414.45l1.575 4.6L256 236.587z" fill="#3C3C3B"/><path d="M127.962 419.05V312.187L0 236.585z" fill="#8C8C8C"/><path d="M127.961 287.958l127.96-75.637-127.96-58.162z" fill="#141414"/><path d="M0 212.32l127.96 75.638V154.159z" fill="#393939"/></svg>
            <span className="text-sm font-semibold text-gray-300">Ethereum</span>
            <span className="text-xs text-gray-500">MetaMask / Rabby</span>
          </div>

          {evmConnected && evmAddress ? (
            <div className="space-y-2">
              <p className="text-xs text-gray-400 font-mono truncate">
                {evmAddress}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => onAddressDetected(evmAddress, "ethereum")}
                  className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
                >
                  Analyze my wallet
                </button>
                <button
                  onClick={() => evmDisconnect()}
                  className="px-3 py-2 text-gray-400 hover:text-white text-sm border border-gray-600 rounded-lg transition-colors"
                >
                  Disconnect
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={handleEvmConnect}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
            >
              Connect MetaMask / Rabby
            </button>
          )}
        </div>

        {/* Solana */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2">
            <svg width="20" height="20" viewBox="0 0 128 128" fill="none"><defs><linearGradient id="sol" x1="0" y1="128" x2="128" y2="0"><stop stopColor="#9945FF"/><stop offset="0.5" stopColor="#8752F3"/><stop offset="1" stopColor="#14F195"/></linearGradient></defs><circle cx="64" cy="64" r="64" fill="url(#sol)"/><path d="M36.7 80.3a2.1 2.1 0 011.5-.6h53.1c.9 0 1.4 1.1.7 1.8l-10.7 10.7a2.1 2.1 0 01-1.5.6H26.7c-.9 0-1.4-1.1-.7-1.8L36.7 80.3zm0-44.5a2.2 2.2 0 011.5-.6h53.1c.9 0 1.4 1.1.7 1.8L81.3 47.7a2.1 2.1 0 01-1.5.6H26.7c-.9 0-1.4-1.1-.7-1.8L36.7 35.8zm44.6 21.6a2.1 2.1 0 00-1.5-.6H26.7c-.9 0-1.4 1.1-.7 1.8L36.7 69.3a2.1 2.1 0 001.5.6h53.1c.9 0 1.4-1.1.7-1.8L81.3 57.4z" fill="#fff"/></svg>
            <span className="text-sm font-semibold text-gray-300">Solana</span>
            <span className="text-xs text-gray-500">Phantom</span>
          </div>

          {solanaKey ? (
            <div className="space-y-2">
              <p className="text-xs text-gray-400 font-mono truncate">
                {solanaKey.toString()}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => onAddressDetected(solanaKey.toString(), "solana")}
                  className="flex-1 px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors"
                >
                  Analyze my wallet
                </button>
                <button
                  onClick={() => solanaDisconnect()}
                  className="px-3 py-2 text-gray-400 hover:text-white text-sm border border-gray-600 rounded-lg transition-colors"
                >
                  Disconnect
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={handleSolanaConnect}
              className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors"
            >
              Connect Phantom
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
