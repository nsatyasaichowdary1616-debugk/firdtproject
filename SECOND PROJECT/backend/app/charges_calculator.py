"""
TradeLens AI - Indian Brokerage & Statutory Charge Calculator
SEBI, NSE, and Ministry of Finance Compliant Engine
Covers Equity Delivery, Equity Intraday, Index/Stock Futures, and Index/Stock Options.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class BrokerRates:
    broker_name: str = "Zerodha / Discount Broker"
    equity_delivery_flat: float = 0.0         # ₹0 for discount brokers
    equity_delivery_pct: float = 0.0
    equity_intraday_flat: float = 20.0        # ₹20 or 0.03% whichever is lower
    equity_intraday_pct: float = 0.0003       # 0.03%
    futures_flat: float = 20.0                # ₹20 flat per executed order
    futures_pct: float = 0.0003
    options_flat: float = 20.0                # ₹20 flat per executed order
    options_pct: float = 0.0

@dataclass
class StatutoryRates:
    # STT Rates (Securities Transaction Tax) - Updated with SEBI Oct 2024 revisions
    stt_delivery_buy_pct: float = 0.001       # 0.1% on buy
    stt_delivery_sell_pct: float = 0.001      # 0.1% on sell
    stt_intraday_sell_pct: float = 0.00025    # 0.025% on sell only
    stt_futures_sell_pct: float = 0.0002      # 0.02% on sell turnover (revised from 0.0125%)
    stt_options_sell_pct: float = 0.001       # 0.1% on sell premium (revised from 0.0625%)

    # Exchange Transaction Charges (NSE standard)
    exch_equity_pct: float = 0.0000297        # 0.00297%
    exch_futures_pct: float = 0.0000173       # 0.00173%
    exch_options_pct: float = 0.0003503       # 0.03503% on premium turnover

    # GST
    gst_rate_pct: float = 0.18                # 18% on (Brokerage + Exchange + SEBI)

    # SEBI Charges
    sebi_charge_pct: float = 0.000001         # ₹10 per crore (0.0001%)

    # Stamp Duty (Applied on BUY side turnover only)
    stamp_duty_delivery_pct: float = 0.00015  # 0.015% (₹1500/Cr)
    stamp_duty_intraday_pct: float = 0.00003  # 0.003% (₹300/Cr)
    stamp_duty_futures_pct: float = 0.00002   # 0.002% (₹200/Cr)
    stamp_duty_options_pct: float = 0.00003   # 0.003% (₹300/Cr)

@dataclass
class ChargesBreakdown:
    brokerage: float
    stt_ctt: float
    exchange_charges: float
    gst: float
    sebi_charges: float
    stamp_duty: float
    total_charges: float
    turnover: float
    buy_turnover: float
    sell_turnover: float
    assumptions_disclosed: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Round numerical values to 2 decimal places for financial reporting
        for k in ['brokerage', 'stt_ctt', 'exchange_charges', 'gst', 'sebi_charges', 'stamp_duty', 'total_charges', 'turnover', 'buy_turnover', 'sell_turnover']:
            d[k] = round(d[k], 2)
        return d


class IndianChargesCalculator:
    """
    Computes exact statutory and broker charges for any Indian trading transaction.
    """
    def __init__(self, broker_rates: Optional[BrokerRates] = None, statutory_rates: Optional[StatutoryRates] = None):
        self.broker = broker_rates or BrokerRates()
        self.statutory = statutory_rates or StatutoryRates()

    def normalize_segment(self, segment_str: str) -> str:
        s = (segment_str or "").upper().strip()
        if "DELIVERY" in s or "EQ_DELIVERY" in s or "CNC" in s:
            return "EQUITY_DELIVERY"
        elif "INTRADAY" in s or "EQ_INTRADAY" in s or "MIS" in s or "EQUITY" in s:
            return "EQUITY_INTRADAY"
        elif "FUT" in s:
            return "FUTURES"
        elif "OPT" in s or "CE" in s or "PE" in s or "CALL" in s or "PUT" in s:
            return "OPTIONS"
        return "EQUITY_INTRADAY"

    def calculate_trade_charges(
        self,
        segment: str,
        buy_qty: int,
        buy_price: float,
        sell_qty: int,
        sell_price: float,
        exchange: str = "NSE"
    ) -> ChargesBreakdown:
        """
        Calculates itemized charges for a round-trip or single-leg trade.
        """
        normalized_seg = self.normalize_segment(segment)
        buy_turnover = float(buy_qty * buy_price)
        sell_turnover = float(sell_qty * sell_price)
        total_turnover = buy_turnover + sell_turnover

        # 1. Brokerage Calculation
        brokerage = 0.0
        if normalized_seg == "EQUITY_DELIVERY":
            # Delivery brokerage
            if buy_qty > 0:
                brokerage += min(self.broker.equity_delivery_flat, buy_turnover * self.broker.equity_delivery_pct) if self.broker.equity_delivery_pct > 0 else self.broker.equity_delivery_flat
            if sell_qty > 0:
                brokerage += min(self.broker.equity_delivery_flat, sell_turnover * self.broker.equity_delivery_pct) if self.broker.equity_delivery_pct > 0 else self.broker.equity_delivery_flat

        elif normalized_seg == "EQUITY_INTRADAY":
            # ₹20 or 0.03% per executed order
            if buy_qty > 0:
                brokerage += min(self.broker.equity_intraday_flat, buy_turnover * self.broker.equity_intraday_pct)
            if sell_qty > 0:
                brokerage += min(self.broker.equity_intraday_flat, sell_turnover * self.broker.equity_intraday_pct)

        elif normalized_seg == "FUTURES":
            # ₹20 or 0.03% per executed order
            if buy_qty > 0:
                brokerage += min(self.broker.futures_flat, buy_turnover * self.broker.futures_pct)
            if sell_qty > 0:
                brokerage += min(self.broker.futures_flat, sell_turnover * self.broker.futures_pct)

        elif normalized_seg == "OPTIONS":
            # Flat ₹20 per executed order on premium turnover
            if buy_qty > 0:
                brokerage += self.broker.options_flat
            if sell_qty > 0:
                brokerage += self.broker.options_flat

        # 2. STT / CTT (Securities Transaction Tax)
        stt = 0.0
        if normalized_seg == "EQUITY_DELIVERY":
            # 0.1% on both Buy and Sell turnover
            stt = (buy_turnover * self.statutory.stt_delivery_buy_pct) + (sell_turnover * self.statutory.stt_delivery_sell_pct)
        elif normalized_seg == "EQUITY_INTRADAY":
            # 0.025% on Sell turnover only
            stt = sell_turnover * self.statutory.stt_intraday_sell_pct
        elif normalized_seg == "FUTURES":
            # 0.02% on Sell turnover only (SEBI revised)
            stt = sell_turnover * self.statutory.stt_futures_sell_pct
        elif normalized_seg == "OPTIONS":
            # 0.1% on Sell premium turnover only (SEBI revised Oct 2024)
            stt = sell_turnover * self.statutory.stt_options_sell_pct

        # 3. Exchange Transaction Charges
        exch_charges = 0.0
        if normalized_seg in ["EQUITY_DELIVERY", "EQUITY_INTRADAY"]:
            exch_charges = total_turnover * self.statutory.exch_equity_pct
        elif normalized_seg == "FUTURES":
            exch_charges = total_turnover * self.statutory.exch_futures_pct
        elif normalized_seg == "OPTIONS":
            # NSE Options: 0.03503% of premium turnover (buy + sell)
            exch_charges = total_turnover * self.statutory.exch_options_pct

        # 4. SEBI Turnover Charges (₹10 per Crore = 0.0001%)
        sebi_charges = total_turnover * self.statutory.sebi_charge_pct

        # 5. GST (18% on Brokerage + Exchange Txn + SEBI)
        gst = (brokerage + exch_charges + sebi_charges) * self.statutory.gst_rate_pct

        # 6. Stamp Duty (Payable on BUY turnover only)
        stamp_duty = 0.0
        if normalized_seg == "EQUITY_DELIVERY":
            stamp_duty = buy_turnover * self.statutory.stamp_duty_delivery_pct
        elif normalized_seg == "EQUITY_INTRADAY":
            stamp_duty = buy_turnover * self.statutory.stamp_duty_intraday_pct
        elif normalized_seg == "FUTURES":
            stamp_duty = buy_turnover * self.statutory.stamp_duty_futures_pct
        elif normalized_seg == "OPTIONS":
            stamp_duty = buy_turnover * self.statutory.stamp_duty_options_pct

        total_charges = brokerage + stt + exch_charges + gst + sebi_charges + stamp_duty

        assumptions = {
            "broker": self.broker.broker_name,
            "segment_classified": normalized_seg,
            "stt_rule": f"STT applied on {'buy & sell' if normalized_seg == 'EQUITY_DELIVERY' else 'sell only'}",
            "stt_rate_pct": (
                self.statutory.stt_options_sell_pct * 100 if normalized_seg == "OPTIONS"
                else self.statutory.stt_futures_sell_pct * 100 if normalized_seg == "FUTURES"
                else self.statutory.stt_intraday_sell_pct * 100 if normalized_seg == "EQUITY_INTRADAY"
                else self.statutory.stt_delivery_buy_pct * 100
            ),
            "gst_rate": "18% on (Brokerage + Exchange + SEBI)",
            "stamp_duty_rule": "Payable on BUY side execution turnover only",
            "effective_date_disclosed": "SEBI revised rate cycle (Oct 2024 onwards: Options STT 0.1% on sell, Futures STT 0.02% on sell)",
        }

        return ChargesBreakdown(
            brokerage=brokerage,
            stt_ctt=stt,
            exchange_charges=exch_charges,
            gst=gst,
            sebi_charges=sebi_charges,
            stamp_duty=stamp_duty,
            total_charges=total_charges,
            turnover=total_turnover,
            buy_turnover=buy_turnover,
            sell_turnover=sell_turnover,
            assumptions_disclosed=assumptions
        )

# Module singleton instance
calculator = IndianChargesCalculator()
