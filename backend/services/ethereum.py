from __future__ import annotations

from typing import Optional, List

from models import (
    TokenAnalysis,
    TokenInfo,
    RiskReport,
    PoolInfo,
    WalletAnalysis,
    WalletToken,
    ChainBalance,
    DefiPosition,
)
from clients import dexscreener, goplus
from clients.evm_rpc import scan_all_chains, CHAINS
from clients.aave import scan_all_lending


async def analyze_token(address: str) -> TokenAnalysis:
    pair_data = await dexscreener.get_token_pairs("ethereum", address)
    security_data = await goplus.get_token_security("ethereum", address)

    token = TokenInfo(address=address)
    pools: List[PoolInfo] = []
    risk: Optional[RiskReport] = None

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

    if security_data:
        warnings = []
        risk_score = 0

        if security_data.get("is_honeypot") == "1":
            warnings.append("Honeypot detected")
            risk_score += 40
        if security_data.get("owner_change_balance") == "1":
            warnings.append("Owner can change balance")
            risk_score += 20
        if security_data.get("cannot_sell_all") == "1":
            warnings.append("Cannot sell all tokens")
            risk_score += 20
        if security_data.get("is_open_source") == "0":
            warnings.append("Contract is not open source")
            risk_score += 10
        if security_data.get("owner_address") and security_data.get("can_take_back_ownership") == "1":
            warnings.append("Ownership can be reclaimed")
            risk_score += 10

        buy_tax = float(security_data.get("buy_tax", 0) or 0)
        sell_tax = float(security_data.get("sell_tax", 0) or 0)
        if buy_tax > 0.1 or sell_tax > 0.1:
            warnings.append(f"High tax: buy {buy_tax*100:.0f}% / sell {sell_tax*100:.0f}%")
            risk_score += 15

        risk = RiskReport(score=min(100, risk_score), warnings=warnings, details={"goplus_raw": security_data})

    return TokenAnalysis(chain="ethereum", token=token, risk=risk, pools=pools)


# Approximate native token prices via DEXScreener (WETH/WBNB/WMATIC)
_NATIVE_PRICE_TOKENS = {
    "ETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH on mainnet
    "BNB": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",  # WBNB on BSC
    "POL": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",  # WMATIC on Polygon
}


async def _get_native_price(symbol: str) -> float:
    token_addr = _NATIVE_PRICE_TOKENS.get(symbol)
    if not token_addr:
        return 0.0
    # Map to correct DEXScreener chain
    chain_map = {"ETH": "ethereum", "BNB": "bsc", "POL": "polygon"}
    chain = chain_map.get(symbol, "ethereum")
    pair = await dexscreener.get_token_pairs(chain, token_addr)
    if pair:
        return float(pair.get("priceUsd", 0) or 0)
    return 0.0


async def analyze_wallet(address: str) -> WalletAnalysis:
    # Scan all EVM chains + Aave positions in parallel
    import asyncio
    chain_results, aave_positions = await asyncio.gather(
        scan_all_chains(address),
        scan_all_lending(address),
    )

    wallet_tokens: List[WalletToken] = []
    chains: List[ChainBalance] = []
    defi_positions: List[DefiPosition] = []
    total_value = 0.0

    # Cache native prices
    native_prices = {}

    for chain_data in chain_results:
        chain_id = chain_data["chain_id"]
        chain_name = chain_data.get("chain_name", chain_id)
        native = chain_data["native"]
        native_balance = chain_data["native_balance"]
        chain_total = 0.0

        # Get native token price (cache it)
        native_sym = native["symbol"]
        if native_sym not in native_prices:
            native_prices[native_sym] = await _get_native_price(native_sym)
        native_price = native_prices[native_sym]

        if native_balance > 0:
            native_value = native_balance * native_price
            chain_total += native_value
            wallet_tokens.append(
                WalletToken(
                    token=TokenInfo(
                        address="0x" + "0" * 40,
                        chain=chain_id,
                        name=native["name"],
                        symbol=native_sym,
                        price_usd=native_price if native_price > 0 else None,
                    ),
                    balance=native_balance,
                    value_usd=native_value if native_price > 0 else None,
                )
            )

        # ERC-20 tokens
        for t in chain_data.get("tokens", []):
            balance = t["balance"]
            # Get price from DEXScreener
            pair = await dexscreener.get_token_pairs(chain_id, t["address"])
            price = float(pair.get("priceUsd", 0) or 0) if pair else 0.0
            value = balance * price if price > 0 else None
            if value:
                chain_total += value

            wallet_tokens.append(
                WalletToken(
                    token=TokenInfo(
                        address=t["address"],
                        chain=chain_id,
                        name=t["name"],
                        symbol=t["symbol"],
                        price_usd=price if price > 0 else None,
                        logo_url=pair.get("info", {}).get("imageUrl") if pair else None,
                    ),
                    balance=balance,
                    value_usd=value,
                )
            )

        if chain_total > 0.01:
            chains.append(ChainBalance(chain_id=chain_id, chain_name=chain_name, usd_value=chain_total))
            total_value += chain_total

    # Add Aave positions
    for pos in aave_positions:
        defi_positions.append(
            DefiPosition(
                protocol=pos["protocol"],
                chain=pos["chain"],
                chain_name=pos["chain_name"],
                total_supplied_usd=pos["total_supplied_usd"],
                total_borrowed_usd=pos["total_borrowed_usd"],
                net_usd_value=pos["net_usd_value"],
                health_factor=pos.get("health_factor"),
                available_borrows_usd=pos.get("available_borrows_usd"),
                ltv=pos.get("ltv"),
            )
        )
        total_value += pos["net_usd_value"]

    # Sort
    wallet_tokens.sort(key=lambda x: x.value_usd or 0, reverse=True)
    chains.sort(key=lambda x: x.usd_value, reverse=True)
    defi_positions.sort(key=lambda x: x.net_usd_value, reverse=True)

    return WalletAnalysis(
        chain="evm",
        address=address,
        total_value_usd=total_value,
        chains=chains,
        tokens=wallet_tokens,
        defi_positions=defi_positions,
    )
