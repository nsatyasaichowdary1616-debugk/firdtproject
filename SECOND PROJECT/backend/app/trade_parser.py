"""
TradeLens AI - Trade File Parser & Broker Normalization Engine
Parses trade logs from Zerodha, Groww, Angel One, Upstox, and Generic CSVs.
Features FIFO round-trip execution matching, error validation, and column mapping.
"""
import io
import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from app.charges_calculator import IndianChargesCalculator

class TradeParserError(Exception):
    pass

class TradeParser:
    def __init__(self, charges_calc: Optional[IndianChargesCalculator] = None):
        self.calc = charges_calc or IndianChargesCalculator()

    @staticmethod
    def detect_broker_format(headers: List[str]) -> str:
        h = [col.strip().lower() for col in headers]
        h_str = " ".join(h)
        if "isin" in h and "order_execution_time" in h:
            return "zerodha"
        elif "trade_type" in h and "tradingsymbol" in h:
            return "zerodha"
        elif "stock name" in h and "order date" in h:
            return "groww"
        elif "scrip" in h and "buy/sell" in h:
            return "angelone"
        elif "scrip" in h and "action" in h:
            return "upstox"
        elif "gross_pnl" in h or "entry_price" in h or "close_date" in h:
            return "tradelens_direct"
        return "generic"

    @staticmethod
    def classify_instrument(symbol: str, raw_segment: str = "") -> Tuple[str, str, Optional[float], Optional[str]]:
        """
        Classifies an Indian instrument into:
        (segment, instrument_type, strike_price, option_type)
        Examples:
          "NIFTY 24500 CE" -> ("OPTIONS", "OPTION", 24500.0, "CE")
          "BANKNIFTY 52000 PE" -> ("OPTIONS", "OPTION", 52000.0, "PE")
          "RELIANCE" -> ("EQUITY_INTRADAY" or "EQUITY_DELIVERY", "EQUITY", None, None)
          "NIFTY NOV FUT" -> ("FUTURES", "FUTURE", None, None)
        """
        s = symbol.upper().strip()
        raw_seg = (raw_segment or "").upper().strip()

        # Check options pattern (e.g., NIFTY24DEC24500CE, NIFTY 24500 CE, BANKNIFTY 50000 PE)
        opt_match = re.search(r'(\d{4,6})\s*(CE|PE)', s)
        if opt_match:
            strike = float(opt_match.group(1))
            opt_type = opt_match.group(2)
            return "OPTIONS", "OPTION", strike, opt_type

        if "CE" in s.split() or "PE" in s.split() or "CALL" in s or "PUT" in s:
            opt_type = "CE" if "CE" in s or "CALL" in s else "PE"
            num_match = re.search(r'\d+', s)
            strike = float(num_match.group(0)) if num_match else None
            return "OPTIONS", "OPTION", strike, opt_type

        if "FUT" in s or "FUTURES" in raw_seg or "NFO-FUT" in raw_seg:
            return "FUTURES", "FUTURE", None, None

        if "CNC" in raw_seg or "DELIVERY" in raw_seg:
            return "EQUITY_DELIVERY", "EQUITY", None, None

        return "EQUITY_INTRADAY", "EQUITY", None, None

    def parse_csv_content(
        self,
        content: str,
        column_mapping: Optional[Dict[str, str]] = None,
        strategy_default: str = "Discretionary"
    ) -> Dict[str, Any]:
        """
        Parses raw CSV string, auto-identifies columns or applies custom mapping,
        and matches trades into round trips.
        """
        f = io.StringIO(content.strip())
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise TradeParserError("The uploaded CSV file is completely empty.")

        clean_headers = [h.strip() for h in raw_headers if h.strip()]
        detected_format = self.detect_broker_format(clean_headers)

        f.seek(0)
        try:
            df = pd.read_csv(f)
        except Exception as e:
            raise TradeParserError(f"Failed to parse CSV file: {str(e)}")

        df.columns = [c.strip() for c in df.columns]

        # Check if already a pre-computed round-trip trade history
        if "gross_pnl" in [c.lower() for c in df.columns] and "net_pnl" in [c.lower() for c in df.columns]:
            return self._process_direct_roundtrip_df(df)

        # Standardize column mapping
        std_df, validation_errors = self._normalize_columns(df, detected_format, column_mapping)
        if validation_errors:
            return {
                "success": False,
                "detected_format": detected_format,
                "errors": validation_errors,
                "trades": [],
                "executions_count": 0
            }

        # Match buy & sell executions into closed round trips using FIFO
        round_trips, unmatched = self._match_fifo_trades(std_df, strategy_default)

        return {
            "success": True,
            "detected_format": detected_format,
            "executions_count": len(std_df),
            "matched_roundtrips_count": len(round_trips),
            "unmatched_executions_count": len(unmatched),
            "trades": round_trips,
            "errors": []
        }

    def _normalize_columns(
        self,
        df: pd.DataFrame,
        format_type: str,
        custom_mapping: Optional[Dict[str, str]]
    ) -> Tuple[pd.DataFrame, List[str]]:
        errors = []
        col_lower = {c.lower(): c for c in df.columns}

        # Build mapping based on format
        mapping = {}
        if custom_mapping:
            mapping = custom_mapping
        elif format_type == "zerodha":
            mapping = {
                "date": col_lower.get("trade_date") or col_lower.get("order_execution_time", "trade_date"),
                "symbol": col_lower.get("tradingsymbol") or col_lower.get("symbol", "symbol"),
                "trade_type": col_lower.get("trade_type", "trade_type"),
                "quantity": col_lower.get("quantity", "quantity"),
                "price": col_lower.get("price", "price"),
                "segment": col_lower.get("segment", "segment")
            }
        elif format_type == "groww":
            mapping = {
                "date": col_lower.get("order date") or col_lower.get("execution date/time", "Order Date"),
                "symbol": col_lower.get("symbol") or col_lower.get("stock name", "Symbol"),
                "trade_type": col_lower.get("type", "Type"),
                "quantity": col_lower.get("quantity", "Quantity"),
                "price": col_lower.get("price", "Price"),
                "segment": col_lower.get("exchange", "Exchange")
            }
        elif format_type == "angelone":
            mapping = {
                "date": col_lower.get("trade date", "Trade Date"),
                "symbol": col_lower.get("scrip", "Scrip"),
                "trade_type": col_lower.get("buy/sell", "Buy/Sell"),
                "quantity": col_lower.get("qty", "Qty"),
                "price": col_lower.get("price", "Price"),
                "segment": col_lower.get("segment", "Segment")
            }
        elif format_type == "upstox":
            mapping = {
                "date": col_lower.get("date", "Date"),
                "symbol": col_lower.get("scrip", "Scrip"),
                "trade_type": col_lower.get("action", "Action"),
                "quantity": col_lower.get("quantity", "Quantity"),
                "price": col_lower.get("price", "Price"),
                "segment": col_lower.get("product", "Product")
            }
        else:
            # Generic guesser
            for key, candidates in [
                ("date", ["date", "trade_date", "trade date", "time", "timestamp", "datetime"]),
                ("symbol", ["symbol", "scrip", "tradingsymbol", "ticker", "stock", "instrument"]),
                ("trade_type", ["trade_type", "type", "action", "side", "buy/sell", "order_type"]),
                ("quantity", ["quantity", "qty", "volume", "shares"]),
                ("price", ["price", "trade_price", "avg_price", "rate", "exec_price"]),
                ("segment", ["segment", "product", "instrument_type", "series", "exchange"])
            ]:
                found = None
                for c in candidates:
                    if c in col_lower:
                        found = col_lower[c]
                        break
                if found:
                    mapping[key] = found
                elif key in ["date", "symbol", "trade_type", "quantity", "price"]:
                    errors.append(f"Missing mandatory column for '{key}'. Expected one of: {', '.join(candidates)}")

        if errors:
            return df, errors

        # Standardize DataFrame
        res = pd.DataFrame()
        for std_col, orig_col in mapping.items():
            if orig_col in df.columns:
                res[std_col] = df[orig_col]
            else:
                if std_col == "segment":
                    res[std_col] = "EQ_INTRADAY"
                else:
                    errors.append(f"Mapped column '{orig_col}' not found in file.")

        if errors:
            return df, errors

        # Clean and validate rows
        res = res.dropna(subset=["date", "symbol", "trade_type", "quantity", "price"])
        res["quantity"] = pd.to_numeric(res["quantity"].astype(str).str.replace(',', '').str.strip(), errors="coerce").fillna(0).astype(int)
        res["price"] = pd.to_numeric(res["price"].astype(str).str.replace(',', '').str.replace('₹', '').str.strip(), errors="coerce").fillna(0.0)
        res["trade_type"] = res["trade_type"].astype(str).str.upper().str.strip()
        res["trade_type"] = res["trade_type"].apply(lambda x: "BUY" if x in ["BUY", "B"] else ("SELL" if x in ["SELL", "S"] else x))

        # Filter out invalid quantities or prices
        invalid_count = len(res[(res["quantity"] <= 0) | (res["price"] <= 0)])
        if invalid_count > 0:
            res = res[(res["quantity"] > 0) & (res["price"] > 0)]

        # Parse dates
        def parse_date_safely(d_str):
            s = str(d_str).strip()
            for fmt in [
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
                "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"
            ]:
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    continue
            return pd.to_datetime(s, errors="coerce")

        res["parsed_datetime"] = res["date"].apply(parse_date_safely)
        res = res.sort_values(by="parsed_datetime")
        return res, []

    def _match_fifo_trades(self, df: pd.DataFrame, default_strategy: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        FIFO matching algorithm for buys and sells per symbol.
        """
        round_trips = []
        open_positions: Dict[str, List[Dict[str, Any]]] = {}

        for idx, row in df.iterrows():
            sym = str(row["symbol"]).strip().upper()
            qty = int(row["quantity"])
            price = float(row["price"])
            action = str(row["trade_type"]).upper()
            dt = row["parsed_datetime"]
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(dt) else str(row["date"])
            date_only = dt.strftime("%Y-%m-%d") if pd.notnull(dt) else dt_str[:10]
            raw_seg = str(row.get("segment", ""))

            segment, inst_type, strike, opt_type = self.classify_instrument(sym, raw_seg)

            if sym not in open_positions:
                open_positions[sym] = []

            # Check if there is an opposite position to match
            opposite_action = "SELL" if action == "BUY" else "BUY"
            
            # Find opposite lots in open_positions
            matched_qty = 0
            while open_positions[sym] and open_positions[sym][0]["action"] == opposite_action and qty > 0:
                opp = open_positions[sym][0]
                fill_qty = min(qty, opp["quantity"])
                
                # Determine Buy & Sell sides
                if action == "SELL":
                    # Long trade closed: opp is BUY, current is SELL
                    direction = "LONG"
                    buy_price = opp["price"]
                    sell_price = price
                    open_dt = opp["datetime"]
                    close_dt = dt_str
                else:
                    # Short trade covered: opp is SELL, current is BUY
                    direction = "SHORT"
                    buy_price = price
                    sell_price = opp["price"]
                    open_dt = opp["datetime"]
                    close_dt = dt_str

                # Gross P&L
                gross_pnl = (sell_price - buy_price) * fill_qty

                # Charges calculation
                charges = self.calc.calculate_trade_charges(
                    segment=segment,
                    buy_qty=fill_qty,
                    buy_price=buy_price,
                    sell_qty=fill_qty,
                    sell_price=sell_price
                )
                net_pnl = gross_pnl - charges.total_charges

                # Duration
                try:
                    t1 = datetime.strptime(open_dt, "%Y-%m-%d %H:%M:%S")
                    t2 = datetime.strptime(close_dt, "%Y-%m-%d %H:%M:%S")
                    duration_mins = max(1, int((t2 - t1).total_seconds() / 60))
                except Exception:
                    duration_mins = 15

                round_trip_trade = {
                    "id": f"TR-{len(round_trips)+1:05d}",
                    "symbol": sym,
                    "segment": segment,
                    "instrument_type": inst_type,
                    "strike_price": strike,
                    "option_type": opt_type,
                    "direction": direction,
                    "quantity": fill_qty,
                    "entry_price": buy_price if direction == "LONG" else sell_price,
                    "exit_price": sell_price if direction == "LONG" else buy_price,
                    "open_date": open_dt,
                    "close_date": close_dt,
                    "trade_date": date_only,
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
                    "is_win": net_pnl > 0,
                    "strategy_tag": default_strategy,
                    "assumptions": charges.assumptions_disclosed
                }
                round_trips.append(round_trip_trade)

                qty -= fill_qty
                opp["quantity"] -= fill_qty
                if opp["quantity"] <= 0:
                    open_positions[sym].pop(0)

            # If leftover quantity, add to open_positions
            if qty > 0:
                open_positions[sym].append({
                    "action": action,
                    "quantity": qty,
                    "price": price,
                    "datetime": dt_str,
                    "segment": segment
                })

        # Leftovers are unmatched positions
        unmatched = []
        for sym, lots in open_positions.items():
            for lot in lots:
                unmatched.append({
                    "symbol": sym,
                    "action": lot["action"],
                    "quantity": lot["quantity"],
                    "price": lot["price"],
                    "date": lot["datetime"]
                })

        return round_trips, unmatched

    def _process_direct_roundtrip_df(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Directly ingests a file that already has calculated trades.
        """
        trades = []
        for idx, row in df.iterrows():
            gross = float(row.get("gross_pnl", 0.0))
            net = float(row.get("net_pnl", gross))
            charges = float(row.get("total_charges", gross - net))
            sym = str(row.get("symbol", "NIFTY"))
            trades.append({
                "id": f"TR-{idx+1:05d}",
                "symbol": sym,
                "segment": str(row.get("segment", "OPTIONS")),
                "instrument_type": str(row.get("instrument_type", "OPTION")),
                "direction": str(row.get("direction", "LONG")),
                "quantity": int(row.get("quantity", 50)),
                "entry_price": float(row.get("entry_price", 100)),
                "exit_price": float(row.get("exit_price", 110)),
                "open_date": str(row.get("open_date", "2026-10-01 09:20:00")),
                "close_date": str(row.get("close_date", "2026-10-01 09:45:00")),
                "trade_date": str(row.get("trade_date", str(row.get("close_date", ""))[:10])),
                "duration_minutes": int(row.get("duration_minutes", 25)),
                "gross_pnl": round(gross, 2),
                "net_pnl": round(net, 2),
                "total_charges": round(charges, 2),
                "brokerage": float(row.get("brokerage", 40.0)),
                "stt_ctt": float(row.get("stt_ctt", charges * 0.2)),
                "exchange_charges": float(row.get("exchange_charges", charges * 0.1)),
                "gst": float(row.get("gst", charges * 0.15)),
                "sebi_charges": float(row.get("sebi_charges", 0.1)),
                "stamp_duty": float(row.get("stamp_duty", 0.5)),
                "is_win": net > 0,
                "strategy_tag": str(row.get("strategy_tag", "Discretionary"))
            })

        return {
            "success": True,
            "detected_format": "tradelens_direct",
            "executions_count": len(trades) * 2,
            "matched_roundtrips_count": len(trades),
            "unmatched_executions_count": 0,
            "trades": trades,
            "errors": []
        }

parser = TradeParser()
