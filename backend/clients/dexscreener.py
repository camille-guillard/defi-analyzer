from __future__ import annotations

from typing import Optional, List

import httpx

BASE_URL = "https://api.dexscreener.com/latest"


async def get_token_pairs(chain: str, address: str) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/dex/tokens/{address}", timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        pairs = data.get("pairs") or []
        chain_map = {"solana": "solana", "ethereum": "ethereum"}
        target = chain_map.get(chain, chain)
        filtered = [p for p in pairs if p.get("chainId") == target]
        return filtered[0] if filtered else (pairs[0] if pairs else None)


async def search_token(query: str) -> List[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/dex/search", params={"q": query}, timeout=10
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("pairs", [])[:10]
