"""
TradeLens AI - Trading Behavioral Insights & Tilt Detection Engine
Quantifies psychological leaks: Overtrading, Revenge Trading, Tilt Index,
Consecutive Loss Streaks, and Asymmetric Holding Biases.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

class BehaviorEngine:
    """
    Analyzes trader execution psychology and detects behavioral anomalies.
    """
    @staticmethod
    def analyze_behavior(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not trades or len(trades) < 2:
            return BehaviorEngine._default_behavior()

        df = pd.DataFrame(trades)
        for col in ['net_pnl', 'gross_pnl', 'total_charges', 'quantity', 'duration_minutes']:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # 1. Winning Days vs Losing Days Overtrading
        if 'trade_date' in df.columns:
            df['date_key'] = df['trade_date'].astype(str).str[:10]
        else:
            df['date_key'] = df['open_date'].astype(str).str[:10]

        daily_groups = df.groupby('date_key').agg(
            trades_count=('id', 'count'),
            net_pnl=('net_pnl', 'sum'),
            gross_pnl=('gross_pnl', 'sum'),
            charges=('total_charges', 'sum')
        ).reset_index()

        green_days = daily_groups[daily_groups['net_pnl'] > 0]
        red_days = daily_groups[daily_groups['net_pnl'] < 0]

        avg_trades_green_day = round(float(green_days['trades_count'].mean()), 1) if len(green_days) > 0 else 0.0
        avg_trades_red_day = round(float(red_days['trades_count'].mean()), 1) if len(red_days) > 0 else 0.0

        overtrading_ratio = round(avg_trades_red_day / avg_trades_green_day, 2) if avg_trades_green_day > 0 else 1.0

        # 2. Consecutive Losses & Sizing Escalation
        consecutive_losses = 0
        max_consecutive_losses = 0
        current_streak = 0
        max_streak_loss_amount = 0.0
        current_streak_loss = 0.0

        consecutive_wins = 0
        max_consecutive_wins = 0
        current_win_streak = 0

        # Sort chronologically
        if 'open_date' in df.columns:
            df = df.sort_values(by='open_date').reset_index(drop=True)

        for _, r in df.iterrows():
            pnl = float(r['net_pnl'])
            if pnl < 0:
                current_streak += 1
                current_streak_loss += abs(pnl)
                if current_streak > max_consecutive_losses:
                    max_consecutive_losses = current_streak
                    max_streak_loss_amount = current_streak_loss
                current_win_streak = 0
            elif pnl > 0:
                current_win_streak += 1
                if current_win_streak > max_consecutive_wins:
                    max_consecutive_wins = current_win_streak
                current_streak = 0
                current_streak_loss = 0.0
            else:
                current_streak = 0
                current_win_streak = 0

        # Sizing escalation after loss (Martingale tendency)
        size_escalation_detected = False
        escalation_events = 0
        for i in range(1, len(df)):
            prev_pnl = float(df.iloc[i-1]['net_pnl'])
            prev_qty = float(df.iloc[i-1]['quantity'])
            curr_qty = float(df.iloc[i]['quantity'])
            if prev_pnl < 0 and curr_qty >= (prev_qty * 1.5):
                escalation_events += 1

        if escalation_events >= 2:
            size_escalation_detected = True

        # 3. Holding Time Asymmetry (Cutting winners fast vs holding losers)
        winners = df[df['net_pnl'] > 0]
        losers = df[df['net_pnl'] < 0]

        avg_winner_duration = round(float(winners['duration_minutes'].mean()), 1) if len(winners) > 0 and 'duration_minutes' in winners.columns else 20.0
        avg_loser_duration = round(float(losers['duration_minutes'].mean()), 1) if len(losers) > 0 and 'duration_minutes' in losers.columns else 45.0

        holding_asymmetry_ratio = round(avg_loser_duration / avg_winner_duration, 2) if avg_winner_duration > 0 else 1.0

        # 4. Outlier Blunder Concentration (Worst 5% of trades vs total losses)
        total_loss_sum = abs(float(losers['net_pnl'].sum())) if len(losers) > 0 else 0.0
        worst_loss = abs(float(df['net_pnl'].min())) if len(df) > 0 else 0.0

        sorted_losses = losers.sort_values(by='net_pnl', ascending=True)
        top_5_pct_count = max(1, int(len(sorted_losses) * 0.1)) # top 10% worst
        worst_cluster_sum = abs(float(sorted_losses.head(top_5_pct_count)['net_pnl'].sum())) if len(sorted_losses) > 0 else 0.0
        blunder_share_pct = round((worst_cluster_sum / total_loss_sum * 100), 1) if total_loss_sum > 0 else 0.0

        # 5. Discipline & Tilt Score Calculation (0 to 100)
        # Base score 100, deduct penalties for psychological leaks
        tilt_score = 100

        # Penalty 1: Revenge overtrading on red days
        if overtrading_ratio > 2.5:
            tilt_score -= 25
        elif overtrading_ratio > 1.7:
            tilt_score -= 15
        elif overtrading_ratio > 1.3:
            tilt_score -= 8

        # Penalty 2: Asymmetric holding (losers held > 2x longer than winners)
        if holding_asymmetry_ratio > 2.2:
            tilt_score -= 20
        elif holding_asymmetry_ratio > 1.5:
            tilt_score -= 10

        # Penalty 3: Sizing escalation after losses
        if size_escalation_detected:
            tilt_score -= 15

        # Penalty 4: Consecutive losses > 4
        if max_consecutive_losses >= 6:
            tilt_score -= 15
        elif max_consecutive_losses >= 4:
            tilt_score -= 8

        # Penalty 5: Blunder concentration > 50%
        if blunder_share_pct > 60:
            tilt_score -= 15
        elif blunder_share_pct > 40:
            tilt_score -= 8

        tilt_score = max(20, min(100, tilt_score))

        # Tilt state badge
        if tilt_score >= 82:
            discipline_level = "Disciplined & Composed"
            discipline_color = "emerald"
        elif tilt_score >= 68:
            discipline_level = "Moderate Discipline (Occasional Tilt)"
            discipline_color = "amber"
        elif tilt_score >= 50:
            discipline_level = "Vulnerable to Tilt"
            discipline_color = "orange"
        else:
            discipline_level = "High Emotional Tilt & Revenge Risk"
            discipline_color = "rose"

        # Diagnostic Behavioral Flags
        flags = []
        if overtrading_ratio >= 1.6:
            flags.append({
                "type": "REVENGE_OVERTRADING",
                "severity": "CRITICAL" if overtrading_ratio > 2.2 else "WARNING",
                "title": "Loss-Triggered Overtrading",
                "detail": f"You execute {overtrading_ratio}x more trades on red days ({avg_trades_red_day} trades/day) compared to green days ({avg_trades_green_day} trades/day)."
            })

        if holding_asymmetry_ratio >= 1.5:
            flags.append({
                "type": "ASYMMETRIC_HOLDING",
                "severity": "WARNING",
                "title": "Disposition Effect (Holding Losers)",
                "detail": f"You hold losing positions for an average of {avg_loser_duration} mins vs only {avg_winner_duration} mins for winning trades ({holding_asymmetry_ratio}x longer)."
            })

        if size_escalation_detected:
            flags.append({
                "type": "MARTINGALE_SIZING",
                "severity": "CRITICAL",
                "title": "Aggressive Position Sizing After Losses",
                "detail": f"Detected {escalation_events} occurrences of doubling/escalating lot size immediately following a loss."
            })

        if blunder_share_pct >= 45:
            flags.append({
                "type": "BLUNDER_CONCENTRATION",
                "severity": "CRITICAL",
                "title": "Catastrophic Tail Risk",
                "detail": f"Your worst {top_5_pct_count} losing trade(s) accounted for {blunder_share_pct}% of your total trading losses (₹{worst_cluster_sum:,.2f})."
            })

        if max_consecutive_losses >= 4:
            flags.append({
                "type": "LOSS_SPIRAL",
                "severity": "WARNING",
                "title": f"Extended Drawdown Streak ({max_consecutive_losses} Losses)",
                "detail": f"Peak consecutive losing streak reached {max_consecutive_losses} trades, draining ₹{max_streak_loss_amount:,.2f} in continuous losses."
            })

        return {
            "discipline_score": tilt_score,
            "discipline_level": discipline_level,
            "discipline_color": discipline_color,
            "overtrading_ratio": overtrading_ratio,
            "avg_trades_green_day": avg_trades_green_day,
            "avg_trades_red_day": avg_trades_red_day,
            "max_consecutive_losses": max_consecutive_losses,
            "max_consecutive_wins": max_consecutive_wins,
            "max_streak_loss_amount": round(max_streak_loss_amount, 2),
            "size_escalation_detected": size_escalation_detected,
            "escalation_events": escalation_events,
            "avg_winner_duration_mins": avg_winner_duration,
            "avg_loser_duration_mins": avg_loser_duration,
            "holding_asymmetry_ratio": holding_asymmetry_ratio,
            "blunder_share_pct": blunder_share_pct,
            "worst_single_loss": round(worst_loss, 2),
            "behavioral_flags": flags
        }

    @staticmethod
    def _default_behavior() -> Dict[str, Any]:
        return {
            "discipline_score": 85,
            "discipline_level": "Baseline / Insufficient Data",
            "discipline_color": "blue",
            "overtrading_ratio": 1.0,
            "avg_trades_green_day": 0.0,
            "avg_trades_red_day": 0.0,
            "max_consecutive_losses": 0,
            "max_consecutive_wins": 0,
            "max_streak_loss_amount": 0.0,
            "size_escalation_detected": False,
            "escalation_events": 0,
            "avg_winner_duration_mins": 0.0,
            "avg_loser_duration_mins": 0.0,
            "holding_asymmetry_ratio": 1.0,
            "blunder_share_pct": 0.0,
            "worst_single_loss": 0.0,
            "behavioral_flags": []
        }

behavior = BehaviorEngine()
