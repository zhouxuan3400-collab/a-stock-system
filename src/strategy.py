# -*- coding: utf-8 -*-
def generate_strategy(stage, score, risk, lifecycle):
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

    if risk == "低风险":
        advice = "可积极参与主线板块，设好止损持有"
    elif risk == "中风险":
        advice = "轻仓参与，关注资金流向变化"
    else:
        advice = "观望为主，不宜激进操作"

    return strategy, position, allow_trade, advice


def generate_trade_mode(stage, score, risk, capital_out, capital_in):
    if capital_out and capital_in:
        trade_mode = "轮动"
        reason = f"资金轮动活跃，从{capital_out[0]}轮动至{capital_in[0]}，适合短差操作"
    elif stage == "主升" and score >= 70:
        trade_mode = "趋势"
        reason = "市场处于主升阶段，趋势明确，可顺势追涨"
    elif risk == "高风险" or stage == "混沌/退潮":
        trade_mode = "防守"
        reason = "市场风险较高，建议收缩战线，防守为主"
    else:
        trade_mode = "轮动"
        reason = "市场处于轮动状态，建议轻仓短差"

    return trade_mode, reason
