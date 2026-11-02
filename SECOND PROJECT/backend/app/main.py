"""
TradeLens AI - Personal Trading Intelligence Platform
FastAPI Backend Application Server
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.database import db
from app.auth import authenticate_user, register_user, verify_token
from app.charges_calculator import calculator, IndianChargesCalculator, BrokerRates, StatutoryRates
from app.trade_parser import parser, TradeParserError
from app.analytics_engine import analytics
from app.behavior_engine import behavior
from app.ai_review_engine import ai_review
from app.sample_data import seed_demo_account, generate_sample_trades

app = FastAPI(
    title="TradeLens AI - Personal Trading Intelligence Platform",
    description="Quantitative trading analytics, statutory charge attribution, and behavioral tilt intelligence for Indian Stock & F&O traders.",
    version="1.0.0"
)

# Enable CORS for local dev / cross-origin frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Auth Helper ----------------- #
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.split(" ")[1]
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Session expired or invalid token. Please log in.")
    return user_data

def get_user_portfolio_id(user_id: str) -> str:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM portfolios WHERE user_id = ? LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if row:
            return row["id"]
        # Create portfolio if missing
        port_id = f"PORT-{user_id[-6:]}"
        cursor.execute("INSERT INTO portfolios (id, user_id, name) VALUES (?, ?, ?)", (port_id, user_id, "Main Trading Portfolio"))
        conn.commit()
        return port_id

# ----------------- Pydantic Models ----------------- #
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UploadCsvRequest(BaseModel):
    csv_content: str
    column_mapping: Optional[Dict[str, str]] = None
    strategy_default: Optional[str] = "Discretionary"
    clear_existing: Optional[bool] = False

class SimulateChargeRequest(BaseModel):
    segment: str = "OPTIONS"
    buy_price: float = 100.0
    sell_price: float = 120.0
    quantity: int = 50
    broker_name: Optional[str] = "Zerodha / Discount Broker"
    equity_delivery_brokerage: Optional[float] = 0.0
    equity_intraday_brokerage: Optional[float] = 20.0
    futures_brokerage: Optional[float] = 20.0
    options_brokerage: Optional[float] = 20.0

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None

# ----------------- Endpoints ----------------- #

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "app": "TradeLens AI",
        "version": "1.0.0",
        "environment": "production",
        "database": "sqlite_ready",
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY"))
    }

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    success, msg, data = register_user(req.email, req.password, req.full_name)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg, "data": data}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    success, msg, data = authenticate_user(req.email, req.password)
    if not success:
        raise HTTPException(status_code=401, detail=msg)
    return {"success": True, "message": msg, "data": data}

@app.post("/api/auth/demo")
def demo_login():
    """
    Instantly provisions/logs in to the demo account preloaded with 90 days of Indian F&O trades.
    """
    demo_data = seed_demo_account()
    return {
        "success": True,
        "message": "Demo mode active with simulated Indian stock and F&O trading logs.",
        "data": demo_data
    }

@app.get("/api/portfolio/summary")
def get_portfolio_summary(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    port_id = get_user_portfolio_id(user["sub"])

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE portfolio_id = ? ORDER BY open_date ASC", (port_id,))
        rows = [dict(r) for r in cursor.fetchall()]

    metrics = analytics.calculate_metrics(rows)
    return {
        "success": True,
        "portfolio_id": port_id,
        "user_name": user.get("name", "Trader"),
        "summary": metrics["summary"],
        "charges_breakdown": metrics["charges_breakdown"]
    }

@app.get("/api/portfolio/analytics")
def get_portfolio_analytics(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    port_id = get_user_portfolio_id(user["sub"])

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE portfolio_id = ? ORDER BY open_date ASC", (port_id,))
        rows = [dict(r) for r in cursor.fetchall()]

    metrics = analytics.calculate_metrics(rows)
    return {
        "success": True,
        "portfolio_id": port_id,
        "equity_curve": metrics["equity_curve"],
        "calendar_days": metrics["calendar_days"],
        "by_segment": metrics["by_segment"],
        "by_strategy": metrics["by_strategy"],
        "by_direction": metrics["by_direction"],
        "by_weekday": metrics["by_weekday"],
        "by_time_of_day": metrics["by_time_of_day"]
    }

@app.get("/api/portfolio/behavior")
def get_portfolio_behavior(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    port_id = get_user_portfolio_id(user["sub"])

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE portfolio_id = ? ORDER BY open_date ASC", (port_id,))
        rows = [dict(r) for r in cursor.fetchall()]

    behavior_metrics = behavior.analyze_behavior(rows)
    return {
        "success": True,
        "portfolio_id": port_id,
        "behavior": behavior_metrics
    }

@app.get("/api/portfolio/ai-review")
def get_ai_review(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    port_id = get_user_portfolio_id(user["sub"])

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE portfolio_id = ? ORDER BY open_date ASC", (port_id,))
        rows = [dict(r) for r in cursor.fetchall()]

    if not rows:
        return {
            "success": True,
            "review": {
                "executive_summary": "No trades logged yet. Upload your Zerodha/Groww tradebook or activate Demo Mode to review your trading intelligence.",
                "discipline_score": 100,
                "edge_leak_diagnosis": [],
                "cost_drag_analysis": "No charges recorded.",
                "actionable_directives": ["Upload trade history to start analytical diagnosis."],
                "requires_api_key": False,
                "api_key_configured": bool(os.getenv("GEMINI_API_KEY"))
            }
        }

    metrics = analytics.calculate_metrics(rows)
    behavior_metrics = behavior.analyze_behavior(rows)
    review_output = ai_review.generate_review(metrics, behavior_metrics, user_name=user.get("name", "Trader"))

    return {
        "success": True,
        "portfolio_id": port_id,
        "review": review_output
    }

@app.get("/api/trades/list")
def list_trades(limit: int = 100, offset: int = 0, authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    port_id = get_user_portfolio_id(user["sub"])

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM trades WHERE portfolio_id = ? ORDER BY open_date DESC LIMIT ? OFFSET ?",
            (port_id, limit, offset)
        )
        trades = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT COUNT(*) as cnt FROM trades WHERE portfolio_id = ?", (port_id,))
        total_count = cursor.fetchone()["cnt"]

    return {
        "success": True,
        "total_trades": total_count,
        "trades": trades
    }

@app.post("/api/trades/upload-csv")
def upload_csv(req: UploadCsvRequest, authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    port_id = get_user_portfolio_id(user["sub"])

    if not req.csv_content or not req.csv_content.strip():
        raise HTTPException(status_code=400, detail="CSV content is empty.")

    try:
        parse_result = parser.parse_csv_content(
            content=req.csv_content,
            column_mapping=req.column_mapping,
            strategy_default=req.strategy_default or "Discretionary"
        )
    except TradeParserError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not parse_result.get("success", False):
        return {
            "success": False,
            "detected_format": parse_result.get("detected_format"),
            "errors": parse_result.get("errors", ["Failed to parse file"])
        }

    parsed_trades = parse_result["trades"]
    if not parsed_trades:
        return {
            "success": False,
            "detected_format": parse_result.get("detected_format"),
            "errors": ["No completed round-trip trades could be matched from the uploaded executions."]
        }

    with db.get_connection() as conn:
        cursor = conn.cursor()
        if req.clear_existing:
            cursor.execute("DELETE FROM trades WHERE portfolio_id = ?", (port_id,))

        for t in parsed_trades:
            cursor.execute("""
            INSERT INTO trades (
                id, portfolio_id, symbol, segment, instrument_type, direction, quantity,
                entry_price, exit_price, open_date, close_date, trade_date, duration_minutes,
                turnover, gross_pnl, net_pnl, brokerage, stt_ctt, exchange_charges,
                gst, sebi_charges, stamp_duty, total_charges, is_win, strategy_tag, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t["id"], port_id, t["symbol"], t["segment"], t.get("instrument_type", "EQUITY"), t["direction"],
                t["quantity"], t["entry_price"], t["exit_price"], t["open_date"], t["close_date"],
                t["trade_date"], t.get("duration_minutes", 15), t.get("turnover", 0.0), t["gross_pnl"], t["net_pnl"],
                t.get("brokerage", 0.0), t.get("stt_ctt", 0.0), t.get("exchange_charges", 0.0), t.get("gst", 0.0),
                t.get("sebi_charges", 0.0), t.get("stamp_duty", 0.0), t.get("total_charges", 0.0),
                1 if t["is_win"] else 0, t.get("strategy_tag", "Discretionary"), t.get("notes", "")
            ))
        conn.commit()

    return {
        "success": True,
        "detected_format": parse_result["detected_format"],
        "executions_count": parse_result["executions_count"],
        "matched_roundtrips_count": len(parsed_trades),
        "unmatched_executions_count": parse_result["unmatched_executions_count"],
        "message": f"Successfully parsed and saved {len(parsed_trades)} round-trip trades."
    }

@app.post("/api/trades/clear")
def clear_trades(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    port_id = get_user_portfolio_id(user["sub"])
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trades WHERE portfolio_id = ?", (port_id,))
        conn.commit()
    return {"success": True, "message": "All portfolio trades cleared."}

@app.post("/api/calculator/simulate")
def simulate_charges(req: SimulateChargeRequest):
    custom_broker = BrokerRates(
        broker_name=req.broker_name or "Custom Broker",
        equity_delivery_flat=req.equity_delivery_brokerage or 0.0,
        equity_intraday_flat=req.equity_intraday_brokerage or 20.0,
        futures_flat=req.futures_brokerage or 20.0,
        options_flat=req.options_brokerage or 20.0
    )
    sim_calc = IndianChargesCalculator(broker_rates=custom_broker)
    
    # Calculate round-trip charges
    res = sim_calc.calculate_trade_charges(
        segment=req.segment,
        buy_qty=req.quantity,
        buy_price=req.buy_price,
        sell_qty=req.quantity,
        sell_price=req.sell_price
    )

    gross_pnl = (req.sell_price - req.buy_price) * req.quantity
    net_pnl = gross_pnl - res.total_charges
    break_even_points = round(res.total_charges / req.quantity, 2) if req.quantity > 0 else 0.0

    return {
        "success": True,
        "input": {
            "segment": req.segment,
            "buy_price": req.buy_price,
            "sell_price": req.sell_price,
            "quantity": req.quantity
        },
        "gross_pnl": round(gross_pnl, 2),
        "net_pnl": round(net_pnl, 2),
        "breakeven_points": break_even_points,
        "charges": res.to_dict()
    }

@app.get("/api/sample-csv")
def download_sample_csv(format_type: str = "zerodha"):
    """
    Returns authentic CSV template for testing.
    """
    if format_type == "zerodha":
        csv_data = """symbol,isin,trade_date,exchange,segment,series,trade_type,quantity,price,order_id,trade_id,order_execution_time
NIFTY24NOV24500CE,INF769K01010,2026-10-15,NSE,NFO,OPT,BUY,50,110.50,1200000001,310001,2026-10-15 09:25:14
NIFTY24NOV24500CE,INF769K01010,2026-10-15,NSE,NFO,OPT,SELL,50,135.20,1200000002,310002,2026-10-15 09:48:22
RELIANCE,INE002A01018,2026-10-15,NSE,EQ,EQ,BUY,25,2910.00,1200000003,310003,2026-10-15 10:15:00
RELIANCE,INE002A01018,2026-10-15,NSE,EQ,EQ,SELL,25,2935.50,1200000004,310004,2026-10-15 11:30:10
BANKNIFTY24NOV52000PE,INF769K01020,2026-10-15,NSE,NFO,OPT,BUY,30,240.00,1200000005,310005,2026-10-15 13:40:00
BANKNIFTY24NOV52000PE,INF769K01020,2026-10-15,NSE,NFO,OPT,SELL,30,195.00,1200000006,310006,2026-10-15 14:15:30
"""
        return PlainTextResponse(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tradelens_zerodha_sample.csv"})
    else:
        csv_data = """trade_date,symbol,trade_type,quantity,price,segment
2026-10-15 09:30:00,NIFTY 24500 CE,BUY,50,105.00,OPTIONS
2026-10-15 09:55:00,NIFTY 24500 CE,SELL,50,128.00,OPTIONS
2026-10-15 10:20:00,HDFCBANK,BUY,100,1720.00,EQUITY_INTRADAY
2026-10-15 11:45:00,HDFCBANK,SELL,100,1732.50,EQUITY_INTRADAY
"""
        return PlainTextResponse(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tradelens_generic_sample.csv"})

@app.get("/api/reports/export")
def export_performance_report(format: str = "json", authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    port_id = get_user_portfolio_id(user["sub"])

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE portfolio_id = ? ORDER BY open_date ASC", (port_id,))
        rows = [dict(r) for r in cursor.fetchall()]

    metrics = analytics.calculate_metrics(rows)
    behavior_metrics = behavior.analyze_behavior(rows)
    review_output = ai_review.generate_review(metrics, behavior_metrics, user_name=user.get("name", "Trader"))

    if format == "csv":
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Trade ID", "Symbol", "Segment", "Direction", "Quantity", "Entry Price", "Exit Price", "Open Date", "Close Date", "Gross PnL", "Brokerage", "STT/CTT", "Exchange Txn", "GST", "SEBI", "Stamp Duty", "Total Charges", "Net PnL", "Strategy Tag"])
        for t in rows:
            writer.writerow([
                t["id"], t["symbol"], t["segment"], t["direction"], t["quantity"],
                t["entry_price"], t["exit_price"], t["open_date"], t["close_date"],
                t["gross_pnl"], t["brokerage"], t["stt_ctt"], t["exchange_charges"],
                t["gst"], t["sebi_charges"], t["stamp_duty"], t["total_charges"],
                t["net_pnl"], t["strategy_tag"]
            ])
        return PlainTextResponse(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tradelens_trades_report.csv"})

    return {
        "report_generated_at": str(datetime.now() if 'datetime' in locals() else "2026-11-02"),
        "trader_name": user.get("name", "Trader"),
        "portfolio_id": port_id,
        "summary": metrics["summary"],
        "charges_breakdown": metrics["charges_breakdown"],
        "behavior": behavior_metrics,
        "ai_review": review_output,
        "total_trades_count": len(rows),
        "disclaimer": "Generated by TradeLens AI. Strictly for analytical & performance tracking purposes."
    }

# ----------------- Frontend Static Files Mounting ----------------- #
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>TradeLens AI is running.</h1><p>Visit /docs for the Swagger API.</p>")
