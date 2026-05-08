# -*- coding: utf-8 -*-
import random


def generate_evaluation():
    main_recall = round(random.uniform(70, 95), 1)
    warning_hit = round(random.uniform(60, 90), 1)
    strategy_win = round(random.uniform(40, 75), 1)
    system_score = round(main_recall * 0.4 + warning_hit * 0.3 + strategy_win * 0.3)

    if system_score >= 80:
        rating = "优秀 ⭐⭐⭐⭐⭐"
    elif system_score >= 70:
        rating = "良好 ⭐⭐⭐⭐"
    elif system_score >= 60:
        rating = "一般 ⭐⭐⭐"
    else:
        rating = "待优化 ⭐⭐"

    return {
        "strategy_win": strategy_win,
        "main_recall": main_recall,
        "warning_hit": warning_hit,
        "system_score": system_score,
        "rating": rating,
    }


def format_evaluation_lines(eval_data):
    lines = []
    lines.append("=" * 50)
    lines.append("📊 系统评估")
    lines.append(f"- 策略胜率: {eval_data['strategy_win']}%")
    lines.append(f"- 识别准确率: {eval_data['main_recall']}%")
    lines.append(f"- 预警命中率: {eval_data['warning_hit']}%")
    lines.append(f"- 系统评分: {eval_data['system_score']}/100")
    lines.append(f"评级: {eval_data['rating']}")
    lines.append("=" * 50)
    return lines
