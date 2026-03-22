from __future__ import annotations

from typing import Optional, List

from models import (
    TokenAnalysis,
    TokenInfo,
    RiskReport,
    PoolInfo,
    HolderInfo,
    WalletAnalysis,
    WalletToken,
)
from clients import dexscreener, rugcheck, solana_rpc


async def analyze_token(address: str) -> TokenAnalysis:
    pair_data = await dexscreener.get_token_pairs("solana", address)
    rug_data = await rugcheck.get_token_report(address)

    token = TokenInfo(address=address)
    pools: List[PoolInfo] = []
    risk: Optional[RiskReport] = None
    holders: List[HolderInfo] = []

    if pair_data:
        base = pair_data.get("baseToken", {})
        token = TokenInfo(
            address=address,
            name=base.get("name"),
            symbol=base.get("symbol"),
            price_usd=float(pair_data.get("priceUsd", 0) or 0),
            price_change_24h=pair_data.get("priceChange", {}).get("h24"),
            volume_24h=pair_data.get("volume", {}).get("h24"),
            liquidity_usd=pair_data.get("liquidity", {}).get("usd"),
            market_cap=pair_data.get("marketCap"),
            logo_url=pair_data.get("info", {}).get("imageUrl"),
        )
        pools.append(
            PoolInfo(
                dex_name=pair_data.get("dexId", "unknown"),
                pair=pair_data.get("pairAddress", ""),
                liquidity_usd=pair_data.get("liquidity", {}).get("usd", 0),
                volume_24h=pair_data.get("volume", {}).get("h24", 0),
                created_at=str(pair_data.get("pairCreatedAt", "")),
            )
        )

    if rug_data:
        warnings = []
        score_raw = rug_data.get("score", 0)
        # RugCheck score: higher = safer, we invert for risk
        risk_score = max(0, min(100, 100 - score_raw))

        risks = rug_data.get("risks", [])
        for r in risks:
            warnings.append(r.get("description", r.get("name", "Unknown risk")))

        top_holders_data = rug_data.get("topHolders", [])
        for h in top_holders_data[:10]:
            holders.append(
                HolderInfo(
                    address=h.get("address", ""),
                    percentage=h.get("pct", 0),
                )
            )

        risk = RiskReport(
            score=risk_score,
            warnings=warnings,
            details={"rugcheck_score": score_raw},
        )

    return TokenAnalysis(
        chain="solana",
        token=token,
        risk=risk,
        top_holders=holders,
        pools=pools,
    )


async def analyze_wallet(address: str) -> WalletAnalysis:
    sol_balance = await solana_rpc.get_sol_balance(address)
    token_accounts = await solana_rpc.get_token_accounts(address)

    wallet_tokens: List[WalletToken] = []
    total_value = 0.0

    # Add native SOL
    sol_pair = await dexscreener.get_token_pairs("solana", "So11111111111111111111111111111111111111112")
    sol_price = float(sol_pair.get("priceUsd", 0) or 0) if sol_pair else 0.0
    sol_value = sol_balance * sol_price
    total_value += sol_value
    wallet_tokens.append(
        WalletToken(
            token=TokenInfo(
                address="So11111111111111111111111111111111111111112",
                name="Solana",
                symbol="SOL",
                price_usd=sol_price,
                logo_url=sol_pair.get("info", {}).get("imageUrl") if sol_pair else None,
            ),
            balance=sol_balance,
            value_usd=sol_value,
        )
    )

    # Add SPL tokens (fetch prices from DEXScreener)
    for t in token_accounts[:20]:
        mint = t["mint"]
        amount = t["amount"]
        pair_data = await dexscreener.get_token_pairs("solana", mint)
        price = 0.0
        name = None
        symbol = None
        logo = None
        if pair_data:
            price = float(pair_data.get("priceUsd", 0) or 0)
            base = pair_data.get("baseToken", {})
            name = base.get("name")
            symbol = base.get("symbol")
            logo = pair_data.get("info", {}).get("imageUrl")

        value = amount * price
        total_value += value
        wallet_tokens.append(
            WalletToken(
                token=TokenInfo(
                    address=mint,
                    name=name,
                    symbol=symbol,
                    price_usd=price if price > 0 else None,
                    logo_url=logo,
                ),
                balance=amount,
                value_usd=value if price > 0 else None,
            )
        )

    # Sort by value descending
    wallet_tokens.sort(key=lambda x: x.value_usd or 0, reverse=True)

    return WalletAnalysis(
        chain="solana",
        address=address,
        total_value_usd=total_value,
        tokens=wallet_tokens,
    )
