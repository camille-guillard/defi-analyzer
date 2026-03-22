from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import TokenAnalysis, WalletAnalysis
from services import solana, ethereum

app = FastAPI(title="DeFi Portfolio Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/analyze/{chain}/{address}", response_model=TokenAnalysis)
async def analyze_token(chain: str, address: str):
    if chain == "solana":
        return await solana.analyze_token(address)
    elif chain == "ethereum":
        return await ethereum.analyze_token(address)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported chain: {chain}")


@app.get("/api/wallet/{chain}/{address}", response_model=WalletAnalysis)
async def analyze_wallet(chain: str, address: str):
    if chain == "solana":
        return await solana.analyze_wallet(address)
    elif chain == "ethereum":
        return await ethereum.analyze_wallet(address)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported chain: {chain}")
