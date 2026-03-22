from __future__ import annotations

from typing import Dict, Any, Optional, List

import asyncio
from clients.evm_rpc import _rpc_call, CHAINS

# All lending protocols that implement getUserAccountData (Aave V3 interface)
# Format: (protocol_name, chain_id, pool_address)
LENDING_POOLS = [
    # Aave V3
    ("Aave V3", "ethereum", "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"),
    ("Aave V3", "base", "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"),
    ("Aave V3", "optimism", "0x794a61358D6845594F94dc1DB02A252b5b4814aD"),
    ("Aave V3", "arbitrum", "0x794a61358D6845594F94dc1DB02A252b5b4814aD"),
    ("Aave V3", "polygon", "0x794a61358D6845594F94dc1DB02A252b5b4814aD"),
    ("Aave V3", "bsc", "0x6807dc923806fE8Fd134338EABCA509979a7e0cB"),
    # Spark (MakerDAO lending, Aave V3 fork)
    ("Spark", "ethereum", "0xC13e21B648A5Ee794902342038FF3aDAB66BE987"),
    # Radiant V2 (Aave V2 fork)
    ("Radiant V2", "arbitrum", "0xF4B1486DD74D07706052A33d31d7c0AAFD0659E1"),
    ("Radiant V2", "bsc", "0xd50Cf00b6e600Dd036Ba8eF475677d816d6c4281"),
    # Seamless (Base, Aave V3 fork)
    ("Seamless", "base", "0x8F44Fd754285aa6A2b8B9B97739B79746e0475a7"),
    # Granary (Aave V2 fork)
    ("Granary", "optimism", "0x8FD4aF47E4E63d1D2D45582c3286b4BD9Bb95DfE"),
    ("Granary", "base", "0x8FD4aF47E4E63d1D2D45582c3286b4BD9Bb95DfE"),
    # Compound V3 uses a different interface - skip for now
]

# getUserAccountData(address) selector - same for all Aave forks
GET_USER_ACCOUNT_DATA = "0xbf92857c"


async def _get_lending_position(
    protocol: str, chain_id: str, pool_address: str, wallet: str
) -> Optional[Dict[str, Any]]:
    """Get lending position using getUserAccountData (Aave V3 / V2 interface).

    Returns 6 uint256 values:
    - totalCollateralBase (USD, 8 decimals)
    - totalDebtBase (USD, 8 decimals)
    - availableBorrowsBase (USD, 8 decimals)
    - currentLiquidationThreshold
    - ltv (basis points)
    - healthFactor (18 decimals)
    """
    chain = CHAINS.get(chain_id)
    if not chain:
        return None

    padded = wallet.lower().replace("0x", "").zfill(64)
    data = GET_USER_ACCOUNT_DATA + padded

    result = await _rpc_call(
        chain["rpc"],
        "eth_call",
        [{"to": pool_address, "data": data}, "latest"],
        timeout=10,
    )

    if not result or result == "0x" or len(result) < 66:
        return None

    hex_data = result[2:]
    if len(hex_data) < 384:
        return None

    total_collateral = int(hex_data[0:64], 16) / 1e8
    total_debt = int(hex_data[64:128], 16) / 1e8
    available_borrows = int(hex_data[128:192], 16) / 1e8
    ltv = int(hex_data[256:320], 16)
    health_factor_raw = int(hex_data[320:384], 16)

    if total_collateral == 0 and total_debt == 0:
        return None

    health_factor = health_factor_raw / 1e18 if health_factor_raw < 2**128 else None

    return {
        "protocol": protocol,
        "chain": chain_id,
        "chain_name": CHAINS[chain_id]["name"],
        "total_supplied_usd": total_collateral,
        "total_borrowed_usd": total_debt,
        "net_usd_value": total_collateral - total_debt,
        "available_borrows_usd": available_borrows,
        "health_factor": round(health_factor, 2) if health_factor else None,
        "ltv": ltv / 100 if ltv > 0 else None,
    }


async def scan_all_lending(wallet: str) -> List[Dict[str, Any]]:
    """Scan all lending protocol positions across all chains in parallel."""
    tasks = [
        _get_lending_position(proto, chain, addr, wallet)
        for proto, chain, addr in LENDING_POOLS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, dict) and r is not None]


# Keep backward compat
async def scan_aave_all_chains(wallet: str) -> List[Dict[str, Any]]:
    return await scan_all_lending(wallet)
