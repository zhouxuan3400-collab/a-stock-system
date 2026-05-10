"""
🧠 数据健康检测（防0数据污染）
"""


def validate_market_data(data):
    """
    检查数据是否有效
    """

    if not data:
        return False, "empty_data"

    values = [
        data.get("上涨家数", 0),
        data.get("下跌家数", 0),
        data.get("涨停数", 0),
        data.get("跌停数", 0),
        data.get("成交额", 0),
    ]

    if sum(values) == 0:
        return False, "all_zero_data"

    return True, "ok"
