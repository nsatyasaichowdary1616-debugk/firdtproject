"""
TradeLens AI - Institutional Quant Analytics Engine
Performs rigorous financial metrics calculation using Pandas.
Includes Drawdown, Expectancy, Profit Factor, Calendar aggregation, and multi-slice breakdowns.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

class AnalyticsEngine:
    """
    Computes institutional trading performance analytics from a list of matched round-trip trades.
    """
    @staticmethod
    def calculate_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not trades:
            return AnalyticsEngine._empty_metrics()

        df = pd.DataFrame(trades)
        
        # Ensure numeric fields
        for col in ['gross_pnl', 'net_pnl', 'total_charges', 'brokerage', 'stt_ctt', 'exchange_charges', 'gst', 'sebi_charges', 'stamp_duty', 'turnover', 'quantity', 'entry_price', 'exit_price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        total_trades = len(df)
        winning_trades = df[df['net_pnl'] > 0]
        losing_trades = df[df['net_pnl'] < 0]
        breakeven_trades = df[df['net_pnl'] == 0]

        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        breakeven_count = len(breakeven_trades)

        win_rate = round((win_count / total_trades) * 100, 2) if total_trades > 0 else 0.0

        gross_pnl = float(df['gross_pnl'].sum())
        total_charges = float(df['total_charges'].sum())
        net_pnl = float(df['net_pnl'].sum())
        total_turnover = float(df['turnover'].sum()) if 'turnover' in df.columns else 0.0

        # Itemized charges sum
        brokerage_sum = float(df['brokerage'].sum()) if 'brokerage' in df.columns else 0.0
        stt_sum = float(df['stt_ctt'].sum()) if 'stt_ctt' in df.columns else 0.0
        exch_sum = float(df['exchange_charges'].sum()) if 'exchange_charges' in df.columns else 0.0
        gst_sum = float(df['gst'].sum()) if 'gst' in df.columns else 0.0
        sebi_sum = float(df['sebi_charges'].sum()) if 'sebi_charges' in df.columns else 0.0
        stamp_sum = float(df['stamp_duty'].sum()) if 'stamp_duty' in df.columns else 0.0

        # Charge Drag: % of gross profit eaten by charges
        gross_wins_sum = float(winning_trades['gross_pnl'].sum()) if len(winning_trades) > 0 else 0.0
        gross_losses_sum = abs(float(losing_trades['gross_pnl'].sum())) if len(losing_trades) > 0 else 0.0

        charge_drag_pct = round((total_charges / gross_wins_sum * 100), 2) if gross_wins_sum > 0 else 0.0
        net_wins_sum = float(winning_trades['net_pnl'].sum()) if len(winning_trades) > 0 else 0.0
        net_losses_sum = abs(float(losing_trades['net_pnl'].sum())) if len(losing_trades) > 0 else 0.0

        # Profit Factor: Gross Wins / Gross Losses
        profit_factor = round(gross_wins_sum / gross_losses_sum, 2) if gross_losses_sum > 0 else (999.0 if gross_wins_sum > 0 else 0.0)

        # Average win and average loss
        avg_win = round(net_wins_sum / win_count, 2) if win_count > 0 else 0.0
        avg_loss = round(net_losses_sum / loss_count, 2) if loss_count > 0 else 0.0
        win_loss_ratio = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0.0

        # Expectancy: (Win% * AvgWin) - (Loss% * AvgLoss)
        win_prob = win_count / total_trades if total_trades > 0 else 0
        loss_prob = loss_count / total_trades if total_trades > 0 else 0
        expectancy = round((win_prob * avg_win) - (loss_prob * avg_loss), 2)

        # Largest Win and Loss
        largest_win = float(df['net_pnl'].max()) if total_trades > 0 else 0.0
        largest_loss = float(df['net_pnl'].min()) if total_trades > 0 else 0.0

        # Equity Curve and Drawdown Analysis
        # Ensure chronological ordering
        if 'close_date' in df.columns:
            df['sort_date'] = pd.to_datetime(df['close_date'], errors='coerce')
        elif 'trade_date' in df.columns:
            df['sort_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
        else:
            df['sort_date'] = pd.to_datetime('2026-01-01')

        df = df.sort_values(by='sort_date').reset_index(drop=True)

        df['cum_gross_pnl'] = df['gross_pnl'].cumsum()
        df['cum_net_pnl'] = df['net_pnl'].cumsum()
        df['cum_charges'] = df['total_charges'].cumsum()

        # Net Peak and Drawdown
        df['peak_net'] = df['cum_net_pnl'].cummax()
        # Drawdown in absolute rupees
        df['drawdown_rupees'] = df['cum_net_pnl'] - df['peak_net']
        
        # Max Drawdown
        max_drawdown_rupees = abs(float(df['drawdown_rupees'].min())) if total_trades > 0 else 0.0
        current_drawdown_rupees = abs(float(df['drawdown_rupees'].iloc[-1])) if total_trades > 0 else 0.0

        # Max drawdown as % of peak capital (assuming baseline ₹2,00,000 capital or peak equity)
        baseline_capital = 200000.0
        df['capital_curve'] = baseline_capital + df['cum_net_pnl']
        df['capital_peak'] = df['capital_curve'].cummax()
        df['drawdown_pct'] = ((df['capital_curve'] - df['capital_peak']) / df['capital_peak']) * 100
        max_drawdown_pct = abs(round(float(df['drawdown_pct'].min()), 2)) if total_trades > 0 else 0.0

        # Equity curve timeline (points for chart)
        equity_curve = []
        for idx, r in df.iterrows():
            d_label = str(r['close_date']) if pd.notnull(r.get('close_date')) else str(r['trade_date'])
            equity_curve.append({
                "trade_index": idx + 1,
                "date": d_label[:16],
                "symbol": r.get('symbol', ''),
                "trade_net": round(float(r['net_pnl']), 2),
                "cum_gross_pnl": round(float(r['cum_gross_pnl']), 2),
                "cum_net_pnl": round(float(r['cum_net_pnl']), 2),
                "cum_charges": round(float(r['cum_charges']), 2),
                "drawdown": round(float(r['drawdown_rupees']), 2),
                "drawdown_pct": round(float(r['drawdown_pct']), 2)
            })

        # Breakdown by Instrument Segment
        segment_breakdown = AnalyticsEngine._slice_breakdown(df, 'segment')
        strategy_breakdown = AnalyticsEngine._slice_breakdown(df, 'strategy_tag')
        direction_breakdown = AnalyticsEngine._slice_breakdown(df, 'direction')

        # Day of Week Breakdown
        df['day_name'] = df['sort_date'].dt.day_name()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        weekday_breakdown = AnalyticsEngine._slice_breakdown(df, 'day_name', order=weekday_order)

        # Time of Day Breakdown
        def categorize_time(dt):
            if pd.isnull(dt):
                return "10:00 - 11:30 (Morning)"
            hour = dt.hour
            minute = dt.minute
            time_val = hour * 60 + minute
            if time_val < 600: # Before 10:00
                return "09:15 - 10:00 (Market Open)"
            elif time_val < 690: # Before 11:30
                return "10:00 - 11:30 (Morning Trend)"
            elif time_val < 810: # Before 13:30
                return "11:30 - 13:30 (Lunch / Chop)"
            elif time_val < 900: # Before 15:00
                return "13:30 - 15:00 (Afternoon Move)"
            else:
                return "15:00 - 15:30 (Closing Flush)"

        df['time_slot'] = df['sort_date'].apply(categorize_time)
        time_slot_order = [
            "09:15 - 10:00 (Market Open)",
            "10:00 - 11:30 (Morning Trend)",
            "11:30 - 13:30 (Lunch / Chop)",
            "13:30 - 15:00 (Afternoon Move)",
            "15:00 - 15:30 (Closing Flush)"
        ]
        time_breakdown = AnalyticsEngine._slice_breakdown(df, 'time_slot', order=time_slot_order)

        # Calendar Matrix (by Date)
        df['date_key'] = df['sort_date'].dt.strftime('%Y-%m-%d')
        daily_summary = df.groupby('date_key').agg(
            trades_count=('id', 'count'),
            gross_pnl=('gross_pnl', 'sum'),
            net_pnl=('net_pnl', 'sum'),
            charges=('total_charges', 'sum'),
            wins=('net_pnl', lambda x: (x > 0).sum()),
            losses=('net_pnl', lambda x: (x < 0).sum())
        ).reset_index()

        daily_summary['win_rate'] = (daily_summary['wins'] / daily_summary['trades_count'] * 100).round(1)
        daily_summary = daily_summary.round(2)
        calendar_days = daily_summary.to_dict(orient='records')

        trading_days_count = len(daily_summary)
        profitable_days = len(daily_summary[daily_summary['net_pnl'] > 0])
        losing_days = len(daily_summary[daily_summary['net_pnl'] < 0])
        day_win_rate = round((profitable_days / trading_days_count * 100), 2) if trading_days_count > 0 else 0.0

        return {
            "summary": {
                "total_trades": total_trades,
                "winning_trades": win_count,
                "losing_trades": loss_count,
                "breakeven_trades": breakeven_count,
                "win_rate": win_rate,
                "gross_pnl": round(gross_pnl, 2),
                "total_charges": round(total_charges, 2),
                "net_pnl": round(net_pnl, 2),
                "turnover": round(total_turnover, 2),
                "profit_factor": profit_factor,
                "average_win": avg_win,
                "average_loss": avg_loss,
                "win_loss_ratio": win_loss_ratio,
                "expectancy": expectancy,
                "charge_drag_pct": charge_drag_pct,
                "max_drawdown_rupees": round(max_drawdown_rupees, 2),
                "max_drawdown_pct": max_drawdown_pct,
                "current_drawdown_rupees": round(current_drawdown_rupees, 2),
                "largest_win": round(largest_win, 2),
                "largest_loss": round(largest_loss, 2),
                "trading_days": trading_days_count,
                "profitable_days": profitable_days,
                "losing_days": losing_days,
                "day_win_rate": day_win_rate,
                "avg_trades_per_day": round(total_trades / trading_days_count, 1) if trading_days_count > 0 else 0
            },
            "charges_breakdown": {
                "brokerage": round(brokerage_sum, 2),
                "stt_ctt": round(stt_sum, 2),
                "exchange_charges": round(exch_sum, 2),
                "gst": round(gst_sum, 2),
                "sebi_charges": round(sebi_sum, 2),
                "stamp_duty": round(stamp_sum, 2),
                "total": round(total_charges, 2)
            },
            "equity_curve": equity_curve,
            "calendar_days": calendar_days,
            "by_segment": segment_breakdown,
            "by_strategy": strategy_breakdown,
            "by_direction": direction_breakdown,
            "by_weekday": weekday_breakdown,
            "by_time_of_day": time_breakdown
        }

    @staticmethod
    def _slice_breakdown(df: pd.DataFrame, group_col: str, order: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if group_col not in df.columns:
            return []

        grouped = df.groupby(group_col).agg(
            trades_count=('id', 'count'),
            gross_pnl=('gross_pnl', 'sum'),
            net_pnl=('net_pnl', 'sum'),
            charges=('total_charges', 'sum'),
            wins=('net_pnl', lambda x: (x > 0).sum()),
            losses=('net_pnl', lambda x: (x < 0).sum())
        ).reset_index()

        grouped['win_rate'] = (grouped['wins'] / grouped['trades_count'] * 100).round(1)
        grouped['profit_factor'] = grouped.apply(
            lambda r: round(r['gross_pnl'] / abs(r['charges'] + 1), 2) if r['gross_pnl'] > 0 else 0.0, axis=1
        )

        res = []
        records = {r[group_col]: r.to_dict() for _, r in grouped.iterrows()}

        keys = order if order else sorted(records.keys())
        for k in keys:
            if k in records:
                item = records[k]
                res.append({
                    "category": str(k),
                    "trades_count": int(item['trades_count']),
                    "gross_pnl": round(float(item['gross_pnl']), 2),
                    "charges": round(float(item['charges']), 2),
                    "net_pnl": round(float(item['net_pnl']), 2),
                    "win_rate": round(float(item['win_rate']), 1),
                    "wins": int(item['wins']),
                    "losses": int(item['losses'])
                })

        return res

    @staticmethod
    def _empty_metrics() -> Dict[str, Any]:
        return {
            "summary": {
                "total_trades": 0, "winning_trades": 0, "losing_trades": 0, "breakeven_trades": 0,
                "win_rate": 0.0, "gross_pnl": 0.0, "total_charges": 0.0, "net_pnl": 0.0, "turnover": 0.0,
                "profit_factor": 0.0, "average_win": 0.0, "average_loss": 0.0, "win_loss_ratio": 0.0,
                "expectancy": 0.0, "charge_drag_pct": 0.0, "max_drawdown_rupees": 0.0, "max_drawdown_pct": 0.0,
                "current_drawdown_rupees": 0.0, "largest_win": 0.0, "largest_loss": 0.0, "trading_days": 0,
                "profitable_days": 0, "losing_days": 0, "day_win_rate": 0.0, "avg_trades_per_day": 0.0
            },
            "charges_breakdown": {
                "brokerage": 0.0, "stt_ctt": 0.0, "exchange_charges": 0.0, "gst": 0.0,
                "sebi_charges": 0.0, "stamp_duty": 0.0, "total": 0.0
            },
            "equity_curve": [],
            "calendar_days": [],
            "by_segment": [],
            "by_strategy": [],
            "by_direction": [],
            "by_weekday": [],
            "by_time_of_day": []
        }

analytics = AnalyticsEngine()
