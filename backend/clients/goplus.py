from __future__ import annotations

from typing import Optional

import httpx

BASE_URL = "https://api.gopluslabs.io/api/v1"


async def get_token_security(chain_id: str, address: str) -> Optional[dict]:
    """Get token security info from GoPlus (EVM chains)."""
    chain_map = {"ethereum": "1", "bsc": "56", "polygon": "137", "arbitrum": "42161"}
    gp_chain = chain_map.get(chain_id, "1")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/token_security/{gp_chain}",
            params={"contract_addresses": address},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        result = data.get("result", {})
        return result.get(address.lower())
