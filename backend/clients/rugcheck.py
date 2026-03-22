from __future__ import annotations

from typing import Optional

import httpx

BASE_URL = "https://api.rugcheck.xyz/v1"


async def get_token_report(mint_address: str) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/tokens/{mint_address}/report/summary", timeout=10
        )
        if resp.status_code != 200:
            return None
        return resp.json()
