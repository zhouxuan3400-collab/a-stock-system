# -*- coding: utf-8 -*-
import os
import csv
import time
import requests
import urllib3
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def safe_request(url, params=None, max_retries=3):
    session = requests.Session()

    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
        "Origin": "https://quote.eastmoney.com",
        "Accept": "application/json,text/plain,*/*",
        "Connection": "keep-alive",
    }

    try:
        response = session.get(
            url, params=params, headers=headers, timeout=20, verify=False
        )

        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"safe_request failed: {e}")
        return None


def fetch_sector_data():
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
    try:
        data = safe_request(url, params=params)
        if data is None:
            print("数据获取失败")
            return [], datetime.now().strftime("%Y-%m-%d")
        sectors = data["data"]["diff"]
        sectors_sorted = sorted(sectors, key=lambda x: x.get("f3", 0), reverse=True)
        top_10 = sectors_sorted[:10]
        today = datetime.now().strftime("%Y-%m-%d")
        os.makedirs("data/raw", exist_ok=True)
        with open("data/raw/sector_rank.csv", "w", encoding="utf-8") as f:
            f.write("日期,排名,板块名称,涨跌幅,成交额\n")
            for i, sector in enumerate(top_10, 1):
                name = sector.get("f14") or "未知板块"
                change_pct = sector.get("f3") if sector.get("f3") is not None else 0
                amount = sector.get("f62") if sector.get("f62") is not None else 0
                f.write(f'{today},{i},"{name}",{change_pct},{amount}\n')
        return top_10, today
    except Exception as e:
        print(f"数据获取失败: {e}")
        return [], datetime.now().strftime("%Y-%m-%d")


def load_today_sectors(top_10):
    today_sectors = {}
    for sector in top_10:
        name = sector.get("f14") or "未知板块"
        today_sectors[name] = {
            "f14": name,
            "f3": sector.get("f3") if sector.get("f3") is not None else 0,
            "f62": sector.get("f62") if sector.get("f62") is not None else 0,
        }
    return today_sectors


def get_today_avg(top_10):
    if not top_10:
        return 0
    return sum(s.get("f3", 0) for s in top_10) / len(top_10)


def load_historical_data():
    historical_data = []
    for day_offset in range(1, 4):
        hist_file = f"data/processed/sector_rank_{day_offset}days.csv"
        if os.path.exists(hist_file):
            with open(hist_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["板块名称"] = row.get("板块名称") or "未知板块"
                    row["涨跌幅"] = float(row.get("涨跌幅") or 0)
                    row["成交额"] = float(row.get("成交额") or 0)
                    row["排名"] = row.get("排名") or "99"
                    historical_data.append(row)
    return historical_data


def load_yesterday_sectors():
    yesterday_file = "data/processed/sector_rank_yesterday.csv"
    yesterday_sectors = set()
    yesterday_main_count = 0
    if os.path.exists(yesterday_file):
        with open(yesterday_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sector_name = row.get("板块名称") or "未知板块"
                yesterday_sectors.add(sector_name)
        yesterday_main_count = len(yesterday_sectors)
    return yesterday_sectors, yesterday_main_count


def load_prev_stage():
    prev_stage = None
    if os.path.exists("data/processed/sector_stage_history.csv"):
        with open(
            "data/processed/sector_stage_history.csv", "r", encoding="utf-8"
        ) as f:
            prev_stage = f.read().strip()
    return prev_stage
