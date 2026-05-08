# -*- coding: utf-8 -*-
import os
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")
os.makedirs("data", exist_ok=True)

from src.data.access import get_latest_result, save_latest_result, append_history
from src.analysis.core import (
    get_market_judge_data,
    analyze_risk_sources,
    run_analysis_core,
)

if __name__ == "__main__":
    print("开始自动分析...")

    try:
        result = run_analysis_core()

        judge_data = get_market_judge_data()
        result.update(judge_data)

        risk_sources = analyze_risk_sources()
        result["risk_sources"] = risk_sources

        save_latest_result(result)

        append_history(
            {
                "date": result.get("date", ""),
                "market_state": result.get("market_state", ""),
                "main_sector": ", ".join(result.get("main_sectors", [])[:3]) if result.get("main_sectors") else "无",
                "risk_level": result.get("risk_level", ""),
                "strategy": result.get("strategy", ""),
                "position": result.get("position", ""),
                "score": result.get("score", 0),
            }
        )

        print(
            f"分析完成: {result.get('date')} - {result.get('market_state')} - {result.get('risk_level')}"
        )
        print(f"策略: {result.get('strategy')} - 仓位: {result.get('position')}")
        print(
            f"判定依据: 上涨{result.get('上涨家数', 0)}家, 下跌{result.get('下跌家数', 0)}家, 涨停{result.get('涨停数', 0)}家"
        )
        print(f"风险来源: {len(risk_sources)}项")
        print("结果已保存")
        print("Auto run completed")

    except Exception as e:
        print(f"分析失败: {str(e)}")
