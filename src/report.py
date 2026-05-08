# -*- coding: utf-8 -*-


def generate_human_readable_reflection(
    stage="未知",
    sentiment="未知",
    main_sectors=None,
    capital_out=None,
    capital_in=None,
    rotation_path="无明显轮动",
    risk="未知",
    warning_level="未知",
    strategy="观望",
    position="0%",
    advice="观望为主",
    lifecycle="未知",
    score=0,
):
    if main_sectors is None:
        main_sectors = []
    if capital_out is None:
        capital_out = []
    if capital_in is None:
        capital_in = []

    lines = []
    lines.append("=" * 50)
    lines.append("📊 AI市场复盘（人话版）")
    lines.append("=" * 50)

    main_str = "、".join(main_sectors[:3]) if main_sectors else "暂无明确主线"

    if stage == "主升" and risk == "低风险":
        market_overview = f"今天市场走势强劲，{main_str}成为市场焦点，带动指数上扬。赚钱效应明显，短线情绪高涨。"
        main_reason = (
            f"这几个板块之所以走强，是因为资金持续流入形成了有效支撑，加上本身处于上涨趋势中，"
            f"属于典型的上升通道中的加速阶段。简单说就是：资金+趋势=继续涨。"
        )
    elif stage == "轮动":
        market_overview = (
            f"今天市场热点切换比较快，没有哪个板块能够持续涨停。{main_str}表现相对强势，"
            f"但整体给人一种'打一枪换一个地方'的感觉。"
        )
        main_reason = (
            f"目前市场处于轮动状态，资金在各板块间快速切换，没有形成合力。这意味着没有明确的持续性主线，"
            f"操作上更适合'低吸潜伏'而不是'追涨'。"
        )
    else:
        market_overview = (
            "今天市场比较低迷，热点匮乏，赚钱效应明显下降。大多数板块处于调整状态。"
        )
        main_reason = (
            "目前没有明确主线，资金观望情绪浓厚，短线操作难度较大，建议防守为主。"
        )

    if capital_out and capital_in:
        flow_desc = f"资金正在从之前的热点板块（如{capital_out[0]}）撤出，转而买入{capital_in[0]}这类低位板块。"
        flow_tip = f"这波资金轮动说明市场风险偏好有所下降，资金在寻找相对安全的方向。"
    elif capital_in:
        flow_desc = f"资金持续买入{capital_in[0]}，推动这些板块走强。"
        flow_tip = "资金面支持上涨，可以继续关注这些方向的持续性。"
    else:
        flow_desc = "资金面比较谨慎，没有明确的方向。"
        flow_tip = "市场处于观望状态，耐心等待明确信号。"

    if warning_level == "安全":
        risk_tip = "目前市场风险可控，可以保持积极操作。"
    elif warning_level == "警惕":
        risk_tip = "需要注意高位回落风险，警惕主线切换，建议适当降低预期。"
    else:
        risk_tip = "市场风险较大，建议收缩战线，多看少动。"

    if strategy == "追涨":
        action_tip = f"当前适合积极做多，仓位可以提高到{position}，顺势而为。"
    elif strategy == "低吸":
        action_tip = f"适合轻仓{position}操作，找回调机会低吸，不要追高。"
    else:
        action_tip = "建议休息为主，不要勉强操作。"

    lines.append("")
    lines.append("【今日市场概况】")
    lines.append(market_overview)
    lines.append("")
    lines.append("【为什么是这些板块】")
    lines.append(main_reason)
    lines.append("")
    lines.append("【资金在往哪里跑】")
    lines.append(flow_desc)
    lines.append(flow_tip)
    lines.append("")
    lines.append("【风险提示】")
    lines.append(risk_tip)
    lines.append("")
    lines.append("【明天怎么干】")
    lines.append(action_tip)
    lines.append("")
    lines.append(f"总结：{advice}")
    lines.append("=" * 50)

    return "\n".join(lines)


def generate_market_reflection_v8(
    main_sectors,
    confidence_score,
    stage,
    sentiment,
    capital_out,
    capital_in,
    rotation_path,
    risk,
    warning_level,
    strategy,
    position,
    advice,
    lifecycle,
    new_main_candidates,
):
    lines = []
    lines.append("=" * 50)
    lines.append("📊 V8 AI复盘引擎")
    lines.append("=" * 50)

    main_str = ", ".join(main_sectors[:3]) if main_sectors else "无主线"

    if stage == "主升":
        what_happened = (
            f"市场处于强势上涨阶段，{main_str}领涨两市，资金持续净流入，市场情绪偏强"
        )
        why_main = (
            f"主线板块具备以下特征：①资金持续流入形成支撑；②板块强度≥70分，可信度{confidence_score}%；"
            f"③生命周期处于{lifecycle}，上涨趋势明确"
        )
    elif stage == "轮动":
        what_happened = f"市场热点快速轮动，{main_str}等板块轮番表现，无明确持续主线"
        why_main = (
            f"当前主线特征：①资金在多个板块间切换；②板块轮动频率较高；③生命周期处于{lifecycle}，"
            f"需观察持续性；可信度{confidence_score}%"
        )
    else:
        what_happened = "市场处于震荡调整期，热点匮乏，赚钱效应减弱"
        why_main = "无明确主线，资金观望情绪浓厚，板块可信度较低"

    if capital_out and capital_in:
        capital_flow = f"资金从{capital_out[0]}等板块流出，净流入{capital_in[0]}等方向，轮动路径：{rotation_path}"
    elif capital_in:
        capital_flow = f"资金净流入{capital_in[0]}等板块，推动板块上涨"
    else:
        capital_flow = "资金流动方向不明确，整体呈观望态势"

    if warning_level == "安全":
        risk_point = "风险较低，关注主线持续性即可"
    elif warning_level == "警惕":
        risk_point = "需警惕主线切换风险，注意高位回落风险"
    else:
        risk_point = "风险较高，建议收缩战线，防守为主"

    if risk == "低风险" and stage == "主升":
        focus_tomorrow = f"可积极参与{strategy}策略，建议仓位{position}，{advice}"
    elif risk == "中风险":
        focus_tomorrow = (
            f"轻仓参与，关注{capital_in[0] if capital_in else '主线'}方向，{advice}"
        )
    else:
        focus_tomorrow = "建议观望为主，不宜激进操作，控制风险"

    lines.append("📊 今日市场复盘：")
    lines.append(f"1. 市场发生了什么（结构总结）\n   {what_happened}")
    lines.append(f"2. 主线为什么是当前板块（逻辑解释）\n   {why_main}")
    lines.append(f"3. 资金如何流动（轮动路径）\n   {capital_flow}")
    lines.append(f"4. 当前风险点是什么\n   {risk_point}")
    lines.append(f"5. 明日交易关注点\n   {focus_tomorrow}")
    lines.append("=" * 50)

    return "\n".join(lines)
