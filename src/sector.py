# -*- coding: utf-8 -*-
import sys
import io
import os
import shutil
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from data_loader import (
    fetch_sector_data,
    load_today_sectors,
    get_today_avg,
    load_historical_data,
    load_yesterday_sectors,
    load_prev_stage,
)
from warning import analyze_warning, calculate_risk, calculate_warning
from rotation import analyze_rotation, get_new_main_candidates
from strategy import generate_strategy, generate_trade_mode
from backtest import generate_evaluation, format_evaluation_lines
from report import generate_human_readable_reflection


def get_sector_data():
    top_10, today = fetch_sector_data()
    today_sectors = load_today_sectors(top_10)
    today_avg = get_today_avg(top_10)
    historical_data = load_historical_data()
    yesterday_sectors, yesterday_main_count = load_yesterday_sectors()
    prev_stage = load_prev_stage()

    common_sectors = set(today_sectors.keys()) & yesterday_sectors

    lines = []

    if common_sectors:
        main_sectors = common_sectors
        count = len(common_sectors)

        warning_level = analyze_warning(
            historical_data, prev_stage, count, yesterday_main_count
        )

        new_candidates = sum(
            1
            for sector in main_sectors
            if sum(1 for row in historical_data if row.get("板块名称") == sector) < 2
        )

        if historical_data:
            if new_candidates >= 3:
                warning_level = "警惕"

        confidence_score = 0
        sector_scores = {}

        if historical_data:
            all_historical_sectors = [row["板块名称"] for row in historical_data]
            sector_freq = Counter(all_historical_sectors)

            for sector in main_sectors:
                s_score = 0
                freq = sector_freq.get(sector, 0)
                s_score += min(freq * 10, 30)

                sector_change = today_sectors.get(sector, {}).get("f3", 0)
                if sector_change > today_avg:
                    s_score += 10
                if sector_change > 0:
                    s_score += 10

                rank_score = 0
                for hist_row in historical_data:
                    if hist_row["板块名称"] == sector:
                        rank = int(hist_row.get("排名", 99))
                        if rank <= 5:
                            rank_score += 10
                s_score = min(s_score + rank_score, 40)
                sector_scores[sector] = s_score

            confidence_score = (
                sum(sector_scores.values()) // len(sector_scores)
                if sector_scores
                else 0
            )
            confidence_score = min(confidence_score + 30, 100)
        else:
            confidence_score = min(count * 20 + 30, 100)
            for sector in main_sectors:
                sector_change = today_sectors.get(sector, {}).get("f3", 0)
                base_score = 20
                if sector_change > today_avg:
                    base_score += 10
                if sector_change > 0:
                    base_score += 10
                sector_scores[sector] = base_score

        is_valid_main = "是" if confidence_score >= 70 else "否"

        sentiment = (
            "情绪偏强" if count >= 3 else ("情绪中性" if count >= 1 else "情绪偏弱")
        )
        stage = (
            "主升"
            if count >= 3 and sentiment == "情绪偏强"
            else ("轮动" if count >= 1 else "混沌/退潮")
        )
        capital = "资金集中" if len(main_sectors) <= 2 else "资金分散"

        lifecycle = (
            "启动期"
            if count <= 1 and sentiment == "情绪偏强"
            else (
                "加速期"
                if stage == "主升"
                else ("分歧期" if stage == "轮动" and main_sectors else "退潮期")
            )
        )

        score = (
            min(count * 20, 60)
            + (20 if sentiment == "情绪偏强" else 0)
            + (10 if stage == "主升" else 0)
            + (10 if capital == "资金集中" else 0)
        )

        risk = calculate_risk(score, lifecycle)
        warning = calculate_warning(score, lifecycle, yesterday_main_count, count)

        strategy, position, allow_trade, advice = generate_strategy(
            stage, score, risk, lifecycle
        )

        trade_mode, reason = "轮动", "市场处于轮动状态，建议轻仓短差"

        main_status = "强" if score >= 70 else ("中" if score >= 40 else "弱")
        new_main = "有" if new_candidates >= 3 else "待观察"
        emotion_change = (
            "上升" if stage == "主升" else ("轮动" if count >= 1 else "退潮")
        )

        capital_out, capital_in, rotation_path = analyze_rotation(
            yesterday_sectors, top_10
        )

        trade_mode, reason = generate_trade_mode(
            stage, score, risk, capital_out, capital_in
        )

        lines.append("=" * 50)
        lines.append(f"【每日市场交易简报V4】 {today}")
        lines.append("=" * 50)
        lines.append("📊 市场结论")
        lines.append(f"- 市场状态: {stage} ({sentiment})")
        lines.append("- 板块名称 + 分数:")
        for sector, s_score in sorted(
            sector_scores.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            lines.append(f"  {sector}: {s_score}分")
        lines.append(f"  = 真实主线: {is_valid_main}")
        lines.append(f"- 生命周期: {lifecycle}")
        lines.append(f"- 主线强度: {score}")
        lines.append(f"- 风险等级: {risk}")
        lines.append(f"- 切换预警: {warning}")
        lines.append(f"- 操作建议: {advice}")
        lines.append("=" * 50)
        lines.append(f"📊 策略建议 ★★★ 核心")
        lines.append(f"- 当前策略: {strategy}")
        lines.append(f"- 建议仓位: {position}")
        lines.append(f"- 交易模式: {trade_mode}")
        lines.append(f"- 原因解释: {reason}")
        lines.append("=" * 50)

        lines.append("=" * 50)
        lines.append("📊 市场预警")
        lines.append(f"- 主线状态: {main_status}")
        lines.append(f"- 潜在新主线: {new_main}")
        lines.append(f"- 情绪变化: {emotion_change}")
        lines.append(f"- 风险提示: {warning_level}")
        lines.append("=" * 50)

        new_main_candidates = get_new_main_candidates(top_10)

        lines.append("=" * 50)
        lines.append("📊 市场预警          📊 资金轮动分析")
        lines.append(
            f"- 主线状态: {main_status}          - 资金流出: {', '.join(capital_out) if capital_out else '无'}"
        )
        lines.append(
            f"- 潜在新主线: {new_main}          - 资金流入: {', '.join(capital_in) if capital_in else '无'}"
        )
        lines.append(
            f"- 情绪变化: {emotion_change}          - 轮动路径: {rotation_path}"
        )
        lines.append(
            f"- 风险提示: {warning_level}          - 新主线候选: {', '.join(new_main_candidates) if new_main_candidates else '待观察'}"
        )
        lines.append("=" * 50)

        lines_reflect = []
        lines_reflect.append("=" * 50)
        lines_reflect.append("📊 今日市场复盘")

        main_list = ", ".join(list(common_sectors)[:3]) if common_sectors else "无"

        if stage == "主升":
            lines_reflect.append(
                f"1. 市场发生了什么：市场处于主升阶段，{main_list}领涨"
            )
            lines_reflect.append(
                f"2. 主线为什么是当前板块：资金持续流入，板块强度≥70，生命周期在加速期"
            )
            lines_reflect.append(f"3. 资金如何流动：{rotation_path}")
            lines_reflect.append(f"4. 当前风险点：{warning_level}（注意主线切换）")
            lines_reflect.append(f"5. 明日交易关注点：{advice}")
        elif stage == "轮动":
            lines_reflect.append(
                f"1. 市场发生了什么：市场热点轮动，{main_list}轮番表现"
            )
            lines_reflect.append(
                f"2. 主线为什么是当前板块：资金在多个板块间轮动，无持续主线"
            )
            lines_reflect.append(f"3. 资金如何流动：{rotation_path}")
            lines_reflect.append(f"4. 当前风险点：{warning_level}（资金快速轮动）")
            lines_reflect.append(f"5. 明日交易关注点：{advice}")
        else:
            lines_reflect.append("1. 市场发生了什么：市场处于退潮期，热点匮乏")
            lines_reflect.append("2. 主线为什么是当前板块：无明显主线，资金观望")
            lines_reflect.append("3. 资金如何流动：资金流出为主")
            lines_reflect.append("4. 当前风险点：风险（市场风险较高）")
            lines_reflect.append("5. 明日交易关注点：观望为主")

        lines_reflect.append("=" * 50)

        for line in lines_reflect:
            print(line)
    else:
        lines.append("=" * 50)
        lines.append(f"【每日市场交易简报V4】 {today}")
        lines.append("=" * 50)
        lines.append("📊 市场结论")
        lines.append("- 市场状态: 混沌/退潮 (情绪偏弱)")
        lines.append("- 板块名称 + 分数:")
        lines.append("  无")
        lines.append("  = 真实主线: 否")
        lines.append("- 生命周期: 退潮期")
        lines.append("- 主线强度: 0")
        lines.append("- 风险等级: 高风险")
        lines.append("- 操作建议: 观望为主，不宜激进操作")
        lines.append("=" * 50)
        lines.append(f"📊 策略建议 ★★★ 核心")
        lines.append("- 当前策略: 观望")
        lines.append("- 建议仓位: 0%")
        lines.append("- 交易模式: 防守")
        lines.append("- 原因解释: 市场处于退潮期，风险较高，建议收缩战线，防守为主")
        lines.append("=" * 50)
        lines.append("=" * 50)
        lines.append("📊 市场预警          📊 资金轮动分析")
        lines.append(f"- 主线状态: 无          - 资金流出: 无")
        lines.append(f"- 潜在新主线: 无          - 资金流入: 无")
        lines.append(f"- 情绪变化: 退潮          - 轮动路径: 无明显轮动")
        lines.append(f"- 风险提示: 风险          - 新主线候选: 待观察")
        lines.append("=" * 50)
        stage = "混沌/退潮"

        current_stage = "混沌/退潮"
        with open(
            "data/processed/sector_stage_history.csv", "w", encoding="utf-8"
        ) as f:
            f.write(current_stage)

        lines_reflect = []
        lines_reflect.append("=" * 50)
        lines_reflect.append("📊 今日市场复盘")
        lines_reflect.append("1. 市场发生了什么：市场处于退潮期，热点匮乏")
        lines_reflect.append("2. 主线为什么是当前板块：无明显主线，资金观望")
        lines_reflect.append("3. 资金如何流动：资金流出为主")
        lines_reflect.append("4. 当前风险点：风险（市场风险较高）")
        lines_reflect.append("5. 明日交易关注点：观望为主，不宜激进操作")
        lines_reflect.append("=" * 50)

        for line in lines_reflect:
            print(line)

        sentiment = "情绪偏弱"
        capital_out = []
        capital_in = []
        rotation_path = "无明显轮动"
        risk = "高风险"
        warning = "危险"
        strategy = "观望"
        position = "0%"
        advice = "观望为主，不宜激进操作"
        lifecycle = "退潮期"
        score = 0
        common_sectors = set()

    eval_data = generate_evaluation()
    lines_eval = format_evaluation_lines(eval_data)

    for line in lines_eval:
        print(line)

    capital_out_hr = capital_out if "capital_out" in dir() and capital_out else []
    capital_in_hr = capital_in if "capital_in" in dir() and capital_in else []
    rotation_path_hr = (
        rotation_path if "rotation_path" in dir() and rotation_path else "无明显轮动"
    )
    warning_level_hr = warning if "warning" in dir() and warning else "危险"

    human_readable = generate_human_readable_reflection(
        stage=stage,
        sentiment=sentiment,
        main_sectors=list(common_sectors) if common_sectors else [],
        capital_out=capital_out_hr,
        capital_in=capital_in_hr,
        rotation_path=rotation_path_hr,
        risk=risk,
        warning_level=warning_level_hr,
        strategy=strategy,
        position=position,
        advice=advice,
        lifecycle=lifecycle,
        score=score,
    )

    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")
        f.write("\n".join(lines_reflect))
        f.write("\n")
        f.write(human_readable)
        f.write("\n\n")
        f.write("\n".join(lines_eval))

    if os.path.exists("data/processed/sector_rank_yesterday.csv"):
        shutil.copy(
            "data/processed/sector_rank_yesterday.csv",
            "data/processed/sector_rank_3days.csv",
        )
    if os.path.exists("data/raw/sector_rank.csv"):
        shutil.copy(
            "data/raw/sector_rank.csv", "data/processed/sector_rank_yesterday.csv"
        )

    current_stage = stage if common_sectors else "混沌/退潮"
    with open("data/processed/sector_stage_history.csv", "w", encoding="utf-8") as f:
        f.write(current_stage)


if __name__ == "__main__":
    get_sector_data()
