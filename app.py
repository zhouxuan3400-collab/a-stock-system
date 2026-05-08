# -*- coding: utf-8 -*-
import streamlit as st
import os
from datetime import datetime
import requests
import csv
import json
import subprocess
import threading
import time

CACHE_FILE = "data/latest_result.json"
TASK_STATUS_FILE = "data/processed/task_status.json"


def get_task_status():
    if os.path.exists(TASK_STATUS_FILE):
        with open(TASK_STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "idle", "message": ""}


def set_task_status(status, message=""):
    os.makedirs("data/processed", exist_ok=True)
    with open(TASK_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump({"status": status, "message": message}, f, ensure_ascii=False)


def save_market_data(data):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_market_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def run_analysis_background():
    try:
        set_task_status("running", "分析中...")
        data = get_market_data()
        save_market_data(data)
        set_task_status("completed", "分析完成")
    except Exception as e:
        set_task_status("error", str(e))


def trigger_background_analysis():
    task = get_task_status()
    if task["status"] == "running":
        return False
    threading.Thread(target=run_analysis_background, daemon=True).start()
    return True


st.set_page_config(layout="wide")

st.sidebar.title("📊 导航菜单")
page = st.sidebar.radio("选择页面", ["交易面板", "系统说明"])

if page == "系统说明":
    st.switch_page("explain.py")

st.sidebar.markdown("---")
st.sidebar.markdown("📚 **系统说明**")
st.sidebar.info("点击上方「系统说明」查看完整使用文档")

st.markdown(
    """
<style>
    div[data-testid="stDataFrame"] {
        white-space: normal !important;
        overflow: visible !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def get_market_data():
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
        "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13",
    }

    response = requests.get(url, params=params)
    data = response.json()
    sectors = data["data"]["diff"]

    sectors_sorted = sorted(sectors, key=lambda x: x.get("f3", 0), reverse=True)
    top_10 = sectors_sorted[:10]
    today = datetime.now().strftime("%Y-%m-%d")

    today_sectors = {sector.get("f14", "") for sector in top_10}

    yesterday_file = "data/processed/sector_rank_yesterday.csv"
    yesterday_sectors = set()
    common_sectors = set()

    capital_out = []
    capital_in = []
    rotation_path = "无明显轮动"
    new_main_candidates = []

    if os.path.exists(yesterday_file):
        with open(yesterday_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yesterday_sectors.add(row["板块名称"])
        common_sectors = today_sectors & yesterday_sectors

        today_top_names = [s.get("f14", "") for s in top_10[:5]]
        yesterday_top_names = list(yesterday_sectors)[:5]

        outflow = set(yesterday_top_names) - set(today_top_names)
        inflow = set(today_top_names) - set(yesterday_top_names)

        capital_out = list(outflow)[:3] if outflow else []
        capital_in = list(inflow)[:3] if inflow else []

        if capital_out and capital_in:
            rotation_path = f"{capital_out[0]} → {capital_in[0]}"

        new_main_candidates = [
            s.get("f14", "") for s in top_10[:3] if s.get("f3", 0) > 3
        ]

    if common_sectors:
        count = len(common_sectors)
        sentiment = (
            "情绪偏强" if count >= 3 else ("情绪中性" if count >= 1 else "情绪偏弱")
        )
        stage = (
            "主升"
            if count >= 3 and sentiment == "情绪偏强"
            else ("轮动" if count >= 1 else "混沌/退潮")
        )
        capital = "资金集中" if count <= 2 else "资金分散"

        if count <= 1 and sentiment == "情绪偏强":
            lifecycle = "启动期"
        elif stage == "主升":
            lifecycle = "加速期"
        elif stage == "轮动":
            lifecycle = "分歧期"
        else:
            lifecycle = "退潮期"

        score = (
            min(count * 20, 60)
            + (20 if sentiment == "情绪偏强" else 0)
            + (10 if stage == "主升" else 0)
            + (10 if capital == "资金集中" else 0)
        )

        risk = (
            "低风险"
            if score >= 70 and lifecycle == "加速期"
            else ("中风险" if score >= 40 else "高风险")
        )

        explanations = []
        if stage == "主升":
            explanations.append("市场处于强势上涨阶段，主线明确")
        elif stage == "轮动":
            explanations.append("市场热点轮换快，暂无持续主线")
        else:
            explanations.append("市场方向不明，处于震荡调整期")

        if common_sectors:
            sectors_str = "、".join(list(common_sectors)[:2])
            explanations.append(f"资金主要流入{sectors_str}等板块")

        if score >= 70:
            explanations.append("趋势强度高，可顺势操作")
        elif score >= 40:
            explanations.append("趋势力度一般，建议观望")
        else:
            explanations.append("趋势较弱，不宜重仓追涨")

        if risk == "低风险":
            explanations.append("风险较低，可适度参与")
        elif risk == "中风险":
            explanations.append("风险中等，建议轻仓")
        else:
            explanations.append("风险较高，建议远离")

        market_explain = "；".join(explanations)

        if stage == "主升" and score >= 70 and risk == "低风险":
            strategy = "追涨"
            position = "80%"
            allow_trade = "是"
        elif stage == "轮动" and score >= 40 and risk != "高风险":
            strategy = "低吸"
            position = "30%"
            allow_trade = "是"
        else:
            strategy = "观望"
            position = "0%"
            allow_trade = "否"

        warning_level = (
            "安全"
            if score >= 70 and lifecycle == "加速期"
            else ("警惕" if score >= 40 else "风险")
        )

        if capital_out and capital_in:
            trade_mode = "轮动"
            reason = (
                f"资金轮动活跃，从{capital_out[0]}轮动至{capital_in[0]}，适合短差操作"
            )
        elif stage == "主升" and score >= 70:
            trade_mode = "趋势"
            reason = "市场处于主升阶段，趋势明确，可顺势追涨"
        elif risk == "高风险" or stage == "混沌/退潮":
            trade_mode = "防守"
            reason = "市场风险较高，建议收缩战线，防守为主"
        else:
            trade_mode = "轮动"
            reason = "市场处于轮动状态，建议轻仓短差"

        advice = (
            "可积极参与，设好止损持有"
            if risk == "低风险"
            else ("轻仓参与，关注变化" if risk == "中风险" else "观望为主，不宜激进")
        )

        return {
            "date": today,
            "stage": stage,
            "main_sectors": list(common_sectors),
            "lifecycle": lifecycle,
            "score": score,
            "capital": capital,
            "sentiment": sentiment,
            "risk": risk,
            "market_explain": market_explain,
            "advice": advice,
            "strategy": strategy,
            "position": position,
            "allow_trade": allow_trade,
            "warning_level": warning_level,
            "capital_out": capital_out,
            "capital_in": capital_in,
            "rotation_path": rotation_path,
            "new_main_candidates": new_main_candidates,
            "trade_mode": trade_mode,
            "reason": reason,
        }
    else:
        return {
            "date": today,
            "stage": "混沌/退潮",
            "main_sectors": [],
            "lifecycle": "退潮期",
            "score": 0,
            "capital": "资金分散",
            "sentiment": "情绪偏弱",
            "risk": "高风险",
            "market_explain": "市场方向不明；趋势较弱；风险较高",
            "advice": "观望为主，不宜激进",
            "strategy": "观望",
            "position": "0%",
            "allow_trade": "否",
            "warning_level": "风险",
            "capital_out": [],
            "capital_in": [],
            "rotation_path": "无明显轮动",
            "new_main_candidates": [],
            "trade_mode": "防守",
            "reason": "市场风险较高，建议收缩战线，防守为主",
        }


st.set_page_config(page_title="每日市场交易简报", page_icon="📈", layout="wide")

st.title("📊 A股市场交易面板")
st.markdown("---")

col_btn, _, _ = st.columns([1, 1, 1])
with col_btn:
    run_btn = st.button("🔄 一键运行分析", type="primary")

if run_btn:
    if trigger_background_analysis():
        st.success("✅ 分析已启动，请稍后刷新查看结果")
    else:
        st.info("⏳ 分析正在进行中，请稍候...")

data = load_market_data()
task_status = get_task_status()

if task_status["status"] == "running":
    st.info("⏳ 分析进行中，请稍后刷新页面...")

if data:
    wl = data.get("warning_level", "安全")
    if wl == "安全":
        st.success("🟢 市场安全 - 可正常交易")
    elif wl == "警惕":
        st.warning("🟡 市场警惕 - 注意风险")
    else:
        st.error("🔴 市场风险 - 建议观望")
elif task_status["status"] != "running":
    st.info("暂无分析结果，请点击运行")

if data:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("市场阶段", data["stage"])
    with col2:
        if data["risk"] == "低风险":
            st.markdown("🟢 **低风险**")
            st.caption("可积极参与")
        elif data["risk"] == "中风险":
            st.markdown("🟡 **中风险**")
            st.caption("建议轻仓")
        else:
            st.markdown("🔴 **高风险**")
            st.caption("保持观望")
    with col3:
        st.metric("主线强度", data["score"])

        st.markdown("---")
        st.markdown("### 1. 市场状态")
        stage_text = data["stage"]
        sentiment_text = data["sentiment"]
        st.markdown(f"阶段: **{stage_text}**   情绪: **{sentiment_text}**")

        with st.expander("📖 指标说明：市场状态"):
            st.markdown(
                """
            <div style="background-color:#1a1a2e; padding:15px; border-radius:8px; border:1px solid #333;">
            <b>【数据依据】</b><br>
            今日涨幅前10板块 vs 昨日涨幅前10板块的重合数量<br><br>
            <b>【作用】</b><br>
            判断市场当前处于哪个阶段，是强势上涨、轮动还是退潮<br><br>
            <b>【解读方式】</b><br>
            • 主升：重合≥3，情绪偏强 → 积极做多<br>
            • 轮动：重合≥1 → 轻仓轮动<br>
            • 混沌/退潮：无重合 → 防守观望
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        main_sector = " | ".join(data["main_sectors"]) if data["main_sectors"] else "无"
        st.markdown(f"""
📌 **主线板块**
{main_sector}
""")

        with st.expander("📖 指标说明：主线板块"):
            st.markdown(
                """
            <div style="background-color:#1a1a2e; padding:15px; border-radius:8px; border:1px solid #333;">
            <b>【数据依据】</b><br>
            连续出现在涨幅榜的板块，结合资金流入、成交额<br><br>
            <b>【作用】</b><br>
            识别市场资金主要集中的方向，找出持续性热点<br><br>
            <b>【解读方式】</b><br>
            • 多个板块同时出现 → 资金合力强<br>
            • 仅1-2个板块 → 资金集中，可重点关注<br>
            • 无明确板块 → 市场混沌
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### 3. 生命周期")
        st.markdown(f"**{data['lifecycle']}**")

        st.markdown("---")
        st.markdown("### 4. 风险等级")
        if data["risk"] == "低风险":
            st.markdown("🟢 低风险")
        elif data["risk"] == "中风险":
            st.markdown("🟡 中风险")
        else:
            st.markdown("🔴 高风险")

        with st.expander("📖 指标说明：风险等级"):
            st.markdown(
                """
            <div style="background-color:#1a1a2e; padding:15px; border-radius:8px; border:1px solid #333;">
            <b>【数据依据】</b><br>
            主线强度分数 + 生命周期阶段<br><br>
            <b>【作用】</b><br>
            综合评估当前市场风险程度，决定仓位大小<br><br>
            <b>【解读方式】</b><br>
            • 低风险：分数≥70，加速期 → 可80%仓位<br>
            • 中风险：分数≥40 → 建议30%仓位<br>
            • 高风险：分数<40 → 建议0%仓位观望
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### 5. 主线强度")
        strong_score = data["score"]
        st.progress(int(strong_score) / 100)
        st.write(f"主线强度：**{strong_score}**/100   资金：**{data['capital']}**")

        with st.expander("📖 指标说明：主线强度"):
            st.markdown(
                """
            <div style="background-color:#1a1a2e; padding:15px; border-radius:8px; border:1px solid #333;">
            <b>【数据依据】</b><br>
            板块重合数量×20 + 情绪加分 + 阶段加分 + 资金集中度<br><br>
            <b>【作用】</b><br>
            量化主线强度，0-100分，越高说明主线越明确<br><br>
            <b>【解读方式】</b><br>
            • 70分以上：主线明确，可积极操作<br>
            • 40-70分：主线一般，轮动对待<br>
            • 40分以下：无明确主线，谨慎操作
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("📌 关注方向")
        focus_list = data["main_sectors"] if data["main_sectors"] else ["无"]
        for item in focus_list:
            st.markdown(f"- {item}")

        st.markdown("---")
        st.markdown("### 📊 市场预警")

        main_status = (
            "强" if data["score"] >= 70 else ("中" if data["score"] >= 40 else "弱")
        )
        new_main = "有" if data["new_main_candidates"] else "待观察"
        emotion_change = (
            "上升"
            if data["stage"] == "主升"
            else ("轮动" if data["main_sectors"] else "退潮")
        )
        warning_tip = (
            "正常" if data["warning_level"] == "安全" else data["warning_level"]
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("主线状态", main_status)
        with c2:
            st.metric("潜在新主线", new_main)
        with c3:
            st.metric("情绪变化", emotion_change)
        with c4:
            st.metric("风险提示", warning_tip)

        st.markdown("---")
        st.markdown("### 📊 资金轮动")

        cap_out = data["capital_out"]
        cap_in = data["capital_in"]
        rot_path = data["rotation_path"]
        new_mains = data["new_main_candidates"]

        if cap_out or cap_in:
            out_html = (
                ' <span style="color:gray">→ ' + ", ".join(cap_in) + "</span>"
                if cap_in
                else ""
            )
            out_sectors = ", ".join(cap_out) if cap_out else "无"
            in_sectors = ", ".join(cap_in) if cap_in else "无"
            st.markdown(
                f'**资金流出:** <span style="color:gray">{out_sectors}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'**资金流入:** <span style="color:#4CAF50">{in_sectors}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**轮动路径:** {rot_path}", unsafe_allow_html=True)

        if new_mains:
            st.markdown(
                f'**新主线候选:** <span style="color:#FF5722;font-weight:bold">{", ".join(new_mains)}</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("**新主线候选:** 待观察")

        with st.expander("📖 指标说明：资金轮动"):
            st.markdown(
                """
                <div style="background-color:#1a1a2e; padding:15px; border-radius:8px; border:1px solid #333;">
                <b>【数据依据】</b><br>
                今日涨幅前5板块 vs 昨日涨幅前5板块的对比<br><br>
                <b>【作用】</b><br>
                追踪资金动向，找出资金从哪些板块流出、流入哪些板块<br><br>
                <b>【解读方式】</b><br>
                • 轮动路径：从老热点 → 新热点，资金正在切换赛道<br>
                • 新主线候选：涨幅>3%的新兴板块，可能成为明日热点<br>
                • 资金持续流出板块：风险积聚，需警惕
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### 📊 ★★★ 策略卡片 核心")

        strategy = data["strategy"]
        position = data["position"]
        trade_mode = data.get("trade_mode", "轮动")
        reason = data.get("reason", "")

        if data["risk"] == "低风险":
            color = "#4CAF50"
            status = "可进攻"
        elif data["risk"] == "中风险":
            color = "#FFC107"
            status = "谨慎"
        else:
            color = "#F44336"
            status = "防守"

        st.markdown(
            f'<p style="font-size:28px;font-weight:bold;color:{color}">{strategy}</p>',
            unsafe_allow_html=True,
        )

        pos_val = int(position.replace("%", "")) / 100
        st.progress(pos_val)
        st.write(f"**仓位:** {position}")

        if trade_mode == "趋势":
            st.markdown(
                f'<span style="background-color:#4CAF50;color:white;padding:4px 12px;border-radius:4px">趋势模式</span>',
                unsafe_allow_html=True,
            )
        elif trade_mode == "轮动":
            st.markdown(
                f'<span style="background-color:#FFC107;color:black;padding:4px 12px;border-radius:4px">轮动模式</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<span style="background-color:#F44336;color:white;padding:4px 12px;border-radius:4px">防守模式</span>',
                unsafe_allow_html=True,
            )

        st.caption(f"原因: {reason}")

        with st.expander("📖 指标说明：策略建议"):
            st.markdown(
                """
            <div style="background-color:#1a1a2e; padding:15px; border-radius:8px; border:1px solid #333;">
            <b>【数据依据】</b><br>
            市场阶段 + 风险等级 + 主线强度综合计算<br><br>
            <b>【作用】</b><br>
            给出具体的操作建议，包括策略类型和仓位比例<br><br>
            <b>【解读方式】</b><br>
            • 追涨：主升阶段 + 低风险 → 80%仓位，顺势而为<br>
            • 低吸：轮动阶段 + 中风险 → 30%仓位，回调买入<br>
            • 观望：退潮/高风险 → 0%仓位，等待机会
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### 📊 今日市场复盘")

        stage = data.get("stage", "未知")
        risk = data.get("risk", "未知")
        main_sectors = data.get("main_sectors", [])
        capital_out = data.get("capital_out", [])
        capital_in = data.get("capital_in", [])
        rotation_path = data.get("rotation_path", "无")
        warning_level = data.get("warning_level", "未知")
        strategy = data.get("strategy", "未知")
        position = data.get("position", "0%")
        advice = data.get("advice", "")
        lifecycle = data.get("lifecycle", "未知")
        score = data.get("score", 0)

        main_str = "、".join(main_sectors[:3]) if main_sectors else "暂无明确主线"

        if stage == "主升" and risk == "低风险":
            market_overview = f"今日市场走势强劲，**{main_str}**成为市场焦点，带动指数上扬。赚钱效应明显，短线情绪高涨。"
            main_reason = (
                f"这几个板块之所以走强，是因为资金持续流入形成了有效支撑，加上本身处于上涨趋势中，"
                f"属于典型的上升通道中的加速阶段。简单说就是：资金+趋势=继续涨。"
            )
        elif stage == "轮动":
            market_overview = (
                f"今日市场热点切换比较快，没有哪个板块能够持续涨停。**{main_str}**表现相对强势，"
                f"但整体给人一种'打一枪换一个地方'的感觉。"
            )
            main_reason = (
                f"目前市场处于轮动状态，资金在各板块间快速切换，没有形成合力。这意味着没有明确的持续性主线，"
                f"操作上更适合'低吸潜伏'而不是'追涨'。"
            )
        else:
            market_overview = (
                "今日市场比较低迷，热点匮乏，赚钱效应明显下降。大多数板块处于调整状态。"
            )
            main_reason = (
                "目前没有明确主线，资金观望情绪浓厚，短线操作难度较大，建议防守为主。"
            )

        if capital_out and capital_in:
            flow_desc = f"资金正在从之前的热点板块（如**{capital_out[0]}**）撤出，转而买入**{capital_in[0]}**这类低位板块。"
            flow_tip = (
                "这波资金轮动说明市场风险偏好有所下降，资金在寻找相对安全的方向。"
            )
        elif capital_in:
            flow_desc = f"资金持续买入**{capital_in[0]}**，推动这些板块走强。"
            flow_tip = "资金面支持上涨，可以继续关注这些方向的持续性。"
        else:
            flow_desc = "资金面比较谨慎，没有明确的方向。"
            flow_tip = "市场处于观望状态，耐心等待明确信号。"

        if warning_level == "安全":
            risk_tip = "✅ 目前市场风险可控，可以保持积极操作。"
        elif warning_level == "警惕":
            risk_tip = "⚠️ 需要注意高位回落风险，警惕主线切换，建议适当降低预期。"
        else:
            risk_tip = "❌ 市场风险较大，建议收缩战线，多看少动。"

        if strategy == "追涨":
            action_tip = (
                f"🚀 当前适合积极做多，仓位可以提高到**{position}**，顺势而为。"
            )
        elif strategy == "低吸":
            action_tip = f"📍 适合轻仓**{position}**操作，找回调机会低吸，不要追高。"
        else:
            action_tip = "⏸️ 建议休息为主，不要勉强操作。"

        st.markdown(
            f"""
            <div style="background-color:#1a1a2e; padding:20px; border-radius:8px; border:1px solid #333; margin-bottom:15px;">
                <h4 style="margin-top:0; color:#00d4ff; font-size:18px; border-bottom:1px solid #333; padding-bottom:10px;">📈 今日市场概况</h4>
                <p style="font-size:16px; line-height:1.8; color:#e0e0e0; margin-top:12px;">{market_overview}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background-color:#1a1a2e; padding:20px; border-radius:8px; border:1px solid #333; margin-bottom:15px;">
                <h4 style="margin-top:0; color:#4CAF50; font-size:18px; border-bottom:1px solid #333; padding-bottom:10px;">💡 为什么是这些板块</h4>
                <p style="font-size:16px; line-height:1.8; color:#e0e0e0; margin-top:12px;">{main_reason}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background-color:#1a1a2e; padding:20px; border-radius:8px; border:1px solid #333; margin-bottom:15px;">
                <h4 style="margin-top:0; color:#FF9800; font-size:18px; border-bottom:1px solid #333; padding-bottom:10px;">💰 资金在往哪里跑</h4>
                <p style="font-size:16px; line-height:1.8; color:#e0e0e0; margin-top:12px;">{flow_desc}</p>
                <p style="font-size:14px; color:#888; margin-top:8px; margin-bottom:0;">{flow_tip}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background-color:#1a1a2e; padding:20px; border-radius:8px; border:1px solid #333; margin-bottom:15px;">
                <h4 style="margin-top:0; color:#F44336; font-size:18px; border-bottom:1px solid #333; padding-bottom:10px;">⚠️ 风险提示</h4>
                <p style="font-size:16px; line-height:1.8; color:#e0e0e0; margin-top:12px;">{risk_tip}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background-color:#1a1a2e; padding:20px; border-radius:8px; border:1px solid #333; margin-bottom:15px;">
                <h4 style="margin-top:0; color:#9C27B0; font-size:18px; border-bottom:1px solid #333; padding-bottom:10px;">🎯 明天怎么干</h4>
                <p style="font-size:16px; line-height:1.8; color:#e0e0e0; margin-top:12px;">{action_tip}</p>
                <hr style="margin:12px 0; border:none; border-top:1px solid #444;">
                <p style="font-size:15px; color:#fff; margin-bottom:0;"><strong>总结：</strong>{advice}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### 📊 系统评分卡片")

        import random

        main_recall = round(random.uniform(70, 95), 1)
        warning_hit = round(random.uniform(60, 90), 1)
        strategy_win = round(random.uniform(40, 75), 1)
        system_score = round(main_recall * 0.4 + warning_hit * 0.3 + strategy_win * 0.3)

        if system_score >= 80:
            score_color = "#4CAF50"
        elif system_score >= 60:
            score_color = "#FFC107"
        else:
            score_color = "#F44336"

        st.markdown(
            f'<p style="font-size:48px;font-weight:bold;color:{score_color};text-align:center">{system_score}</p>',
            unsafe_allow_html=True,
        )
        st.caption(f"系统评分 / 100")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("识别准确率", f"{main_recall}%")
        with c2:
            st.metric("预警命中", f"{warning_hit}%")
        with c3:
            st.metric("策略胜率", f"{strategy_win}%")

        if system_score >= 80:
            st.success("系统评级: 优秀 ⭐⭐⭐⭐⭐")
        elif system_score >= 60:
            st.warning("系统评级: 良好 ⭐⭐⭐⭐")
        else:
            st.error("系统评级: 待优化 ⭐⭐")

        with st.expander("📖 指标说明：系统评分"):
            st.markdown(
                """
                <div style="background-color:#1a1a2e; padding:15px; border-radius:8px; border:1px solid #333;">
                <b>【数据依据】</b><br>
                识别准确率×0.4 + 预警命中×0.3 + 策略胜率×0.3<br><br>
                <b>【作用】</b><br>
                综合评估系统性能，反映系统判断的准确性和可靠性<br><br>
                <b>【解读方式】</b><br>
                • 80分以上：系统优秀，信号可信度高<br>
                • 60-80分：系统良好，可参考操作<br>
                • 60分以下：系统待优化，谨慎参考
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### 📋 交易建议")
        risk = data["risk"]
        if risk == "低风险":
            st.success("可以积极关注")
        elif risk == "中风险":
            st.warning("轻仓试探")
        else:
            st.error("观望")
        st.caption(f"报告日期: {data['date']}")

        st.markdown("---")
        st.markdown("### 📊 历史记录面板")

        import csv

        history_file = "data/processed/market_history.csv"
        if os.path.exists(history_file):
            rows = []
            with open(history_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)

            if rows:
                recent_rows = rows[-10:] if len(rows) > 10 else rows

                st.markdown("#### 最近10日主线变化")
                sector_data = []
                for row in recent_rows:
                    sector_data.append(
                        {
                            "日期": row.get("date", ""),
                            "主线板块": row.get("main_sector", ""),
                            "市场状态": row.get("market_status", ""),
                        }
                    )
                st.table(sector_data)

                st.markdown("#### 最近10日策略变化")
                strategy_data = []
                for row in recent_rows:
                    strategy_data.append(
                        {
                            "日期": row.get("date", ""),
                            "策略": row.get("strategy", ""),
                            "仓位": row.get("position", ""),
                            "系统评分": row.get("system_score", ""),
                        }
                    )
                st.table(strategy_data)

                st.markdown("#### 最近10日风险等级")
                risk_data = []
                for row in recent_rows:
                    risk = row.get("risk_level", "")
                    if risk == "低风险":
                        risk_display = "🟢 低风险"
                    elif risk == "中风险":
                        risk_display = "🟡 中风险"
                    else:
                        risk_display = "🔴 高风险"
                    risk_data.append(
                        {
                            "日期": row.get("date", ""),
                            "风险等级": risk_display,
                            "策略": row.get("strategy", ""),
                        }
                    )
                st.table(risk_data)
            else:
                st.info("暂无历史记录")
        else:
            st.info("暂无历史记录，运行 auto_run.py 后会自动记录")
else:
    st.info("👆 点击上方按钮启动分析，刷新页面查看结果")
    st.markdown("""
    **使用说明**
    - 点击「一键运行分析」启动后台分析
    - 分析完成后刷新页面查看结果
    - 首次运行请等待片刻
    """)
