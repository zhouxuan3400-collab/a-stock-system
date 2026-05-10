"""
🧠 数据服务层（健康检查版）
"""

from data.health_check import validate_market_data


def get_market_data():
    try:
        from data.provider import get_market_snapshot

        data = get_market_snapshot()

        ok, reason = validate_market_data(data)

        if not ok:
            return {
                "上涨家数": "数据异常",
                "下跌家数": "数据异常",
                "涨停数": "数据异常",
                "跌停数": "数据异常",
                "成交额": "数据异常",
                "成交额变化": "数据异常",
                "status": reason,
            }

        return data

    except Exception as e:
        return {
            "上涨家数": "数据异常",
            "下跌家数": "数据异常",
            "涨停数": "数据异常",
            "跌停数": "数据异常",
            "成交额": "数据异常",
            "成交额变化": "数据异常",
            "error": str(e),
            "status": "fetch_failed",
        }
