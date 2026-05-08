# -*- coding: utf-8 -*-
import os
import json
import requests
from datetime import datetime


def fetch_market_summary():
    try:
        url = "https://push2ex.eastmoney.com/getTopicZDFenBu"
        response = requests.get(url, timeout=5)
        data = response.json()

        up_count = data.get("data", {}).get("up", 0)
        down_count = data.get("data", {}).get("down", 0)

        return {
            "上涨家数": up_count,
            "下跌家数": down_count,
        }
    except:
        return {"上涨家数": 0, "下跌家数": 0}


def fetch_limit_count():
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1,
            "pz": 5000,
            "po": 1,
            "np": 1,
            "ut": "b2884a393a59ad64002292a3e90d46a5",
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:0+t:80",
            "fields": "f3",
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        stocks = data.get("data", {}).get("diff", [])

        up_limit = sum(1 for s in stocks if s.get("f3", 0) >= 9.9)
        down_limit = sum(1 for s in stocks if s.get("f3", 0) <= -9.9)

        return {"涨停数": up_limit, "跌停数": down_limit}
    except:
        return {"涨停数": 0, "跌停数": 0}


def fetch_market_amount():
    try:
        url = "https://push2.eastmoney.com/api/qt/ulistn/get"
        params = {
            "pn": 1,
            "pz": 1,
            "po": 1,
            "fltt": 2,
            "invt": 2,
            "ut": "b2884a393a59ad64002292a3e90d46a5",
            "fields": "f2",
            "fs": "m:0+t:80+f:!2",
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        amount = data.get("data", {}).get("diff", [{}])[0].get("f2", 0)

        amount_yi = amount / 100000000 if amount else 0
        return {"市场成交额": f"{amount_yi:.0f}亿"}
    except:
        return {"市场成交额": "未知"}


def fetch_north_money():
    try:
        url = "https://push2ex.eastmoney.com/getTopicZTPool"
        params = {"ut": "b2884a393a59ad64002292a3e90d46a5", "dession": "ALL"}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        north = data.get("data", {}).get("north", {})
        north_in = north.get("amount", 0)

        north_yi = north_in / 100000000 if north_in else 0
        return {"北向资金净流入": f"{north_yi:.1f}亿"}
    except:
        return {"北向资金净流入": "暂无"}


def get_market_judge_data():
    summary = fetch_market_summary()
    limit_data = fetch_limit_count()
    amount_data = fetch_market_amount()
    north_data = fetch_north_money()

    result = {}
    result.update(summary)
    result.update(limit_data)
    result.update(amount_data)
    result.update(north_data)

    return result


def analyze_risk_sources():
    risk_data = get_market_judge_data()

    risk_sources = []

    up_count = risk_data.get("上涨家数", 0)
    down_count = risk_data.get("下跌家数", 0)
    total = up_count + down_count
    if total > 0:
        up_ratio = up_count / total

        if up_ratio < 0.3:
            risk_sources.append(
                {
                    "项目": "涨跌比例",
                    "状态": "危险",
                    "说明": f"上涨仅{up_ratio * 100:.0f}%，市场弱势",
                }
            )
        elif up_ratio < 0.5:
            risk_sources.append(
                {
                    "项目": "涨跌比例",
                    "状态": "警惕",
                    "说明": f"上涨{up_ratio * 100:.0f}%，情绪低迷",
                }
            )
        else:
            risk_sources.append(
                {
                    "项目": "涨跌比例",
                    "状态": "安全",
                    "说明": f"上涨{up_ratio * 100:.0f}%，多方占优",
                }
            )

    limit_up = risk_data.get("涨停数", 0)
    limit_down = risk_data.get("跌停数", 0)

    if limit_up > 0 and limit_down > 5:
        risk_sources.append(
            {
                "项目": "炸板率",
                "状态": "危险",
                "说明": f"涨停{limit_up}家，跌停{limit_down}家，风险大",
            }
        )
    elif limit_down > 0:
        risk_sources.append(
            {
                "项目": "跌停数量",
                "状态": "警惕",
                "说明": f"有{limit_down}家跌停，注意风险",
            }
        )
    else:
        risk_sources.append(
            {"项目": "跌停数量", "状态": "安全", "说明": "无跌停股，市场稳定"}
        )

    amount_str = risk_data.get("市场成交额", "未知")
    if amount_str != "未知":
        amount_val = float(amount_str.replace("亿", ""))
        if amount_val < 5000:
            risk_sources.append(
                {
                    "项目": "成交额变化",
                    "状态": "警惕",
                    "说明": f"成交额不足{amount_val:.0f}亿，交投清淡",
                }
            )
        else:
            risk_sources.append(
                {
                    "项目": "成交额变化",
                    "状态": "安全",
                    "说明": f"成交额{amount_val:.0f}亿，活跃度良好",
                }
            )
    else:
        risk_sources.append(
            {"项目": "成交额变化", "状态": "未知", "说明": "数据获取失败"}
        )

    north_str = risk_data.get("北向资金净流入", "暂无")
    if north_str != "暂无":
        try:
            north_val = float(north_str.replace("亿", ""))
            if north_val < 0:
                risk_sources.append(
                    {
                        "项目": "北向资金",
                        "状态": "危险",
                        "说明": f"净流出{-north_val:.1f}亿，外资撤离",
                    }
                )
            elif north_val < 10:
                risk_sources.append(
                    {
                        "项目": "北向资金",
                        "状态": "警惕",
                        "说明": f"净流入{north_val:.1f}亿，态度谨慎",
                    }
                )
            else:
                risk_sources.append(
                    {
                        "项目": "北向资金",
                        "状态": "安全",
                        "说明": f"净流入{north_val:.1f}亿，外资看好",
                    }
                )
        except:
            risk_sources.append(
                {"项目": "北向资金", "状态": "未知", "说明": "数据解析失败"}
            )
    else:
        risk_sources.append({"项目": "北向资金", "状态": "未知", "说明": "暂无数据"})

    if limit_up >= 30:
        risk_sources.append(
            {
                "项目": "高位股情绪",
                "状态": "安全",
                "说明": f"涨停{limit_up}家，短线情绪亢奋",
            }
        )
    elif limit_up >= 10:
        risk_sources.append(
            {
                "项目": "高位股情绪",
                "状态": "安全",
                "说明": f"涨停{limit_up}家，赚钱效应良好",
            }
        )
    else:
        risk_sources.append(
            {
                "项目": "高位股情绪",
                "状态": "警惕",
                "说明": f"涨停仅{limit_up}家，赚钱效应不足",
            }
        )

    return risk_sources


def run_analysis_core():
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "fid": "f62",
        "po": "1",
        "pz": "60",
        "pn": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "ut": "b2884a393a59ad64002292a3e90d46a5",
        "fs": "m:90+t:2",
        "fields": "f12,f14,f2,f3,f62",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        sectors = data["data"]["diff"]
        sectors_sorted = sorted(sectors, key=lambda x: x.get("f3", 0), reverse=True)
        top_10 = sectors_sorted[:10]
        today = datetime.now().strftime("%Y-%m-%d")

        main_sectors_detail = []
        for i, sector in enumerate(top_10[:5]):
            change = sector.get("f3", 0)
            amount = sector.get("f62", 0)
            amount_yi = amount / 100000000 if amount else 0

            strength = 100 - i * 15

            if change >= 5:
                lifecycle = "加速"
            elif change >= 3:
                lifecycle = "发酵"
            elif change >= 1:
                lifecycle = "启动"
            else:
                lifecycle = "退潮"

            confidence = min(100, strength + 20)

            main_sectors_detail.append(
                {
                    "name": sector.get("f14", "未知板块"),
                    "涨幅": f"{change:.2f}%",
                    "成交额": f"{amount_yi:.0f}亿",
                    "强度": strength,
                    "涨停数": 1 if change >= 9.9 else 0,
                    "连板数": 0,
                    "龙头股": sector.get("f14", "未知")[:4],
                    "生命周期": lifecycle,
                    "可信度": confidence,
                }
            )

        common_sectors = [s.get("f14") for s in top_10[:5]]

        count = len(common_sectors)
        sentiment = (
            "情绪偏强" if count >= 3 else ("情绪中性" if count >= 1 else "情绪偏弱")
        )
        stage = (
            "主升"
            if count >= 3 and sentiment == "情绪偏强"
            else ("轮动" if count >= 1 else "震荡")
        )

        score = min(count * 20 + 30, 100)

        if stage == "主升" and score >= 70:
            risk = "低风险"
            strategy = "追涨"
            position = "80%"
            strategy_basis = f"市场处于{stage}阶段，主线明确，情绪{sentiment}，评分{score}分，可顺势追击强势股"
            position_basis = f"主线强度{score}分，处于加速期，风险低，建议高仓位参与"
        elif stage == "轮动" and score >= 40:
            risk = "中风险"
            strategy = "低吸"
            position = "30%"
            strategy_basis = (
                f"市场处于{stage}阶段，热点轮换快，情绪{sentiment}，适合回调低吸"
            )
            position_basis = f"主线强度{score}分，存在不确定性，建议轻仓观望"
        else:
            risk = "高风险"
            strategy = "观望"
            position = "0%"
            strategy_basis = (
                f"市场处于{stage}阶段，情绪偏弱，评分{score}分，建议休息为主"
            )
            position_basis = f"主线强度不足，风险较高，建议清仓观望"

        advice = (
            "可积极参与"
            if risk == "低风险"
            else ("轻仓参与" if risk == "中风险" else "观望为主")
        )

        result = {
            "date": today,
            "market_state": stage,
            "main_sectors": common_sectors,
            "main_sectors_detail": main_sectors_detail,
            "risk_level": risk,
            "strategy": strategy,
            "position": position,
            "score": score,
            "lifecycle": "加速期"
            if stage == "主升"
            else ("分歧期" if stage == "轮动" else "退潮期"),
            "sentiment": sentiment,
            "warning_level": "安全"
            if risk == "低风险"
            else ("警惕" if risk == "中风险" else "风险"),
            "advice": advice,
            "trade_mode": "趋势" if stage == "主升" else "轮动",
            "reason": f"市场处于{stage}阶段",
            "strategy_basis": strategy_basis,
            "position_basis": position_basis,
        }

        return result

    except Exception as e:
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "market_state": "震荡",
            "main_sectors": [],
            "main_sectors_detail": [],
            "risk_level": "高风险",
            "strategy": "观望",
            "position": "0%",
            "score": 0,
            "strategy_basis": "数据获取失败，无法判断",
            "position_basis": "风险未知，建议观望",
            "error": str(e),
        }


if __name__ == "__main__":
    data = run_analysis_core()
    print(data)
