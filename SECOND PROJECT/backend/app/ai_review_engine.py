"""
TradeLens AI - Grounded Trading Intelligence & Weekly Review Engine
Generates rigorous, metric-grounded trading audits and behavioral post-mortems.
Zero invented conclusions, zero guaranteed-profit claims, strict calculation separation.
Supports both native deterministic factual synthesis and optional Gemini API.
"""
import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

class AIReviewEngine:
    """
    Synthesizes calculated metrics into an executive trading review.
    Calculations and explanations are strictly decoupled.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate_review(
        self,
        metrics: Dict[str, Any],
        behavior: Dict[str, Any],
        user_name: str = "Trader"
    ) -> Dict[str, Any]:
        """
        Receives pure calculated metrics and produces a comprehensive review.
        """
        summary = metrics.get("summary", {})
        charges = metrics.get("charges_breakdown", {})
        by_weekday = metrics.get("by_weekday", [])
        by_time = metrics.get("by_time_of_day", [])
        by_segment = metrics.get("by_segment", [])

        # Step 1: Extract verified facts
        net_pnl = summary.get("net_pnl", 0.0)
        gross_pnl = summary.get("gross_pnl", 0.0)
        total_charges = summary.get("total_charges", 0.0)
        win_rate = summary.get("win_rate", 0.0)
        profit_factor = summary.get("profit_factor", 0.0)
        charge_drag = summary.get("charge_drag_pct", 0.0)
        max_drawdown = summary.get("max_drawdown_rupees", 0.0)
        total_trades = summary.get("total_trades", 0)

        discipline_score = behavior.get("discipline_score", 85)
        overtrading_ratio = behavior.get("overtrading_ratio", 1.0)
        max_loss_streak = behavior.get("max_consecutive_losses", 0)
        blunder_share = behavior.get("blunder_share_pct", 0.0)

        # Step 2: Identify Edge Leaks from Data
        edge_leaks = []
        # Check weekday leaks (e.g. Thursday or Wednesday expiry days)
        for day in by_weekday:
            if day.get("net_pnl", 0) < 0 and day.get("trades_count", 0) >= 3:
                edge_leaks.append(f"{day['category']}: Net loss of ₹{abs(day['net_pnl']):,.2f} over {day['trades_count']} trades (Win Rate: {day['win_rate']}%)")

        # Check time-of-day leaks
        for slot in by_time:
            if slot.get("net_pnl", 0) < 0 and slot.get("trades_count", 0) >= 3:
                edge_leaks.append(f"Time Window '{slot['category']}': Net loss of ₹{abs(slot['net_pnl']):,.2f} (Win Rate: {slot['win_rate']}%)")

        # Check segment leaks
        for seg in by_segment:
            if seg.get("net_pnl", 0) < 0:
                edge_leaks.append(f"Segment '{seg['category']}': Net loss of ₹{abs(seg['net_pnl']):,.2f} with charges of ₹{seg['charges']:,.2f}")

        # If no severe leaks found, highlight neutral observation
        if not edge_leaks:
            edge_leaks.append("No isolated segment or time slot generated net negative returns across the analyzed period.")

        # Step 3: Cost Drag Analysis
        cost_analysis = (
            f"Trading friction consumed ₹{total_charges:,.2f} across {total_trades} trades. "
            f"Brokerage accounted for ₹{charges.get('brokerage', 0):,.2f}, STT/CTT accounted for ₹{charges.get('stt_ctt', 0):,.2f}, "
            f"and Exchange/GST/SEBI charges totaled ₹{(charges.get('exchange_charges', 0) + charges.get('gst', 0) + charges.get('sebi_charges', 0)):,.2f}. "
        )
        if gross_pnl > 0:
            cost_analysis += f"Statutory and broker charges consumed {charge_drag}% of your gross trading profits."
        else:
            cost_analysis += f"Friction added ₹{total_charges:,.2f} in additional losses on top of gross negative returns."

        # Step 4: Grounded Actionable Directives (strictly empirical)
        directives = []
        if overtrading_ratio > 1.5:
            directives.append(
                f"Enforce Hard Daily Trade Caps: Your trading frequency spikes {overtrading_ratio}x on losing days. Implement a mandatory stop rule after 2 consecutive losses."
            )
        if blunder_share > 35:
            directives.append(
                f"Cap Maximum Loss per Trade: The top worst trades accounted for {blunder_share}% of all your losses. Use fixed-rupee stop losses at entry."
            )
        if charge_drag > 25:
            directives.append(
                f"Eliminate Low-Conviction Scalps: Friction is eating {charge_drag}% of gross gains. Filter out trades with target risk-to-reward below 1:2 to ensure edge exceeds statutory costs."
            )
        if not directives:
            directives.append("Maintain disciplined trade pacing and continue logging strategy tags for all executions.")

        # If user has configured Gemini API key, attempt live AI synthesis
        if self.api_key:
            try:
                gemini_review = self._call_gemini_api(
                    metrics=summary,
                    behavior=behavior,
                    edge_leaks=edge_leaks,
                    cost_analysis=cost_analysis,
                    directives=directives
                )
                if gemini_review:
                    return gemini_review
            except Exception as e:
                # Silently fallback to deterministic synthesis if API fails or is quota-limited
                pass

        # Built-in Institutional Deterministic Synthesis (Grounded & 100% Reliable)
        pnl_status = "profitable" if net_pnl >= 0 else "unprofitable"
        executive_summary = (
            f"Performance Audit for {total_trades} trades ({summary.get('trading_days', 0)} active trading days). "
            f"Your trading operations resulted in a gross P&L of ₹{gross_pnl:,.2f} and a net P&L of ₹{net_pnl:,.2f} after ₹{total_charges:,.2f} in statutory and broker charges. "
            f"Overall win rate stands at {win_rate}% with a Profit Factor of {profit_factor} and Maximum Drawdown of ₹{max_drawdown:,.2f} ({summary.get('max_drawdown_pct', 0)}%). "
            f"Behavioral discipline index is rated at {discipline_score}/100 ({behavior.get('discipline_level', 'Active')})."
        )

        behavioral_flags = [f["title"] for f in behavior.get("behavioral_flags", [])]

        return {
            "source": "Grounded Deterministic Engine (Zero Hallucination)",
            "requires_api_key": False,
            "api_key_configured": bool(self.api_key),
            "discipline_score": discipline_score,
            "executive_summary": executive_summary,
            "edge_leak_diagnosis": edge_leaks[:3],
            "cost_drag_analysis": cost_analysis,
            "behavioral_audit": {
                "overtrading_multiplier": overtrading_ratio,
                "max_loss_streak": max_loss_streak,
                "blunder_concentration_pct": blunder_share,
                "flags": behavioral_flags
            },
            "actionable_directives": directives,
            "disclaimer": "This review is purely quantitative and diagnostic, derived from verified historical trade logs. TradeLens AI does not provide financial advice, tips, or profit guarantees."
        }

    def _call_gemini_api(
        self,
        metrics: Dict[str, Any],
        behavior: Dict[str, Any],
        edge_leaks: List[str],
        cost_analysis: str,
        directives: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Calls Google Gemini API with strictly constrained prompt grounding.
        """
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        system_instruction = (
            "You are TradeLens AI, an institutional quantitative trading risk auditor for Indian stock and F&O markets. "
            "You are given strictly calculated mathematical facts. DO NOT hallucinate, DO NOT invent facts, DO NOT recommend specific stocks to buy, "
            "and DO NOT make profit promises or guarantees. Ground every insight in the exact numbers provided. "
            "Output your answer in clean JSON format matching the schema."
        )

        prompt_data = {
            "summary_metrics": metrics,
            "behavioral_metrics": behavior,
            "verified_edge_leaks": edge_leaks,
            "verified_cost_analysis": cost_analysis,
            "recommended_directives": directives
        }

        user_content = f"Analyze these trading performance metrics:\n{json.dumps(prompt_data, indent=2)}\nProvide a rigorous trading critique in JSON with keys: executive_summary, edge_leak_diagnosis (list of strings), cost_drag_analysis, actionable_directives (list of strings)."

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_instruction}\n\n{user_content}"}]}
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                resp_json = json.loads(response.read().decode("utf-8"))
                text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                return {
                    "source": "Gemini 1.5 Grounded Engine",
                    "requires_api_key": True,
                    "api_key_configured": True,
                    "discipline_score": behavior.get("discipline_score", 85),
                    "executive_summary": parsed.get("executive_summary", ""),
                    "edge_leak_diagnosis": parsed.get("edge_leak_diagnosis", edge_leaks),
                    "cost_drag_analysis": parsed.get("cost_drag_analysis", cost_analysis),
                    "behavioral_audit": {
                        "overtrading_multiplier": behavior.get("overtrading_ratio", 1.0),
                        "max_loss_streak": behavior.get("max_consecutive_losses", 0),
                        "blunder_concentration_pct": behavior.get("blunder_share_pct", 0.0),
                        "flags": [f["title"] for f in behavior.get("behavioral_flags", [])]
                    },
                    "actionable_directives": parsed.get("actionable_directives", directives),
                    "disclaimer": "This review is grounded strictly in historical trade data. TradeLens AI does not provide financial advice or profit guarantees."
                }
        return None

ai_review = AIReviewEngine()
