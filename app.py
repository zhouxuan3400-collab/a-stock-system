# -*- coding: utf-8 -*-
import streamlit as st

from src.data.access import get_latest_result, get_history


st.set_page_config(page_title="A股交易面板", page_icon="📈")

st.markdown(
    """
<style>
    .stMetric { padding: 10px; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("📈 A股交易面板")

data = get_latest_result()

if data and "error" not in data:
    st.markdown("### 📊 市场总览")

    state = data.get("market_state", "未知")
    if state == "主升":
        emoji = "🐂"
    elif state == "轮动":
        emoji = "↔️"
    else:
        emoji = "🐻"
    st.metric("市场状态", f"{emoji} {state}")

    risk = data.get("risk_level", "未知")
    if risk == "低风险":
        st.metric("风险等级", "✅ 低风险")
    elif risk == "中风险":
        st.metric("风险等级", "⚠️ 中风险")
    else:
        st.metric("风险等级", "❌ 高风险")

    score = data.get("score", 0)
    st.metric("情绪评分", f"{score}/100")

    with st.expander("📖 指标说明：市场总览"):
        st.markdown("""
        **情绪评分**: 基于主线强度、市场阶段、板块活跃度综合计算，0-100分
        - 70分以上：情绪亢奋，可积极做多
        - 40-70分：情绪中性，轮动对待
        - 40分以下：情绪低迷，建议观望
        
        **风险等级**: 综合市场状态、主线强度、生命周期判断
        - 低风险：主线明确，趋势健康，可80%仓位
        - 中风险：主线模糊，建议30%仓位
        - 高风险：趋势不明，建议0%仓位
        """)

    st.markdown("---")

    st.markdown("### ⚠️ 风险来源分析")

    risk_sources = data.get("risk_sources", [])
    if risk_sources:
        for rs in risk_sources:
            status = rs.get("状态", "未知")
            if status == "安全":
                icon = "✅"
            elif status == "警惕":
                icon = "⚠️"
            else:
                icon = "❌"
            st.markdown(f"**{icon} {rs.get('项目', '')}**: {rs.get('说明', '')}")
    else:
        st.info("暂无风险来源数据")

    up_count = data.get("上涨家数", "未知")
    down_count = data.get("下跌家数", "未知")
    limit_up = data.get("涨停数", "未知")
    limit_down = data.get("跌停数", "未知")
    amount = data.get("市场成交额", "未知")
    north = data.get("北向资金净流入", "暂无")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("上涨家数", up_count)
        st.metric("涨停数", limit_up)
        st.metric("市场成交额", amount)
    with col2:
        st.metric("下跌家数", down_count)
        st.metric("跌停数", limit_down)
        st.metric("北向资金", north)

    st.markdown("---")

    st.markdown("### 🚀 主线板块")

    main_sectors_detail = data.get("main_sectors_detail", [])
    if main_sectors_detail:
        for sector in main_sectors_detail:
            with st.expander(
                f"📌 {sector.get('name', '未知')} - {sector.get('涨幅', '0%')}"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("强度", f"{sector.get('强度', 0)}/100")
                    st.metric("涨停数", sector.get("涨停数", 0))
                    st.metric("生命周期", sector.get("生命周期", "未知"))
                with col2:
                    st.metric("涨幅", sector.get("涨幅", "0%"))
                    st.metric("连板数", sector.get("连板数", 0))
                    st.metric("可信度", f"{sector.get('可信度', 0)}%")

                st.markdown(f"**龙头股:** {sector.get('龙头股', '暂无')}")
                st.markdown(f"**成交额:** {sector.get('成交额', '未知')}")

        with st.expander("📖 指标说明：主线板块"):
            st.markdown("""
            **生命周期**: 板块当前所处的上涨阶段
            - 启动期：刚刚启动，后续有望加速
            - 发酵期：市场认可度提升，趋势形成
            - 加速期：主升浪，风险收益比最佳
            - 退潮期：开始回落，注意风险
            
            **连板数**: 板块中连续涨停的股票数量，反映短线情绪强度
            
            **可信度**: 基于板块强度、成交额、持续性的综合评分
            """)
    else:
        main_sectors = data.get("main_sectors", [])
        if main_sectors:
            for i, sector in enumerate(main_sectors[:5], 1):
                st.markdown(f"**{i}. {sector}**")
        else:
            st.info("暂无主线板块")

    st.markdown("---")

    st.markdown("### 📈 策略建议")

    strategy = data.get("strategy", "观望")
    position = data.get("position", "0%")
    advice = data.get("advice", "")
    strategy_basis = data.get("strategy_basis", "")
    position_basis = data.get("position_basis", "")

    st.metric("操作方向", strategy)
    st.metric("建议仓位", position)

    pos_val = int(position.replace("%", "")) / 100
    st.progress(pos_val)

    st.markdown(f"**策略依据:** {strategy_basis}")
    st.markdown(f"**仓位依据:** {position_basis}")

    with st.expander("📖 指标说明：策略与仓位"):
        st.markdown("""
        **仓位建议**: 根据市场风险等级和主线强度综合决定
        - 80%仓位：主线明确，趋势健康，可积极做多
        - 30%仓位：主线模糊，轮动为主，轻仓参与
        - 0%仓位：风险较高，建议观望
        
        **操作方向**: 基于市场阶段选择的策略
        - 追涨：主升阶段，顺势追击强势股
        - 低吸：轮动阶段，回调时买入
        - 观望：退潮阶段，多看少动
        """)

    st.markdown("---")

    st.markdown("### 📜 历史走势")

    history = get_history()
    if not history:
        st.warning("暂无历史数据，请等待系统运行")
    else:
        history_sorted = sorted(history, key=lambda x: x.get("date", ""), reverse=True)[
            :10
        ]

        if len(history_sorted) >= 2:
            import pandas as pd

            history_df = pd.DataFrame(history_sorted)
            history_df["date"] = pd.to_datetime(history_df["date"])
            st.markdown("**情绪评分趋势**")
            score_data = history_df.set_index("date")["score"]
            st.line_chart(score_data, use_container_width=True)

        st.markdown("**最近10日变化记录**")

        for row in history_sorted:
            main_sector = row.get("main_sector", "无")
            st.markdown(
                f"**{row.get('date', '')[:10]}** | {row.get('market_state', '')} | {main_sector[:15]} | {row.get('risk_level', '')} | {row.get('strategy', '')} | {row.get('position', '')}"
            )

    st.markdown("---")
    st.caption(f"📅 更新: {data.get('date', '未知')}")

elif data and "error" in data:
    st.error(f"❌ 分析出错: {data.get('error')}")

else:
    st.warning("⚠️ 暂无数据，请等待自动运行")
    st.markdown("""
    ---
    **说明：**
    - 数据由 GitHub Actions 每天自动更新
    - 或运行 `python auto_run.py` 本地生成数据
    """)

st.caption("📈 A股交易面板 v7.0")
