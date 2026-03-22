from __future__ import annotations

from typing import List, Dict, Any, Optional, Set

import httpx
import asyncio

# Public RPC endpoints per chain
CHAINS = {
    "ethereum": {
        "name": "Ethereum",
        "rpc": "https://eth.llamarpc.com",
        "native": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
        "chain_id": 1,
    },
    "base": {
        "name": "Base",
        "rpc": "https://mainnet.base.org",
        "native": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
        "chain_id": 8453,
    },
    "optimism": {
        "name": "Optimism",
        "rpc": "https://mainnet.optimism.io",
        "native": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
        "chain_id": 10,
    },
    "arbitrum": {
        "name": "Arbitrum",
        "rpc": "https://arb1.arbitrum.io/rpc",
        "native": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
        "chain_id": 42161,
    },
    "bsc": {
        "name": "BNB Chain",
        "rpc": "https://bsc-dataseed.binance.org",
        "native": {"symbol": "BNB", "name": "BNB", "decimals": 18},
        "chain_id": 56,
    },
    "polygon": {
        "name": "Polygon",
        "rpc": "https://polygon-rpc.com",
        "native": {"symbol": "POL", "name": "Polygon", "decimals": 18},
        "chain_id": 137,
    },
    "linea": {
        "name": "Linea",
        "rpc": "https://rpc.linea.build",
        "native": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
        "chain_id": 59144,
    },
    "zksync": {
        "name": "zkSync Era",
        "rpc": "https://mainnet.era.zksync.io",
        "native": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
        "chain_id": 324,
    },
}

BALANCE_OF_SELECTOR = "0x70a08231"
# ERC-20 metadata selectors
NAME_SELECTOR = "0x06fdde03"
SYMBOL_SELECTOR = "0x95d89b41"
DECIMALS_SELECTOR = "0x313ce567"
# Transfer(address,address,uint256) event topic
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


async def _rpc_call(rpc_url: str, method: str, params: list, timeout: int = 10) -> Optional[Any]:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(rpc_url, json=payload, timeout=timeout)
            if resp.status_code != 200:
                return None
            data = resp.json()
            return data.get("result")
        except Exception:
            return None


async def get_native_balance(chain_id: str, wallet: str) -> float:
    chain = CHAINS.get(chain_id)
    if not chain:
        return 0.0
    result = await _rpc_call(chain["rpc"], "eth_getBalance", [wallet, "latest"])
    if not result:
        return 0.0
    wei = int(result, 16)
    return wei / (10 ** chain["native"]["decimals"])


async def get_erc20_balance(rpc_url: str, wallet: str, token_address: str, decimals: int) -> float:
    padded = wallet.lower().replace("0x", "").zfill(64)
    data = BALANCE_OF_SELECTOR + padded
    result = await _rpc_call(rpc_url, "eth_call", [{"to": token_address, "data": data}, "latest"])
    if not result or result == "0x" or result == "0x0":
        return 0.0
    try:
        raw = int(result, 16)
        return raw / (10 ** decimals)
    except Exception:
        return 0.0


def _decode_string(hex_result: str) -> Optional[str]:
    """Decode ABI-encoded string from eth_call result."""
    if not hex_result or hex_result == "0x" or len(hex_result) < 130:
        return None
    try:
        hex_data = hex_result[2:]
        # offset (32 bytes) + length (32 bytes) + data
        length = int(hex_data[64:128], 16)
        if length == 0 or length > 100:
            return None
        raw = bytes.fromhex(hex_data[128:128 + length * 2])
        return raw.decode("utf-8", errors="ignore").strip("\x00")
    except Exception:
        return None


async def _get_token_metadata(rpc_url: str, token_address: str) -> Dict[str, Any]:
    """Get name, symbol, decimals for an ERC-20 token."""
    name_res, symbol_res, decimals_res = await asyncio.gather(
        _rpc_call(rpc_url, "eth_call", [{"to": token_address, "data": NAME_SELECTOR}, "latest"]),
        _rpc_call(rpc_url, "eth_call", [{"to": token_address, "data": SYMBOL_SELECTOR}, "latest"]),
        _rpc_call(rpc_url, "eth_call", [{"to": token_address, "data": DECIMALS_SELECTOR}, "latest"]),
        return_exceptions=True,
    )

    name = _decode_string(name_res) if isinstance(name_res, str) else None
    symbol = _decode_string(symbol_res) if isinstance(symbol_res, str) else None

    decimals = 18
    if isinstance(decimals_res, str) and decimals_res != "0x":
        try:
            decimals = int(decimals_res, 16)
        except Exception:
            pass

    return {"name": name, "symbol": symbol, "decimals": decimals}


async def _discover_tokens_via_logs(rpc_url: str, wallet: str) -> Set[str]:
    """Find token contracts via Transfer events TO or FROM this wallet."""
    wallet_padded = "0x" + wallet.lower().replace("0x", "").zfill(64)

    latest = await _rpc_call(rpc_url, "eth_blockNumber", [])
    if not latest:
        return set()

    latest_block = int(latest, 16)
    from_block = hex(max(0, latest_block - 500000))

    # Transfers TO and FROM this wallet (parallel)
    to_logs, from_logs = await asyncio.gather(
        _rpc_call(rpc_url, "eth_getLogs", [{
            "fromBlock": from_block, "toBlock": "latest",
            "topics": [TRANSFER_TOPIC, None, wallet_padded],
        }], timeout=20),
        _rpc_call(rpc_url, "eth_getLogs", [{
            "fromBlock": from_block, "toBlock": "latest",
            "topics": [TRANSFER_TOPIC, wallet_padded],
        }], timeout=20),
        return_exceptions=True,
    )

    contracts = set()
    for logs in [to_logs, from_logs]:
        if isinstance(logs, list):
            for log in logs:
                addr = log.get("address", "").lower()
                if addr:
                    contracts.add(addr)

    return contracts


# Well-known tokens to always check (fallback if logs don't work)
_FALLBACK_TOKENS = {
    "ethereum": [
        ("0xdac17f958d2ee523a2206206994597c13d831ec7", "USDT", "Tether USD", 6),
        ("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "USDC", "USD Coin", 6),
        ("0x6b175474e89094c44da98b954eedeac495271d0f", "DAI", "Dai", 18),
        ("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", "WBTC", "Wrapped BTC", 8),
        ("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "WETH", "Wrapped Ether", 18),
        ("0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", "AAVE", "Aave", 18),
        ("0x514910771af9ca656af840dff83e8264ecf986ca", "LINK", "Chainlink", 18),
        ("0x1f9840a85d5af5bf1d1762f925bdaddc4201f984", "UNI", "Uniswap", 18),
        ("0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce", "SHIB", "Shiba Inu", 18),
        ("0x6982508145454ce325ddbe47a25d4ec3d2311933", "PEPE", "Pepe", 18),
        ("0x9813037ee2218799597d83d4a5b6f3b6778218d9", "BONE", "Bone ShibaSwap", 18),
        ("0xaea46a60368a7bd060eec7df8cba43b7ef41ad85", "FET", "Fetch.ai", 18),
        ("0xd533a949740bb3306d119cc777fa900ba034cd52", "CRV", "Curve DAO", 18),
        ("0x4d224452801aced8b2f0aebe155379bb5d594381", "APE", "ApeCoin", 18),
        ("0xE0f63A424a4439cBE457D80E4f4b51aD25b2c56C", "CUMMIES", "CumRocket", 18),
    ],
    "base": [
        ("0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", "USDC", "USD Coin", 6),
        ("0x4200000000000000000000000000000000000006", "WETH", "Wrapped Ether", 18),
        ("0x50c5725949a6f0c72e6c4a641f24049a917db0cb", "DAI", "Dai", 18),
        ("0x532f27101965dd16442E59d40670FaF5eBB142E4", "BRETT", "Brett", 18),
        ("0xBC45647eA894030a4E9801Ec03479739FA2485F0", "TOSHI", "Toshi", 18),
        ("0xb1a03eda10342529bbf8eb700a06c60441fef25d", "MIGGLES", "Miggles", 18),
    ],
    "bsc": [
        ("0x55d398326f99059ff775485246999027b3197955", "USDT", "Tether USD", 18),
        ("0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "USDC", "USD Coin", 18),
        ("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c", "WBNB", "Wrapped BNB", 18),
        ("0xba2ae424d960c26247dd6c32edc70b295c744c43", "DOGE", "Dogecoin", 8),
        ("0x2859e4544C4bB03966803b044A93563Bd2D0DD4D", "SHIB", "Shiba Inu", 18),
        ("0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82", "CAKE", "PancakeSwap", 18),
        ("0x7bd6fabd64813c48545c9c0e312a0099d9be2540", "DOBO", "DogeBonk", 9),
    ],
    "arbitrum": [
        ("0xaf88d065e77c8cc2239327c5edb3a432268e5831", "USDC", "USD Coin", 6),
        ("0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9", "USDT", "Tether USD", 6),
        ("0x82af49447d8a07e3bd95bd0d56f35241523fbab1", "WETH", "Wrapped Ether", 18),
        ("0x912ce59144191c1204e64559fe8253a0e49e6548", "ARB", "Arbitrum", 18),
        ("0xfc5a1a6eb076a2c7ad06ed22c90d7e710e35ad0a", "GMX", "GMX", 18),
    ],
    "optimism": [
        ("0x0b2c639c533813f4aa9d7837caf62653d097ff85", "USDC", "USD Coin", 6),
        ("0x4200000000000000000000000000000000000006", "WETH", "Wrapped Ether", 18),
        ("0x4200000000000000000000000000000000000042", "OP", "Optimism", 18),
    ],
    "polygon": [
        ("0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "USDC", "USD Coin", 6),
        ("0xc2132d05d31c914a87c6611c10748aeb04b58e8f", "USDT", "Tether USD", 6),
        ("0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270", "WMATIC", "Wrapped MATIC", 18),
    ],
    "linea": [
        ("0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f", "WETH", "Wrapped Ether", 18),
        ("0x176211869ca2b568f2a7d4ee941e073a821ee1ff", "USDC", "USD Coin", 6),
    ],
    "zksync": [
        ("0x5aea5775959fbc2557cc8789bc1bf90a239d9a91", "WETH", "Wrapped Ether", 18),
        ("0x1d17cbcf0d6d143135ae902365d2e5e2a16538d4", "USDC", "USD Coin", 6),
    ],
}


async def get_all_balances_for_chain(chain_id: str, wallet: str) -> Dict[str, Any]:
    """Get native + discovered token balances for one chain."""
    chain = CHAINS.get(chain_id)
    if not chain:
        return {"chain_id": chain_id, "native_balance": 0, "tokens": []}

    rpc_url = chain["rpc"]

    # Step 1: Get native balance + discover tokens via Transfer logs (parallel)
    native_balance, discovered = await asyncio.gather(
        get_native_balance(chain_id, wallet),
        _discover_tokens_via_logs(rpc_url, wallet),
        return_exceptions=True,
    )

    if isinstance(native_balance, Exception):
        native_balance = 0.0
    if isinstance(discovered, Exception):
        discovered = set()

    # Merge discovered tokens with fallback known tokens
    fallback = _FALLBACK_TOKENS.get(chain_id, [])
    fallback_map = {addr.lower(): (sym, name, dec) for addr, sym, name, dec in fallback}

    # All addresses to check = discovered + fallback
    all_addresses = set(discovered)
    for addr, _, _, _ in fallback:
        all_addresses.add(addr.lower())

    # Limit to 40 tokens per chain
    token_addresses = list(all_addresses)[:40]

    if not token_addresses:
        return {
            "chain_id": chain_id,
            "chain_name": chain["name"],
            "native": chain["native"],
            "native_balance": native_balance,
            "tokens": [],
        }

    # Step 2: For discovered tokens (not in fallback), get metadata
    # For fallback tokens, we already know the metadata
    needs_metadata = [a for a in token_addresses if a not in fallback_map]
    metadata_tasks = [_get_token_metadata(rpc_url, addr) for addr in needs_metadata]
    metadata_results = await asyncio.gather(*metadata_tasks, return_exceptions=True)

    fetched_meta = {}
    for i, addr in enumerate(needs_metadata):
        meta = metadata_results[i] if not isinstance(metadata_results[i], Exception) else {}
        fetched_meta[addr] = meta

    # Build token list
    tokens_with_meta = []
    for addr in token_addresses:
        if addr in fallback_map:
            sym, name, dec = fallback_map[addr]
            tokens_with_meta.append({"address": addr, "name": name, "symbol": sym, "decimals": dec})
        elif addr in fetched_meta:
            m = fetched_meta[addr]
            tokens_with_meta.append({
                "address": addr,
                "name": m.get("name"),
                "symbol": m.get("symbol"),
                "decimals": m.get("decimals", 18),
            })

    # Step 3: Get all balances in parallel
    balance_tasks = [
        get_erc20_balance(rpc_url, wallet, t["address"], t["decimals"])
        for t in tokens_with_meta
    ]
    balance_results = await asyncio.gather(*balance_tasks, return_exceptions=True)

    tokens = []
    for i, t in enumerate(tokens_with_meta):
        bal = balance_results[i] if not isinstance(balance_results[i], Exception) else 0.0
        if bal > 0:
            tokens.append({**t, "balance": bal})

    return {
        "chain_id": chain_id,
        "chain_name": chain["name"],
        "native": chain["native"],
        "native_balance": native_balance,
        "tokens": tokens,
    }


async def scan_all_chains(wallet: str) -> List[Dict[str, Any]]:
    """Scan all EVM chains in parallel."""
    tasks = [get_all_balances_for_chain(cid, wallet) for cid in CHAINS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, dict)]
