"""
TradeLens AI - Realistic Indian Stock & F&O Trader Sample Dataset Generator
Generates ~90 days of authentic trading data for demo testing.
Clearly labeled as simulated demo data.
"""
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
from app.charges_calculator import IndianChargesCalculator

calculator = IndianChargesCalculator()

def generate_sample_trades() -> List[Dict[str, Any]]:
    """
    Generates realistic trades mirroring typical Indian F&O & intraday trading habits:
    - High morning discipline
    - Afternoon fatigue & chop
    - Expiry-day (Thursday) overtrading spikes
    - Revenge trade sizing escalation on losing runs
    """
    trades = []
    
    # Base start date ~75 trading days ago
    start_date = datetime.now() - timedelta(days=100)
    current_date = start_date

    instruments_pool = [
        {"sym": "NIFTY 24400 CE", "seg": "OPTIONS", "type": "OPTION", "lot": 25, "price_range": (80.0, 160.0), "strat": "Breakout Scalp"},
        {"sym": "NIFTY 24300 PE", "seg": "OPTIONS", "type": "OPTION", "lot": 25, "price_range": (60.0, 140.0), "strat": "VWAP Reversal"},
        {"sym": "BANKNIFTY 51800 CE", "seg": "OPTIONS", "type": "OPTION", "lot": 15, "price_range": (180.0, 380.0), "strat": "Expiry Momentum"},
        {"sym": "BANKNIFTY 51500 PE", "seg": "OPTIONS", "type": "OPTION", "lot": 15, "price_range": (150.0, 320.0), "strat": "Mean Reversion"},
        {"sym": "RELIANCE", "seg": "EQUITY_INTRADAY", "type": "EQUITY", "lot": 50, "price_range": (2850.0, 2980.0), "strat": "ORB (Opening Range Breakout)"},
        {"sym": "HDFCBANK", "seg": "EQUITY_INTRADAY", "type": "EQUITY", "lot": 100, "price_range": (1680.0, 1750.0), "strat": "Trend Following"},
        {"sym": "TATAMOTORS", "seg": "EQUITY_INTRADAY", "type": "EQUITY", "lot": 150, "price_range": (940.0, 1020.0), "strat": "Support/Resistance"},
        {"sym": "NIFTY FUT", "seg": "FUTURES", "type": "FUTURE", "lot": 25, "price_range": (24350.0, 24650.0), "strat": "Swing Breakout"},
        {"sym": "INFY", "seg": "EQUITY_DELIVERY", "type": "EQUITY", "lot": 30, "price_range": (1820.0, 1920.0), "strat": "Positional Accumulation"},
    ]

    trade_id_seq = 1

    # Deterministic seed for reproducible testing
    random.seed(42)

    while current_date <= datetime.now():
        # Skip weekends (Saturday=5, Sunday=6)
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        weekday = current_date.weekday()
        # Thursday is index 3 (Nifty Expiry Day) -> tendency to overtrade
        is_expiry_day = (weekday == 3)
        
        # Decide number of trades today
        # On normal days: 1 to 3 trades
        # On expiry days or revenge days: 4 to 8 trades
        daily_mood_loss = random.random() < 0.38  # 38% of days are losing days
        if is_expiry_day:
            trade_count = random.randint(4, 7)
        elif daily_mood_loss:
            trade_count = random.randint(3, 5) # Revenge overtrading on loss days
        else:
            trade_count = random.randint(1, 3)

        day_trades = []
        consecutive_day_losses = 0

        # Time slots throughout trading hours (09:15 to 15:30)
        time_slots = [
            (9, random.randint(20, 50)),   # Market open
            (10, random.randint(5, 45)),   # Morning trend
            (11, random.randint(15, 55)),  # Late morning
            (12, random.randint(10, 50)),  # Lunch chop
            (13, random.randint(35, 58)),  # Afternoon
            (14, random.randint(15, 45)),  # Expiry hero-or-zero flush
            (15, random.randint(5, 18))    # Closing square-off
        ]

        for t_idx in range(min(trade_count, len(time_slots))):
            inst = random.choice(instruments_pool)
            h, m = time_slots[t_idx]
            trade_time = current_date.replace(hour=h, minute=m, second=random.randint(0, 59))
            
            # Sizing: if previous trade was a loss, trader sometimes tilts and increases lots
            lots_multiplier = 1
            if consecutive_day_losses >= 1 and random.random() < 0.65:
                lots_multiplier = random.choice([2, 3]) # Revenge sizing escalation!

            base_lot = inst["lot"]
            quantity = base_lot * lots_multiplier
            min_p, max_p = inst["price_range"]
            entry_price = round(random.uniform(min_p, max_p), 2)

            # Determine win/loss probability based on time and setup
            # Morning trades (before 11:30) have higher win probability
            # Afternoon and lunch trades have lower win probability
            is_morning = h < 12
            win_prob = 0.68 if is_morning else (0.35 if is_expiry_day and h >= 13 else 0.45)

            is_win = random.random() < win_prob
            direction = random.choice(["LONG", "LONG", "LONG", "SHORT"])

            # Win/loss price impact
            if inst["seg"] == "OPTIONS":
                duration_mins = random.randint(8, 45)
                if is_win:
                    # +18% to +55% gain
                    delta_pct = random.uniform(0.18, 0.55)
                    exit_price = round(entry_price * (1.0 + delta_pct if direction == "LONG" else 1.0 - delta_pct), 2)
                    exit_price = max(1.0, exit_price)
                else:
                    # -20% to -65% loss (theta decay or SL hit)
                    delta_pct = random.uniform(0.20, 0.65)
                    exit_price = round(entry_price * (1.0 - delta_pct if direction == "LONG" else 1.0 + delta_pct), 2)
                    exit_price = max(0.5, exit_price)
            elif inst["seg"] == "FUTURES":
                duration_mins = random.randint(25, 120)
                pts_delta = random.uniform(40.0, 110.0)
                exit_price = round(entry_price + (pts_delta if is_win else -pts_delta), 2)
            else: # Equity
                duration_mins = random.randint(15, 90) if inst["seg"] == "EQUITY_INTRADAY" else random.randint(2000, 10000)
                pct_delta = random.uniform(0.006, 0.025)
                exit_price = round(entry_price * (1.0 + pct_delta if is_win else 1.0 - pct_delta), 2)

            # Gross P&L
            if direction == "LONG":
                gross_pnl = (exit_price - entry_price) * quantity
                buy_price = entry_price
                sell_price = exit_price
            else:
                gross_pnl = (entry_price - exit_price) * quantity
                buy_price = exit_price
                sell_price = entry_price

            charges = calculator.calculate_trade_charges(
                segment=inst["seg"],
                buy_qty=quantity,
                buy_price=buy_price,
                sell_qty=quantity,
                sell_price=sell_price
            )

            net_pnl = gross_pnl - charges.total_charges
            close_time = trade_time + timedelta(minutes=duration_mins)

            if net_pnl < 0:
                consecutive_day_losses += 1
            else:
                consecutive_day_losses = 0

            trade_record = {
                "id": f"SIM-{trade_id_seq:05d}",
                "symbol": inst["sym"],
                "segment": inst["seg"],
                "instrument_type": inst["type"],
                "direction": direction,
                "quantity": quantity,
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "open_date": trade_time.strftime("%Y-%m-%d %H:%M:%S"),
                "close_date": close_time.strftime("%Y-%m-%d %H:%M:%S"),
                "trade_date": current_date.strftime("%Y-%m-%d"),
                "duration_minutes": duration_mins,
                "turnover": round(charges.turnover, 2),
                "gross_pnl": round(gross_pnl, 2),
                "net_pnl": round(net_pnl, 2),
                "brokerage": charges.brokerage,
                "stt_ctt": charges.stt_ctt,
                "exchange_charges": charges.exchange_charges,
                "gst": charges.gst,
                "sebi_charges": charges.sebi_charges,
                "stamp_duty": charges.stamp_duty,
                "total_charges": charges.total_charges,
                "is_win": bool(net_pnl > 0),
                "strategy_tag": inst["strat"],
                "is_simulated": True,
                "notes": "Simulated Indian Market Demo Trade"
            }

            trades.append(trade_record)
            trade_id_seq += 1

        current_date += timedelta(days=1)

    return trades

def seed_demo_account() -> Dict[str, Any]:
    """
    Seeds the database with a pre-configured demo account and trades.
    """
    from app.auth import register_user, authenticate_user
    from app.database import db

    demo_email = "demo@tradelens.ai"
    demo_pass = "demotrader123"

    # Try authenticating first
    success, msg, auth_res = authenticate_user(demo_email, demo_pass)
    if not success:
        # Register fresh demo user
        _, _, auth_res = register_user(demo_email, demo_pass, "Arjun Verma (Demo Trader)", is_demo=True)

    portfolio_id = auth_res["portfolio_id"]

    # Check if trades already exist
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM trades WHERE portfolio_id = ?", (portfolio_id,))
        count = cursor.fetchone()["cnt"]

        if count == 0:
            sample_trades = generate_sample_trades()
            for t in sample_trades:
                cursor.execute("""
                INSERT INTO trades (
                    id, portfolio_id, symbol, segment, instrument_type, direction, quantity,
                    entry_price, exit_price, open_date, close_date, trade_date, duration_minutes,
                    turnover, gross_pnl, net_pnl, brokerage, stt_ctt, exchange_charges,
                    gst, sebi_charges, stamp_duty, total_charges, is_win, strategy_tag, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    t["id"], portfolio_id, t["symbol"], t["segment"], t["instrument_type"], t["direction"],
                    t["quantity"], t["entry_price"], t["exit_price"], t["open_date"], t["close_date"],
                    t["trade_date"], t["duration_minutes"], t["turnover"], t["gross_pnl"], t["net_pnl"],
                    t["brokerage"], t["stt_ctt"], t["exchange_charges"], t["gst"], t["sebi_charges"],
                    t["stamp_duty"], t["total_charges"], 1 if t["is_win"] else 0, t["strategy_tag"], t["notes"]
                ))
            conn.commit()

    return auth_res
