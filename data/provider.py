# -*- coding: utf-8 -*-
import streamlit as st
import akshare as ak
import pandas as pd
import random
from datetime import datetime, timedelta


def is_market_open():
    """
    判断是否在交易时间
    A股：9:30-11:30 / 13:00-15:00
    """
    now = datetime.now()
    hour = now.hour
    minute = now.minute

    time_value = hour * 60 + minute

    morning_start = 9 * 60 + 30
    morning_end = 11 * 60 + 30
    afternoon_start = 13 * 60
    afternoon_end = 15 * 60

    return (morning_start <= time_value <= morning_end) or (
        afternoon_start <= time_value <= afternoon_end
    )


def normalize_value(value, default=0):
    if value is None:
        return default
    if isinstance(value, float):
        if value != value:
            return default
        if abs(value) > 1e15:
            return float("nan")
        return value
    if isinstance(value, str):
        value_str = value.strip()
        if "e" in value_str.lower() or "E" in value_str:
            return float("nan")
        try:
            v = float(value_str.replace(",", ""))
            if abs(v) > 1e15:
                return float("nan")
            return v
        except:
            return default
    try:
        v = float(value)
        if abs(v) > 1e15:
            return float("nan")
        return v
    except:
        return default


@st.cache_data(ttl=600)
def get_market_boards():
    try:
        df = ak.stock_board_industry_name_em()
        if df is not None and not df.empty:
            cols = df.columns.tolist()
            name_col = next(
                (c for c in cols if "板块" in c or "行业" in c or "名称" in c), None
            )
            change_col = next((c for c in cols if "涨跌幅" in c or "涨幅" in c), None)

            if name_col and change_col:
                df = df.sort_values(by=change_col, ascending=False).head(10)
                boards = []
                for _, row in df.iterrows():
                    boards.append(
                        {
                            "name": row.get(name_col, ""),
                            "change": normalize_value(row.get(change_col, 0)),
                        }
                    )
                return boards
    except Exception as e:
        print(f"get_market_boards failed: {e}")
    return None


@st.cache_data(ttl=600)
def get_market_snapshot():
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            up_count = 0
            down_count = 0
            limit_up = 0
            limit_down = 0
            total_amount = 0

            for _, row in df.iterrows():
                try:
                    change = normalize_value(row.get("涨跌幅", 0))
                    amount = normalize_value(row.get("成交额", 0))

                    if change > 0:
                        up_count += 1
                    elif change < 0:
                        down_count += 1

                    if change >= 9.9:
                        limit_up += 1
                    elif change <= -9.9:
                        limit_down += 1

                    total_amount += amount
                except:
                    continue

            return {
                "up_count": up_count,
                "down_count": down_count,
                "limit_up": limit_up,
                "limit_down": limit_down,
                "total_amount": total_amount,
            }
    except Exception as e:
        print(f"get_market_snapshot failed: {e}")
    return None


@st.cache_data(ttl=600)
def get_turnover_change():
    try:
        df = ak.stock_zh_index_daily_em(symbol="000001")
        if df is not None and not df.empty:
            amount_today = normalize_value(df.iloc[-1].get("成交额", 0))
            if len(df) >= 2:
                amount_yesterday = normalize_value(df.iloc[-2].get("成交额", 0))
            else:
                amount_yesterday = amount_today * 0.9

            if amount_yesterday > 0:
                return (amount_today - amount_yesterday) / amount_yesterday * 100
    except Exception as e:
        print(f"get_turnover_change failed: {e}")
    return None


@st.cache_data(ttl=600)
def get_stock_list():
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            cols = df.columns.tolist()
            name_col = next((c for c in cols if "名称" in c), None)
            code_col = next((c for c in cols if "代码" in c), None)
            change_col = next((c for c in cols if "涨跌幅" in c), None)
            amount_col = next((c for c in cols if "成交额" in c), None)

            stocks = []
            for _, row in df.head(100).iterrows():
                name = row.get(name_col, "") if name_col else ""
                if name:
                    stocks.append(
                        {
                            "name": name,
                            "code": row.get(code_col, "") if code_col else "",
                            "change": normalize_value(row.get(change_col, 0)),
                            "amount": normalize_value(row.get(amount_col, 0)),
                            "is_limit_up": normalize_value(row.get(change_col, 0))
                            >= 9.9,
                        }
                    )
            return stocks
    except Exception as e:
        print(f"get_stock_list failed: {e}")
    return None


def get_board_stocks(board_name):
    try:
        df = ak.stock_board_industry_cons_em(board=board_name)
        if df is not None and not df.empty:
            cols = df.columns.tolist()
            name_col = next((c for c in cols if "名称" in c or "股票" in c), None)
            code_col = next((c for c in cols if "代码" in c), None)

            stocks = []
            if name_col:
                for _, row in df.head(20).iterrows():
                    stocks.append(
                        {
                            "name": row.get(name_col, ""),
                            "code": row.get(code_col, "") if code_col else "",
                        }
                    )
            return stocks
    except Exception as e:
        print(f"get_board_stocks failed for {board_name}: {e}")
    return [] # board_name)


@st.cache_data(ttl=600)
def get_risk_sources():
    snapshot = get_market_snapshot()
    turnover_change = get_turnover_change()

    risk_sources = []

    up_count = snapshot.get("up_count", 0)
    down_count = snapshot.get("down_count", 0)
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

    limit_up = snapshot.get("limit_up", 0)
    limit_down = snapshot.get("limit_down", 0)

    if limit_down > 0:
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

    total_amount = snapshot.get("total_amount", 0)
    amount_yi = total_amount / 100000000 if total_amount else 0

    if amount_yi < 5000:
        risk_sources.append(
            {
                "项目": "成交额变化",
                "状态": "警惕",
                "说明": f"成交额不足{amount_yi:.0f}亿，交投清淡",
            }
        )
    else:
        risk_sources.append(
            {
                "项目": "成交额变化",
                "状态": "安全",
                "说明": f"成交额{amount_yi:.0f}亿，活跃度良好",
            }
        )

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


def format_money(value):
    if value is None:
        return "0亿"
    if isinstance(value, float):
        if value != value:
            return "0亿"
        return f"{value:.2f}亿"
    return f"{float(value):.2f}亿" if value else "0亿"
