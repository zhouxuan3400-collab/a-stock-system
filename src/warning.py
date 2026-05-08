# -*- coding: utf-8 -*-
def analyze_warning(
    historical_data, prev_stage, common_sectors_count, yesterday_main_count
):
    warning_level = "正常"
    new_candidates = 0

    if historical_data and prev_stage == "主升" and common_sectors_count < 3:
        warning_level = "警惕"

    if historical_data:
        if new_candidates >= 3:
            warning_level = "警惕"

    if (
        prev_stage == "主升"
        and common_sectors_count < 3
        and yesterday_main_count > 0
        and common_sectors_count < yesterday_main_count
    ):
        warning_level = "警惕"

    return warning_level


def calculate_risk(score, lifecycle):
    if score >= 70 and lifecycle == "加速期":
        risk = "低风险"
    elif score >= 40:
        risk = "中风险"
    else:
        risk = "高风险"
    return risk


def calculate_warning(score, lifecycle, yesterday_main_count, common_sectors_count):
    if score >= 70 and lifecycle == "加速期":
        warning = "安全"
    elif lifecycle == "分歧期" or (
        yesterday_main_count > 0 and common_sectors_count < yesterday_main_count
    ):
        warning = "警惕"
    else:
        warning = "危险"
    return warning
