# -*- coding: utf-8 -*-
def analyze_rotation(yesterday_sectors, top_10):
    capital_out = []
    capital_in = []
    rotation_path = "无明显轮动"

    if not yesterday_sectors:
        return capital_out, capital_in, rotation_path

    today_top_names = [s.get("f14", "") for s in top_10[:5]]
    yesterday_top_names = list(yesterday_sectors)[:5]

    outflow = set(yesterday_top_names) - set(today_top_names)
    inflow = set(today_top_names) - set(yesterday_top_names)

    capital_out = list(outflow)[:3] if outflow else []
    capital_in = list(inflow)[:3] if inflow else []

    if capital_out and capital_in:
        rotation_path = f"{capital_out[0]} → {capital_in[0]}"

    return capital_out, capital_in, rotation_path


def get_new_main_candidates(top_10):
    return [s.get("f14", "") for s in top_10[:3] if s.get("f3", 0) > 3]
