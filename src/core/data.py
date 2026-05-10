# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
from datetime import datetime, timedelta
from services.akshare import (
    get_stock_daily,
    get_northbound_data,
    get_north_flow_data,
    get_market_breadth,
    get_zt_dt_pool,
    get_sector_data,
    get_main_sectors,
    calculate_market_sentiment,
)

__all__ = ["get_market_data", "get_index_data", "get_stock_data", "get_compatible_data"]


def get_market_data(code: str = "000001", days: int = 30) -> dict:
    """
    获取市场行情数据 (统一入口)

    参数:
        code: 指数/股票代码，默认 000001（上证指数）
        days: 天数，默认30天

    返回:
        {"market_data": DataFrame, "status": "success/fail"}
    """
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        df = get_stock_daily(code, start_date, end_date)
        if df is not None and not df.empty:
            return {"market_data": df, "status": "success"}
        return {"market_data": pd.DataFrame(), "status": "fail"}
    except Exception as e:
        return {"market_data": pd.DataFrame(), "status": "fail", "error": str(e)}


def get_index_data(
    code: str = "000001",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """
    获取指数历史数据

    参数:
        code: 指数代码，默认 000001（上证指数）
        start_date: 开始日期
        end_date: 结束日期

    返回:
        {"market_data": DataFrame, "status": "success/fail"}
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

    return get_market_data(code, days=0)


def get_stock_data(
    code: str, start_date: Optional[str] = None, end_date: Optional[str] = None
) -> dict:
    """
    获取股票历史数据

    参数:
        code: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    返回:
        {"market_data": DataFrame, "status": "success/fail"}
    """
    try:
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        df = get_stock_daily(code, start_date, end_date)
        if df is not None and not df.empty:
            return {"market_data": df, "status": "success"}
        return {"market_data": pd.DataFrame(), "status": "fail"}
    except Exception as e:
        return {"market_data": pd.DataFrame(), "status": "fail", "error": str(e)}


def get_compatible_data(code: str = "000001", days: int = 30) -> dict:
    """
    AKShare数据兼容层 - 映射成旧系统数据结构

    返回:
        {
            "market_overview": {},
            "northbound": {},
            "sector_rotation": {},
            "risk_analysis": {},
            "strategy": {}
        }
    """
    result = {
        "market_overview": {},
        "northbound": {},
        "north_flow": {},
        "sector_rotation": {},
        "main_sectors": [],
        "market_sentiment": {},
        "risk_analysis": {},
        "strategy": {},
        "history_data": {},
        "market_breadth": {},
        "zt_dt_pool": {},
    }

    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        df = get_stock_daily(code, start_date, end_date)

        if df is not None and not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            latest_date = str(latest.get("date", ""))
            latest_close = latest.get("close", 0)
            prev_close = prev.get("close", 0)

            change = latest_close - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            amount = latest.get("amount", 0)
            amount_yi = amount / 100000000 if amount else 0

            change_value = f"{'+' if change >= 0 else ''}{change:.2f}"
            change_str = f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%"

            if abs(change_pct) < 1:
                risk_level = "低风险"
                risk_icon = "✅"
            elif abs(change_pct) < 3:
                risk_level = "中风险"
                risk_icon = "⚠️"
            else:
                risk_level = "高风险"
                risk_icon = "❌"

            result["market_overview"] = {
                "date": latest_date,
                "close": latest_close,
                "change": change_value,
                "change_pct": change_str,
                "amount": amount_yi,
                "state": "上涨" if change >= 0 else "下跌",
                "risk_level": risk_level,
                "risk_icon": risk_icon,
            }

            risk_reasons = []

            if change_pct < -3:
                risk_reasons.append("最近1日跌幅超过3%，风险增加")

            if len(df) >= 2:
                prev_amount = df.iloc[-2].get("amount", 0)
                if prev_amount > 0:
                    amount_change = (amount - prev_amount) / prev_amount * 100
                    if amount_change < -20:
                        risk_reasons.append("成交额下降超过20%，流动性减弱")

            if len(df) >= 4:
                change_3d_list = []
                for i in range(1, 4):
                    c_now = df.iloc[-i].get("close", 0)
                    c_prev = df.iloc[-i - 1].get("close", 0)
                    if c_prev > 0:
                        change_3d_list.append(c_now > c_prev)
                if all(change_3d_list):
                    risk_reasons.append("最近3日连续上涨，情绪偏强")

            if len(risk_reasons) >= 2:
                calc_risk_level = "高"
            elif len(risk_reasons) == 1:
                calc_risk_level = "中"
            else:
                calc_risk_level = "低"

            result["risk_analysis"] = {
                "risk_level": calc_risk_level,
                "risk_reasons": risk_reasons,
                "change_pct": change_pct,
                "status": "正常",
            }

            if len(df) >= 6:
                close_5d_ago = df.iloc[-6].get("close", 0)
                change_5d = (
                    ((latest_close - close_5d_ago) / close_5d_ago * 100)
                    if close_5d_ago > 0
                    else 0
                )
                result["market_overview"]["change_5d"] = (
                    f"{'+' if change_5d >= 0 else ''}{change_5d:.2f}%"
                )
            else:
                result["market_overview"]["change_5d"] = "暂无"

            if len(df) >= 2:
                history_df = df.tail(30)
                result["history_data"] = {
                    "dates": [
                        str(row.get("date", "")) for _, row in history_df.iterrows()
                    ],
                    "close": [
                        round(row.get("close", 0), 2)
                        for _, row in history_df.iterrows()
                    ],
                    "amount": [
                        round(row.get("amount", 0) / 100000000, 2)
                        for _, row in history_df.iterrows()
                    ],
                    "status": "正常",
                }
        else:
            result["market_overview"] = {"status": "暂无", "message": "数据获取失败"}
            result["risk_analysis"] = {"status": "暂无", "message": "数据获取失败"}

    except Exception as e:
        result["market_overview"] = {"status": "暂无", "message": str(e)}
        result["risk_analysis"] = {"status": "暂无", "message": str(e)}

    northbound_data = get_northbound_data()
    result["northbound"] = northbound_data

    try:
        north_flow_data = get_north_flow_data()
        result["north_flow"] = north_flow_data
    except:
        result["north_flow"] = {
            "north_in": 0,
            "north_out": 0,
            "net": 0,
            "status": "暂无数据",
        }

    try:
        result["main_sectors"] = get_main_sectors()
    except:
        result["main_sectors"] = []

    try:
        market_breadth_data = get_market_breadth()
        result["market_breadth"] = market_breadth_data
    except Exception:
        result["market_breadth"] = {
            "up": 0,
            "down": 0,
            "flat": 0,
            "up_ratio": 0,
            "status": "暂无数据",
        }

    try:
        zt_dt_data = get_zt_dt_pool()
        result["zt_dt_pool"] = zt_dt_data
    except Exception:
        result["zt_dt_pool"] = {"limit_up": 0, "limit_down": 0, "status": "暂无数据"}

    up_count = result.get("market_breadth", {}).get("up", 0)
    down_count = result.get("market_breadth", {}).get("down", 0)
    flat_count = result.get("market_breadth", {}).get("flat", 0)
    limit_up_count = result.get("zt_dt_pool", {}).get("limit_up", 0)
    limit_down_count = result.get("zt_dt_pool", {}).get("limit_down", 0)
    north_net = result.get("north_flow", {}).get("net", 0)
    amount_change_pct = result.get("market_overview", {}).get("amount_change_pct", 0)

    sentiment = calculate_market_sentiment(
        up_count,
        down_count,
        flat_count,
        limit_up_count,
        limit_down_count,
        north_net,
        amount_change_pct,
    )
    result["market_sentiment"] = sentiment

    result["sector_rotation"] = {
        "status": "模块升级中",
        "message": "板块轮动数据模块升级中",
    }

    result["strategy"] = {"status": "模块升级中", "message": "策略建议模块升级中"}

    return result


if __name__ == "__main__":
    print(get_market_data())
