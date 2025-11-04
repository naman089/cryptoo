from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx, os, json, random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")

app = FastAPI(title="Token Insight & PnL API")


class TokenRequest(BaseModel):
    vs_currency: str = "usd"


@app.get("/")
def health():
    return {"status": "✅ Server running"}


@app.post("/test")
def test_post():
    return {"message": "POST route working fine."}


@app.post("/api/token/{token_id}/insight")
async def get_token_insight(token_id: str, body: TokenRequest):
    """Fetch token info from CoinGecko + generate short AI insight"""

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"https://api.coingecko.com/api/v3/coins/{token_id}")
            res.raise_for_status()
            data = res.json()
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch token data: {e}")

    market = data.get("market_data", {})
    name, symbol = data.get("name"), data.get("symbol", "").upper()

    prompt = f"""
    Analyze {name} ({symbol}):
    - Price: {market.get('current_price', {}).get('usd')} USD
    - Market Cap: {market.get('market_cap', {}).get('usd')}
    - 24h Change: {market.get('price_change_percentage_24h')}%
    
    Give a short two-line insight and a sentiment label (Bullish/Bearish/Neutral).
    Respond in JSON:
    {{
      "reasoning": "...",
      "sentiment": "Bullish|Bearish|Neutral"
    }}
    """

    ai_output = {"reasoning": "AI key not set or API unavailable.", "sentiment": "Neutral"}

    if OPENAI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt.strip()}],
                    },
                )
                content = resp.json()["choices"][0]["message"]["content"]
                ai_output = json.loads(content) if content.strip().startswith("{") else {"reasoning": content[:200], "sentiment": "Neutral"}
        except Exception as e:
            ai_output = {"reasoning": f"AI error: {str(e)}", "sentiment": "Neutral"}

    return {
        "source": "coingecko",
        "token": {
            "id": data["id"],
            "symbol": data["symbol"],
            "name": data["name"],
            "market_data": {
                "price_usd": market["current_price"]["usd"],
                "market_cap_usd": market["market_cap"]["usd"],
                "change_24h": market["price_change_percentage_24h"],
            },
        },
        "insight": ai_output,
        "model": {"provider": AI_PROVIDER, "name": "gpt-4o-mini"},
    }



@app.get("/api/hyperliquid/{wallet}/pnl")
def mock_pnl(wallet: str, start: str, end: str):
    """Generate mock daily PnL data for a wallet"""
    try:
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
        if start_date > end_date:
            raise ValueError("Start date must be before end date.")
    except Exception as e:
        raise HTTPException(400, f"Invalid date input: {e}")

    daily = []
    current = start_date
    while current <= end_date:
        realized = round(random.uniform(-50, 100), 2)
        unrealized = round(random.uniform(-15, 30), 2)
        fees = round(-random.uniform(0, 5), 2)
        funding = round(random.uniform(-1, 1), 2)
        net = round(realized + unrealized + funding + fees, 2)
        daily.append({
            "date": current.strftime("%Y-%m-%d"),
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
            "fees": fees,
            "funding": funding,
            "net_pnl": net
        })
        current += timedelta(days=1)

    summary = {k: round(sum(d[k] for d in daily), 2) for k in ["realized_pnl", "unrealized_pnl", "fees", "funding", "net_pnl"]}
    summary = {k.replace("_pnl", ""): v for k, v in summary.items()}

    return {
        "wallet": wallet,
        "start": start,
        "end": end,
        "daily": daily,
        "summary": summary,
        "meta": {"generated_at": datetime.utcnow().isoformat(), "note": "Mock data for testing."},
    }

