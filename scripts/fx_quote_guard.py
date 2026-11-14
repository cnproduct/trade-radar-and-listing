#!/usr/bin/env python3
"""Deterministic FX settlement rate tracker, delta monitor, and export quote safety-cushion calculator."""

import argparse
import csv
import datetime as dt
import json
import os
from typing import Any, Dict, List, Optional


FX_FIELDS = ["date", "pair", "rate", "baseline_rate", "delta_vs_prev_pct", "delta_vs_base_pct", "status"]


def load_last_rate(history_file: str, pair: str) -> Optional[float]:
    if not os.path.exists(history_file):
        return None
    last_val: Optional[float] = None
    with open(history_file, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("pair", "").upper() == pair.upper():
                try:
                    last_val = float(row["rate"])
                except (KeyError, ValueError):
                    pass
    return last_val


def evaluate_fx(
    pair: str,
    current_rate: float,
    baseline_rate: float,
    gross_margin: float,
    alert_threshold_pct: float,
    history_file: str,
    record_date: str = "",
) -> Dict[str, Any]:
    if current_rate <= 0 or baseline_rate <= 0:
        raise ValueError("汇率必须大于 0")

    today_str = record_date or dt.date.today().isoformat()
    prev_rate = load_last_rate(history_file, pair)

    delta_prev_pct = ((current_rate - prev_rate) / prev_rate * 100.0) if prev_rate else 0.0
    delta_base_pct = (current_rate - baseline_rate) / baseline_rate * 100.0

    # Assume export settlement: 1 Foreign Currency = rate * Local Currency (e.g. USD/CNY).
    # Original cost in CNY for $1 quote = baseline_rate * (1 - gross_margin).
    # New settled CNY for $1 quote = current_rate.
    cny_cost_per_fx_unit = baseline_rate * (1.0 - gross_margin)
    new_margin = (current_rate - cny_cost_per_fx_unit) / current_rate
    margin_shift_pct_pts = (new_margin - gross_margin) * 100.0

    # Required foreign-currency price multiplier to restore original gross margin
    reprice_multiplier = baseline_rate / current_rate
    required_price_adj_pct = (reprice_multiplier - 1.0) * 100.0

    if delta_base_pct <= -abs(alert_threshold_pct):
        status = "ALERT_MARGIN_EROSION"
        advice = (
            f"结汇牌价较核价基准下跌 {abs(delta_base_pct):.2f}%（外币贬值/本币升值），"
            f"实际毛利率从 {gross_margin*100:.1f}% 被压缩至 {new_margin*100:.2f}%。"
            f"建议新发报价上调外币单价约 {required_price_adj_pct:.2f}%，并将报价有效期缩短至 7 天内。"
        )
    elif delta_base_pct >= abs(alert_threshold_pct):
        status = "FAVORABLE_WINDOW"
        advice = (
            f"结汇牌价较核价基准上涨 {delta_base_pct:.2f}%（外币升值汇兑增厚），"
            f"实际毛利率提升至 {new_margin*100:.2f}%。"
            f"可利用此约 {abs(required_price_adj_pct):.2f}% 的汇率空间给重点观望客户做限时锁单让利促成交。"
        )
    else:
        status = "SAFE_BAND"
        advice = "汇率波动处于安全缓冲垫内，现有对外报价单可维持不变。"

    parent = os.path.dirname(os.path.abspath(history_file))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    exists = os.path.exists(history_file)
    with open(history_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FX_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({
            "date": today_str,
            "pair": pair.upper(),
            "rate": f"{current_rate:.4f}",
            "baseline_rate": f"{baseline_rate:.4f}",
            "delta_vs_prev_pct": f"{delta_prev_pct:.3f}",
            "delta_vs_base_pct": f"{delta_base_pct:.3f}",
            "status": status,
        })

    return {
        "date": today_str,
        "pair": pair.upper(),
        "current_rate": round(current_rate, 4),
        "previous_logged_rate": round(prev_rate, 4) if prev_rate else None,
        "baseline_quote_rate": round(baseline_rate, 4),
        "delta_vs_prev_pct": round(delta_prev_pct, 3),
        "delta_vs_base_pct": round(delta_base_pct, 3),
        "original_gross_margin_pct": round(gross_margin * 100.0, 2),
        "effective_gross_margin_pct": round(new_margin * 100.0, 2),
        "margin_change_pct_pts": round(margin_shift_pct_pts, 2),
        "suggested_fx_price_adjustment_pct": round(required_price_adj_pct, 2),
        "status": status,
        "action_advice": advice,
    }


def format_markdown(res: Dict[str, Any]) -> str:
    prev_txt = f"{res['previous_logged_rate']:.4f} ({res['delta_vs_prev_pct']:+.2f}%)" if res["previous_logged_rate"] else "首次记录"
    return "\n".join([
        f"### 结汇汇率监测与报价预警卡（{res['pair']} | {res['date']}）",
        "",
        f"- **当前最新牌价**: {res['current_rate']:.4f}（较上次记录：{prev_txt}）",
        f"- **报价核算基准汇率**: {res['baseline_quote_rate']:.4f}（累计偏离：{res['delta_vs_base_pct']:+.2f}%）",
        f"- **毛利率影响测算**: 原定 {res['original_gross_margin_pct']:.1f}% -> 当前实际 {res['effective_gross_margin_pct']:.2f}%（变动 {res['margin_change_pct_pts']:+.2f} 个百分点）",
        f"- **调价与跟单建议**: {res['action_advice']}",
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="外贸结汇汇率涨跌记录与报价安全垫测算工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_chk = sub.add_parser("check")
    p_chk.add_argument("--pair", default="USD/CNY")
    p_chk.add_argument("--current-rate", type=float, required=True)
    p_chk.add_argument("--baseline-rate", type=float, required=True)
    p_chk.add_argument("--gross-margin", type=float, default=0.15)
    p_chk.add_argument("--alert-threshold-pct", type=float, default=1.0)
    p_chk.add_argument("--history-file", default="./fx_history.csv")
    p_chk.add_argument("--date", default="")
    p_chk.add_argument("--markdown", action="store_true")

    args = parser.parse_args()
    if args.cmd == "check":
        res = evaluate_fx(
            args.pair, args.current_rate, args.baseline_rate,
            args.gross_margin, args.alert_threshold_pct, args.history_file, args.date
        )
        if args.markdown:
            print(format_markdown(res))
        else:
            print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
