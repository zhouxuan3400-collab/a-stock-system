# -*- coding: utf-8 -*-
import streamlit as st

from src.version import get_version
from data.provider import (
    get_market_snapshot,
    get_turnover_change,
    get_risk_sources,
    safe_snapshot,
)


st.set_page_config(page_title="市场总览", page_icon="📊")

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


st.title("📊 市场总览")

if "market_data" in st.session_state:
    raw_snapshot = st.session_state.market_data.get("snapshot", None)
    turnover_change = st.session_state.market_data.get("turnover_change", 0)
else:
    from data.provider import get_market_snapshot, get_turnover_change, safe_snapshot

    raw_snapshot = get_market_snapshot()
    turnover_change = get_turnover_change()
    safe_snapshot = safe_snapshot

snapshot = safe_snapshot(raw_snapshot)

risk_sources = get_risk_sources()

st.markdown("### ⚠️ 风险来源分析")

if risk_sources:
    for rs in risk_sources:
        status = rs.get("状态", "未知")
        if status == "安全":
            icon = "✅"
        elif status == "警惕":
            icon = "⚠️"
        else:
            icon = "❌"
        item = rs.get("项目", "")
        desc = rs.get("说明", "")
        st.markdown(f"**{icon} {item}**: {desc}")
else:
    st.info("数据获取中")

st.markdown("---")

st.markdown("### 📈 市场总览")

up_count = snapshot.get("up_count", 0)
down_count = snapshot.get("down_count", 0)
limit_up = snapshot.get("limit_up", 0)
limit_down = snapshot.get("limit_down", 0)
total_amount = snapshot.get("total_amount", 0)
amount_yi = total_amount / 100000000 if total_amount else 0

turnover_str = f"{turnover_change:+.1f}%" if turnover_change else "数据获取中"

col1, col2 = st.columns(2)
with col1:
    st.metric("上涨家数", f"{up_count:,}" if up_count else "数据获取中")
    st.metric("涨停数", f"{limit_up}" if limit_up else "数据获取中")
    st.metric("市场成交额", f"{amount_yi:.0f}亿" if amount_yi else "数据获取中")
    st.metric("成交额变化", turnover_str)
with col2:
    st.metric("下跌家数", f"{down_count:,}" if down_count else "数据获取中")
    st.metric("跌停数", f"{limit_down}" if limit_down else "数据获取中")

st.markdown("---")

from datetime import datetime

st.caption(f"📅 更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.caption("📊 市场总览")
