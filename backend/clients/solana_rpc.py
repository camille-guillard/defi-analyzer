from __future__ import annotations

from typing import List, Dict, Any

import httpx

RPC_URL = "https://api.mainnet-beta.solana.com"
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


async def get_token_accounts(wallet_address: str) -> List[Dict[str, Any]]:
    """Get all SPL token accounts for a Solana wallet."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_address,
            {"programId": TOKEN_PROGRAM_ID},
            {"encoding": "jsonParsed"},
        ],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(RPC_URL, json=payload, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        result = data.get("result", {}).get("value", [])

        tokens = []
        for account in result:
            info = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
            token_amount = info.get("tokenAmount", {})
            amount = float(token_amount.get("uiAmount", 0) or 0)
            if amount > 0:
                tokens.append({
                    "mint": info.get("mint", ""),
                    "amount": amount,
                    "decimals": token_amount.get("decimals", 0),
                })
        return tokens


async def get_sol_balance(wallet_address: str) -> float:
    """Get native SOL balance."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(RPC_URL, json=payload, timeout=10)
        if resp.status_code != 200:
            return 0.0
        data = resp.json()
        lamports = data.get("result", {}).get("value", 0)
        return lamports / 1_000_000_000
