from __future__ import annotations

from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class TokenInfo(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    address: str
    chain: Optional[str] = None
    price_usd: Optional[float] = None
    price_change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    liquidity_usd: Optional[float] = None
    market_cap: Optional[float] = None
    logo_url: Optional[str] = None


class RiskReport(BaseModel):
    score: int  # 0-100, higher = riskier
    warnings: List[str] = []
    details: Dict = {}


class HolderInfo(BaseModel):
    address: str
    percentage: float


class PoolInfo(BaseModel):
    dex_name: str
    pair: str
    liquidity_usd: float
    volume_24h: float
    created_at: Optional[str] = None


class TokenAnalysis(BaseModel):
    chain: str
    token: TokenInfo
    risk: Optional[RiskReport] = None
    top_holders: List[HolderInfo] = []
    pools: List[PoolInfo] = []


class WalletToken(BaseModel):
    token: TokenInfo
    balance: float
    value_usd: Optional[float] = None


class ChainBalance(BaseModel):
    chain_id: str
    chain_name: str
    usd_value: float


class DefiPosition(BaseModel):
    protocol: str
    chain: str
    chain_name: str
    total_supplied_usd: float
    total_borrowed_usd: float
    net_usd_value: float
    health_factor: Optional[float] = None
    available_borrows_usd: Optional[float] = None
    ltv: Optional[float] = None


class WalletAnalysis(BaseModel):
    chain: str
    address: str
    total_value_usd: Optional[float] = None
    chains: List[ChainBalance] = []
    tokens: List[WalletToken] = []
    defi_positions: List[DefiPosition] = []
