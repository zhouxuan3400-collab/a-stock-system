# -*- coding: utf-8 -*-
import random
import pandas as pd
from datetime import datetime, timedelta


def get_fallback_boards():
    return [
        {"name": "人工智能", "change": 5.2, "amount": 5000000000},
        {"name": "新能源", "change": 3.8, "amount": 8000000000},
        {"name": "半导体", "change": 3.5, "amount": 6000000000},
        {"name": "医药", "change": 2.9, "amount": 4000000000},
        {"name": "汽车", "change": 2.5, "amount": 3000000000},
    ]


def get_fallback_market_snapshot():
    up_count = random.randint(1200, 2800)
    down_count = 5000 - up_count
    return {
        "up_count": up_count,
        "down_count": down_count,
        "limit_up": random.randint(30, 150),
        "limit_down": random.randint(0, 30),
        "total_amount": random.randint(500000000000, 1500000000000),
    }


def get_fallback_north_money():
    return random.uniform(-500000000, 1500000000)


def get_fallback_turnover_change():
    return random.uniform(-15, 25)


def get_fallback_stock_list():
    names = [
        "贵州茅台",
        "宁德时代",
        "比亚迪",
        "招商银行",
        "中国平安",
        "五粮液",
        "隆基绿能",
        "恒瑞医药",
        "海康威视",
        "美的集团",
    ]
    stocks = []
    for name in names:
        stocks.append(
            {
                "name": name,
                "code": "600000",
                "change": random.uniform(-2, 8),
                "amount": random.randint(500000000, 10000000000),
                "is_limit_up": random.random() > 0.8,
            }
        )
    return stocks


def get_fallback_board_stocks(board_name):
    stocks = []
    for i in range(15):
        stocks.append(
            {
                "name": f"{board_name}股票{i + 1}",
                "code": f"60{i:04d}",
            }
        )
    return stocks
