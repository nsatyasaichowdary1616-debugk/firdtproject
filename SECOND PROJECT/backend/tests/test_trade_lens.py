"""
TradeLens AI - Automated Test Suite
Verifies mathematical correctness of statutory charge calculators,
FIFO trade parsing, quant metrics, behavioral tilt detection, and authentication.
"""
import unittest
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app.charges_calculator import IndianChargesCalculator, BrokerRates, StatutoryRates
from app.trade_parser import TradeParser
from app.analytics_engine import AnalyticsEngine
from app.behavior_engine import BehaviorEngine
from app.ai_review_engine import AIReviewEngine
from app.auth import hash_password, verify_password, create_access_token, verify_token

class TestTradeLensAI(unittest.TestCase):
    def setUp(self):
        self.calc = IndianChargesCalculator()
        self.parser = TradeParser(self.calc)

    def test_options_charges_calculation(self):
        """
        Verify Indian Options charges:
        Buy 50 qty @ 100, Sell 50 qty @ 120
        Buy turnover = 5000, Sell turnover = 6000
        """
        res = self.calc.calculate_trade_charges(
            segment="OPTIONS",
            buy_qty=50,
            buy_price=100.0,
            sell_qty=50,
            sell_price=120.0
        )
        # Brokerage = 20 buy + 20 sell = 40.0
        self.assertEqual(res.brokerage, 40.0)
        # STT = 0.1% on sell premium (6000 * 0.001) = 6.0
        self.assertEqual(round(res.stt_ctt, 2), 6.0)
        # Stamp duty = 0.003% on buy turnover (5000 * 0.00003) = 0.15
        self.assertEqual(round(res.stamp_duty, 2), 0.15)
        # Total charges should be greater than sum of basic brokerage
        self.assertTrue(res.total_charges > 50.0)

    def test_equity_intraday_charges(self):
        """
        Verify Equity Intraday charges:
        Buy 100 @ 2500, Sell 100 @ 2520
        """
        res = self.calc.calculate_trade_charges(
            segment="EQUITY_INTRADAY",
            buy_qty=100,
            buy_price=2500.0,
            sell_qty=100,
            sell_price=2520.0
        )
        # Turnover = 250,000 buy + 252,000 sell = 502,000
        # Brokerage = min(20, 250000*0.0003) + min(20, 252000*0.0003) = 20 + 20 = 40.0
        self.assertEqual(res.brokerage, 40.0)
        # STT on intraday sell = 0.025% of 252,000 = 63.0
        self.assertEqual(round(res.stt_ctt, 2), 63.0)
        # Stamp duty on intraday buy = 0.003% of 250,000 = 7.5
        self.assertEqual(round(res.stamp_duty, 2), 7.5)

    def test_fifo_trade_matching(self):
        """
        Tests parsing and matching a Zerodha CSV snippet.
        """
        sample_csv = """symbol,isin,trade_date,exchange,segment,series,trade_type,quantity,price,order_id,trade_id,order_execution_time
NIFTY24NOV24500CE,INF769K01010,2026-10-15,NSE,NFO,OPT,BUY,50,100.00,1001,2001,2026-10-15 09:20:00
NIFTY24NOV24500CE,INF769K01010,2026-10-15,NSE,NFO,OPT,SELL,50,130.00,1002,2002,2026-10-15 09:40:00
"""
        result = self.parser.parse_csv_content(sample_csv)
        self.assertTrue(result["success"])
        self.assertEqual(result["matched_roundtrips_count"], 1)
        trade = result["trades"][0]
        self.assertEqual(trade["direction"], "LONG")
        self.assertEqual(trade["gross_pnl"], 1500.0) # (130 - 100) * 50
        self.assertTrue(trade["net_pnl"] < 1500.0) # Net PnL must deduct charges
        self.assertTrue(trade["is_win"])

    def test_quant_analytics_engine(self):
        """
        Verify Win Rate, Profit Factor, and Drawdown calculations.
        """
        mock_trades = [
            {"id": "1", "symbol": "NIFTY", "gross_pnl": 2000.0, "total_charges": 60.0, "net_pnl": 1940.0, "trade_date": "2026-10-01", "close_date": "2026-10-01 10:00:00"},
            {"id": "2", "symbol": "NIFTY", "gross_pnl": -1000.0, "total_charges": 60.0, "net_pnl": -1060.0, "trade_date": "2026-10-02", "close_date": "2026-10-02 10:00:00"},
            {"id": "3", "symbol": "NIFTY", "gross_pnl": 3000.0, "total_charges": 60.0, "net_pnl": 2940.0, "trade_date": "2026-10-03", "close_date": "2026-10-03 10:00:00"}
        ]
        res = AnalyticsEngine.calculate_metrics(mock_trades)
        summary = res["summary"]
        self.assertEqual(summary["total_trades"], 3)
        self.assertEqual(summary["winning_trades"], 2)
        self.assertEqual(summary["losing_trades"], 1)
        self.assertEqual(round(summary["win_rate"], 1), 66.7)
        self.assertEqual(summary["gross_pnl"], 4000.0)
        self.assertEqual(summary["total_charges"], 180.0)
        self.assertEqual(summary["net_pnl"], 3820.0)
        # Profit factor: gross wins (5000) / gross losses (1000) = 5.0
        self.assertEqual(summary["profit_factor"], 5.0)

    def test_behavioral_tilt_detection(self):
        """
        Verify detection of overtrading on losing days.
        """
        mock_trades = [
            # Green day: 1 trade (+2000)
            {"id": "1", "open_date": "2026-10-01 09:30:00", "trade_date": "2026-10-01", "net_pnl": 2000.0, "quantity": 50, "duration_minutes": 20},
            # Red day: 4 trades (-4000 total) -> overtrading ratio = 4.0x
            {"id": "2", "open_date": "2026-10-02 09:30:00", "trade_date": "2026-10-02", "net_pnl": -1000.0, "quantity": 50, "duration_minutes": 60},
            {"id": "3", "open_date": "2026-10-02 10:30:00", "trade_date": "2026-10-02", "net_pnl": -1000.0, "quantity": 50, "duration_minutes": 60},
            {"id": "4", "open_date": "2026-10-02 11:30:00", "trade_date": "2026-10-02", "net_pnl": -1000.0, "quantity": 100, "duration_minutes": 60},
            {"id": "5", "open_date": "2026-10-02 13:30:00", "trade_date": "2026-10-02", "net_pnl": -1000.0, "quantity": 100, "duration_minutes": 60},
        ]
        res = BehaviorEngine.analyze_behavior(mock_trades)
        self.assertEqual(res["overtrading_ratio"], 4.0)
        self.assertTrue(res["discipline_score"] < 70)
        flag_types = [f["type"] for f in res["behavioral_flags"]]
        self.assertIn("REVENGE_OVERTRADING", flag_types)

    def test_auth_security(self):
        """
        Verify password hashing and JWT token signing.
        """
        pwd = "tradelensSecurePass123"
        hashed = hash_password(pwd)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("wrongPass", hashed))

        token = create_access_token("USR-TEST", "trader@test.com", "Test Trader")
        verified = verify_token(token)
        self.assertIsNotNone(verified)
        self.assertEqual(verified["sub"], "USR-TEST")
        self.assertEqual(verified["email"], "trader@test.com")

if __name__ == '__main__':
    unittest.main()
