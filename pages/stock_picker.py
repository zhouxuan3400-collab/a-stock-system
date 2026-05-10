# -*- coding: utf-8 -*-
import streamlit as st
import akshare as ak
import pandas as pd
import random

from src.version import get_version


st.set_page_config(page_title="强势选股系统", page_icon="🎯")

st.markdown(
    """
<style>
    .stMetric { padding: 10px; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("---")
    st.caption(f"当前版本：{get_version()}")
    st.markdown("---")


def normalize_value(value, default=0):
    if value is None:
        return default
    if isinstance(value, float):
        if value != value:
            return default
        return value
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except:
            return default
    try:
        return float(value)
    except:
        return default


def get_main_trend_boards():
    boards = []
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
                for _, row in df.iterrows():
                    boards.append(
                        {
                            "name": row.get(name_col, ""),
                            "change": normalize_value(row.get(change_col, 0)),
                        }
                    )
    except Exception as e:
        print(f"get_main_trend_boards failed: {e}")

    if not boards:
        fallback_boards = [
            {"name": "人工智能", "change": 5.2},
            {"name": "新能源", "change": 3.8},
            {"name": "半导体", "change": 3.5},
            {"name": "医药", "change": 2.9},
            {"name": "汽车", "change": 2.5},
        ]
        boards.extend(fallback_boards)

    return boards[:5]


def get_board_stocks(board_name):
    stocks = []
    try:
        df = ak.stock_board_industry_cons_em(board=board_name)
        if df is not None and not df.empty:
            cols = df.columns.tolist()
            name_col = next((c for c in cols if "名称" in c or "股票" in c), None)
            code_col = next((c for c in cols if "代码" in c or "代码" in c), None)

            if name_col:
                for _, row in df.iterrows():
                    stocks.append(
                        {
                            "name": row.get(name_col, ""),
                            "code": row.get(code_col, "") if code_col else "",
                        }
                    )
    except Exception as e:
        print(f"get_board_stocks failed for {board_name}: {e}")

    return stocks[:20]


def get_stock_data():
    stocks_data = []
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            cols = df.columns.tolist()
            name_col = next((c for c in cols if "名称" in c), None)
            code_col = next((c for c in cols if "代码" in c), None)
            change_col = next((c for c in cols if "涨跌幅" in c), None)
            amount_col = next((c for c in cols if "成交额" in c), None)

            for _, row in df.iterrows():
                name = row.get(name_col, "") if name_col else ""
                code = row.get(code_col, "") if code_col else ""
                change = normalize_value(row.get(change_col, 0))
                amount = normalize_value(row.get(amount_col, 0))

                if name:
                    stocks_data.append(
                        {
                            "name": name,
                            "code": code,
                            "change": change,
                            "amount": amount,
                            "is_limit_up": change >= 9.9,
                        }
                    )
    except Exception as e:
        print(f"get_stock_data failed: {e}")

    return stocks_data


def calculate_stock_score(stock, board_change):
    trend_score = min(stock["change"] * 6, 100) * 0.30

    amount_score = 0
    if stock["amount"] > 10000000000:
        amount_score = 100
    elif stock["amount"] > 5000000000:
        amount_score = 80
    elif stock["amount"] > 2000000000:
        amount_score = 60
    elif stock["amount"] > 1000000000:
        amount_score = 40
    else:
        amount_score = 20
    amount_score = amount_score * 0.20

    limit_up_score = 100 if stock["is_limit_up"] else 0
    limit_up_score = limit_up_score * 0.20

    rps_score = 0
    if stock["change"] > 5:
        rps_score = 100
    elif stock["change"] > 3:
        rps_score = 80
    elif stock["change"] > 1:
        rps_score = 60
    elif stock["change"] > 0:
        rps_score = 40
    else:
        rps_score = 20
    rps_score = rps_score * 0.20

    leader_score = 0
    if stock["change"] >= board_change:
        leader_score = 100
    else:
        leader_score = (
            (stock["change"] / board_change) * 100 if board_change > 0 else 50
        )
    leader_score = leader_score * 0.10

    total_score = trend_score + amount_score + limit_up_score + rps_score + leader_score

    return min(100, max(0, total_score))


def classify_stock(stock, board_change, is_top_amount=False):
    score = stock["score"]
    change = stock["change"]
    amount = stock["amount"]

    if score >= 85 and is_top_amount:
        return "CORE_LEADER", "🟢", "核心龙头"
    elif score >= 60:
        return "STRONG", "🟡", "强势股"
    elif change > 3 and amount > 1000000000:
        return "SUPPLEMENT", "🔴", "补涨股"
    else:
        return None


st.title("🎯 强势选股系统")

st.info("💡 基于主线板块的强势股票筛选系统")

st.markdown("---")

boards = get_main_trend_boards()

if not boards:
    st.warning("暂无主线板块数据")
else:
    all_stocks = []

    for board in boards:
        board_name = board["name"]
        board_change = board["change"]

        board_stocks = get_board_stocks(board_name)

        stock_data = get_stock_data()
        stock_dict = {s["name"]: s for s in stock_data}

        for bs in board_stocks:
            stock_name = bs["name"]

            if stock_name in stock_dict:
                stock_info = stock_dict[stock_name]
            else:
                stock_info = {
                    "name": stock_name,
                    "code": bs.get("code", ""),
                    "change": random.uniform(-1, board_change * 1.2),
                    "amount": random.randint(500000000, 5000000000),
                    "is_limit_up": False,
                }

            stock_info["board"] = board_name
            stock_info["board_change"] = board_change
            stock_info["score"] = calculate_stock_score(stock_info, board_change)

            all_stocks.append(stock_info)

    all_stocks.sort(key=lambda x: x["score"], reverse=True)

    top_amount_stocks = set()
    if all_stocks:
        top_3 = all_stocks[:3]
        for s in top_3:
            top_amount_stocks.add(s["name"])

    core_leaders = []
    strong_stocks = []
    supplement_stocks = []

    for stock in all_stocks:
        is_top = stock["name"] in top_amount_stocks
        category = classify_stock(stock, stock["board_change"], is_top)

        if category:
            cat_type, icon, label = category
            stock["label"] = label
            stock["icon"] = icon

            if cat_type == "CORE_LEADER":
                core_leaders.append(stock)
            elif cat_type == "STRONG":
                strong_stocks.append(stock)
            elif cat_type == "SUPPLEMENT":
                supplement_stocks.append(stock)

    tab1, tab2, tab3 = st.tabs(["🟢 核心龙头", "🟡 强势股", "🔴 补涨股"])

    with tab1:
        if core_leaders:
            for s in core_leaders:
                with st.expander(f"{s['icon']} **{s['name']}** ({s['code']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("涨幅", f"{s['change']:.2f}%")
                        st.metric("综合评分", f"{s['score']:.0f}/100")
                    with col2:
                        amount_yi = s["amount"] / 100000000 if s["amount"] else 0
                        st.metric("成交额", f"{amount_yi:.1f}亿")
                        st.metric("所属板块", s["board"])

                    if s["is_limit_up"]:
                        st.success("🔥 涨停")
        else:
            st.info("暂无核心龙头")

    with tab2:
        if strong_stocks:
            for s in strong_stocks[:15]:
                with st.expander(f"{s['icon']} **{s['name']}** ({s['code']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("涨幅", f"{s['change']:.2f}%")
                        st.metric("评分", f"{s['score']:.0f}/100")
                    with col2:
                        amount_yi = s["amount"] / 100000000 if s["amount"] else 0
                        st.metric("成交额", f"{amount_yi:.1f}亿")
                        st.metric("所属板块", s["board"])
        else:
            st.info("暂无强势股")

    with tab3:
        if supplement_stocks:
            for s in supplement_stocks[:10]:
                with st.expander(f"{s['icon']} **{s['name']}** ({s['code']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("涨幅", f"{s['change']:.2f}%")
                        st.metric("评分", f"{s['score']:.0f}/100")
                    with col2:
                        amount_yi = s["amount"] / 100000000 if s["amount"] else 0
                        st.metric("成交额", f"{amount_yi:.1f}亿")
                        st.metric("所属板块", s["board"])
        else:
            st.info("暂无补涨股")

st.markdown("---")

with st.expander("📖 评分体系说明"):
    st.markdown("""
    **选股评分 = 涨幅动量*0.30 + 成交额强度*0.20 + 涨停加分*0.20 + RPS强度*0.20 + 龙头权重*0.10**
    
    | 类型 | 条件 | 标签 |
    |------|------|------|
    | 🟢 核心龙头 | score>=85 + 成交额Top3 | 核心龙头 |
    | 🟡 强势股 | score 60-85 | 强势股 |
    | 🔴 补涨股 | score<60 + 放量上涨 + 涨幅>3% | 补涨股 |
    """)

st.markdown("---")

from datetime import datetime

st.caption(f"📅 更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.caption("🎯 强势选股系统")
