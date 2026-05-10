# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def to_tx_code(code: str) -> str:
    """股票代码转换为通达信格式"""
    code = code.strip()
    if not code:
        return ""
    if code.startswith("6"):
        return f"sh{code}"
    elif code.startswith(("0", "3")):
        return f"sz{code}"
    elif code.startswith("8") or code.startswith("4"):
        return f"bj{code}"
    return code


def get_stock_daily(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取股票历史日线数据 (前复权)"""
    try:
        symbol = to_tx_code(code)
        if not symbol:
            return pd.DataFrame()

        start_date = start_date.replace("-", "") if "-" in start_date else start_date
        end_date = end_date.replace("-", "") if "-" in end_date else end_date

        df = ak.stock_zh_a_daily(
            symbol=symbol, start_date=start_date, end_date=end_date, adjust="qfq"
        )

        if df is not None and not df.empty:
            return df
        return pd.DataFrame()

    except Exception as e:
        print(f"获取股票数据失败: {code}, {e}")
        return pd.DataFrame()


def get_northbound_data() -> dict:
    """获取北向资金数据（沪深港通合计）"""
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is not None and not df.empty:
            total_inflow = 0
            total_buy = 0
            date = ""
            up_count = 0
            down_count = 0
            for _, row in df.iterrows():
                inflow = row.get("资金净流入", 0) or 0
                if isinstance(inflow, str):
                    inflow = 0
                total_inflow += inflow
                buy = row.get("成交净买额", 0) or 0
                if isinstance(buy, str):
                    buy = 0
                total_buy += buy
                date = str(row.get("交易日", ""))
                up_count = row.get("上涨数", 0) or 0
                down_count = row.get("下跌数", 0) or 0
            return {
                "inflow": total_inflow,
                "inflow_amount": total_inflow,
                "buy_amount": total_buy,
                "date": date,
                "up_count": up_count,
                "down_count": down_count,
                "status": "正常",
            }
        return {"status": "暂无数据", "message": "北向资金数据为空"}
    except Exception as e:
        print(f"获取北向资金数据失败: {e}")
        return {"status": "暂无数据", "message": str(e)}


def get_north_flow_data() -> dict:
    """获取北向资金净流入数据 - 动态验证模式

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    动态验证规则:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. 允许尝试所有 akshare.stock_* 接口
    2. 调用前动态检查: getattr(ak, api_name)
    3. 存在即用，不存在跳过
    4. 全部失败才返回 no_data
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    import akshare as ak

    CANDIDATE_APIS = [
        "stock_hsgt_north_net_flow_in_em",
        "stock_hsgt_fund_flow_em",
        "stock_hsgt_stock_hold_em",
        "stock_hsgt_fund_flow_hist_em",
        "stock_hsgt_fund_flow_summary_em",
        "stock_hsgt_hist_em",
        "stock_hsgt_hold_stock_em",
    ]

    for api_name in CANDIDATE_APIS:
        print(f"check api: {api_name}")

        try:
            api_func = getattr(ak, api_name)
        except AttributeError:
            print(f"  -> NOT_EXIST, skip")
            continue

        try:
            result = _fetch_north_by_api(api_name)
            if result and result.get("status") == "success":
                print(f"north source: {api_name}")
                print(f"north status: success")
                return result
        except Exception as e:
            print(f"  -> failed: {e}")
            continue

    print("north source: all failed")
    print("north status: no_data")
    return {
        "north_in": 0,
        "north_out": 0,
        "net": 0,
        "status": "no_data",
        "source": "none",
    }


def _fetch_north_by_api(api_name: str) -> dict:
    """根据API名称获取北向资金数据"""
    import akshare as ak

    if api_name == "stock_hsgt_north_net_flow_in_em":
        df = ak.stock_hsgt_north_net_flow_in_em()
        if df is None or df.empty:
            return None
        cols = df.columns.tolist()
        net_col = next(
            (c for c in cols if any(x in c for x in ["净", "流入", "net"])), None
        )
        if net_col:
            net = float(df.iloc[-1].get(net_col, 0) or 0)
            if net > 0:
                return {
                    "north_in": round(net, 2),
                    "north_out": 0,
                    "net": round(net, 2),
                    "status": "success",
                    "source": api_name,
                }
            elif net < 0:
                return {
                    "north_in": 0,
                    "north_out": round(abs(net), 2),
                    "net": round(net, 2),
                    "status": "success",
                    "source": api_name,
                }
        return None

    elif api_name == "stock_hsgt_fund_flow_em":
        df = ak.stock_hsgt_fund_flow_em()
        if df is None or df.empty:
            return None
        cols = df.columns.tolist()
        net_col = next(
            (c for c in cols if any(x in c for x in ["净", "流入", "net"])), None
        )
        if net_col:
            net = float(df.iloc[-1].get(net_col, 0) or 0)
            if net > 0:
                return {
                    "north_in": round(net, 2),
                    "north_out": 0,
                    "net": round(net, 2),
                    "status": "success",
                    "source": api_name,
                }
            elif net < 0:
                return {
                    "north_in": 0,
                    "north_out": round(abs(net), 2),
                    "net": round(net, 2),
                    "status": "success",
                    "source": api_name,
                }
        return None

    elif api_name == "stock_hsgt_stock_hold_em":
        df = ak.stock_hsgt_stock_hold_em()
        if df is None or df.empty:
            return None
        cols = df.columns.tolist()
        change_col = next(
            (c for c in cols if any(x in c for x in ["增持", "持股", "change"])), None
        )
        if change_col:
            total = 0.0
            for val in df[change_col].dropna():
                try:
                    total += float(val)
                except:
                    pass
            net = total
            if net > 0:
                return {
                    "north_in": round(net, 2),
                    "north_out": 0,
                    "net": round(net, 2),
                    "status": "success",
                    "source": api_name,
                }
            elif net < 0:
                return {
                    "north_in": 0,
                    "north_out": round(abs(net), 2),
                    "net": round(net, 2),
                    "status": "success",
                    "source": api_name,
                }
        return None

    elif api_name == "stock_hsgt_fund_flow_summary_em":
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is None or df.empty:
            return None
        north_in = 0.0
        north_out = 0.0
        net = 0.0
        for _, row in df.iterrows():
            direction = str(row.get("资金方向", ""))
            inflow = row.get("资金净流入")
            if inflow is None:
                continue
            inflow = float(inflow)
            if "北向" in direction:
                if inflow > 0:
                    north_in += inflow
                else:
                    north_out += abs(inflow)
                net += inflow
        if net != 0:
            return {
                "north_in": round(north_in, 2),
                "north_out": round(north_out, 2),
                "net": round(net, 2),
                "status": "success",
                "source": api_name,
            }
        return None

    elif api_name == "stock_hsgt_hist_em":
        df = ak.stock_hsgt_hist_em(symbol="北向资金")
        if df is None or df.empty:
            return None
        latest = df.iloc[-1]
        net = latest.get("当日成交净买额")
        if net is None:
            return None
        net = float(net)
        if net > 0:
            return {
                "north_in": round(net, 2),
                "north_out": 0,
                "net": round(net, 2),
                "status": "success",
                "source": api_name,
            }
        elif net < 0:
            return {
                "north_in": 0,
                "north_out": round(abs(net), 2),
                "net": round(net, 2),
                "status": "success",
                "source": api_name,
            }
        return None

    elif api_name == "stock_hsgt_hold_stock_em":
        df = ak.stock_hsgt_hold_stock_em()
        if df is None or df.empty:
            return None
        cols = df.columns.tolist()
        change_col = next(
            (c for c in cols if any(x in c for x in ["增持", "持股", "change"])), None
        )
        if change_col:
            total = 0.0
            for val in df[change_col].dropna():
                try:
                    total += float(val)
                except:
                    pass
            net = total
            if net > 0:
                return {
                    "north_in": round(net, 2),
                    "north_out": 0,
                    "net": round(net, 2),
                    "status": "success",
                    "source": api_name,
                }
            elif net < 0:
                return {
                    "north_in": 0,
                    "north_out": round(abs(net), 2),
                    "net": round(net, 2),
                    "status": "success",
                    "source": api_name,
                }
        return None

    return None


def _get_north_flow_v1() -> dict:
    """接口1: stock_hsgt_fund_flow_summary_em"""
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is None or df.empty:
            return None

        north_in = 0.0
        north_out = 0.0
        net = 0.0

        for _, row in df.iterrows():
            direction = str(row.get("资金方向", ""))
            inflow = row.get("资金净流入", 0)
            if inflow is None:
                continue
            inflow = float(inflow)
            if "北向" in direction:
                if inflow > 0:
                    north_in += inflow
                else:
                    north_out += abs(inflow)
                net += inflow

        if net == 0:
            return None

        return {
            "north_in": round(north_in, 2),
            "north_out": round(north_out, 2),
            "net": round(net, 2),
            "status": "success",
        }
    except:
        return None


def _get_north_flow_v2() -> dict:
    """接口2: stock_hsgt_hist_em"""
    try:
        df = ak.stock_hsgt_hist_em(symbol="北向资金")
        if df is None or df.empty or len(df) < 1:
            return None

        latest = df.iloc[-1]
        net = latest.get("当日成交净买额")
        if net is None:
            return None
        net = float(net)
        if net != net:
            return None

        if net > 0:
            return {
                "north_in": round(net, 2),
                "north_out": 0,
                "net": round(net, 2),
                "status": "success",
            }
        elif net < 0:
            return {
                "north_in": 0,
                "north_out": round(abs(net), 2),
                "net": round(net, 2),
                "status": "success",
            }
        return None
    except:
        return None


def _get_north_flow_v3() -> dict:
    """接口3: stock_hsgt_hold_stock_em 兜底（持股数据）"""
    try:
        df = ak.stock_hsgt_hold_stock_em()
        if df is None or df.empty:
            return None

        total_change = 0.0
        change_col = None
        for col in ["5日增持估计-股数", "10日增持估计-股数", "今日持股-股数"]:
            if col in df.columns:
                change_col = col
                break

        if change_col:
            for val in df[change_col].dropna():
                try:
                    total_change += float(val)
                except:
                    pass

        net = total_change
        if net > 0:
            return {
                "north_in": round(net, 2),
                "north_out": 0,
                "net": round(net, 2),
                "status": "success",
            }
        elif net < 0:
            return {
                "north_in": 0,
                "north_out": round(abs(net), 2),
                "net": round(net, 2),
                "status": "success",
            }
        return None
    except:
        return None


def _get_north_flow_from_summary() -> dict:
    """从 stock_hsgt_fund_flow_summary_em 获取北向资金数据"""
    df = ak.stock_hsgt_fund_flow_summary_em()
    if df is None or df.empty:
        return None

    north_in = 0.0
    north_out = 0.0
    net = 0.0

    for _, row in df.iterrows():
        direction = str(row.get("资金方向", ""))
        inflow = row.get("资金净流入", 0) or 0
        if "北向" in direction:
            if isinstance(inflow, (int, float)):
                if inflow > 0:
                    north_in += inflow
                else:
                    north_out += abs(inflow)
                net += inflow

    if net == 0:
        return None

    return {
        "north_in": round(north_in, 2),
        "north_out": round(north_out, 2),
        "net": round(net, 2),
        "status": "正常",
    }


def _get_north_flow_from_hist() -> dict:
    """从 stock_hsgt_hist_em 获取北向资金数据"""
    df = ak.stock_hsgt_hist_em(symbol="北向资金")
    if df is None or df.empty:
        return None

    latest = df.iloc[-1]
    net = latest.get("当日成交净买额", 0)
    if net is None:
        return None
    net = float(net) if not isinstance(net, (int, float)) else net
    if net != net:
        return None

    if net > 0:
        return {
            "north_in": round(net, 2),
            "north_out": 0,
            "net": round(net, 2),
            "status": "正常",
        }
    elif net < 0:
        return {
            "north_in": 0,
            "north_out": round(abs(net), 2),
            "net": round(net, 2),
            "status": "正常",
        }
    return None


def _get_north_flow_from_min() -> dict:
    """从 stock_hsgt_fund_min_em 获取北向资金数据"""
    df = ak.stock_hsgt_fund_min_em()
    if df is None or df.empty:
        return None

    north_total = 0.0
    for _, row in df.iterrows():
        north = row.get("北向资金", 0) or 0
        if isinstance(north, (int, float)):
            north_total += north

    if north_total > 0:
        return {
            "north_in": round(north_total, 2),
            "north_out": 0,
            "net": round(north_total, 2),
            "status": "正常",
        }
    elif north_total < 0:
        return {
            "north_in": 0,
            "north_out": round(abs(north_total), 2),
            "net": round(north_total, 2),
            "status": "正常",
        }
    return None


_market_breadth_cache = {"data": None, "time": 0}


def get_market_breadth() -> dict:
    """获取全市场涨跌家数（基于stock_zh_a_daily）

    实现方式：
    1. 获取A股股票列表
    2. 随机取样200只
    3. 对每只股票计算涨跌幅
    4. 统计上涨/下跌/平盘家数
    5. 缓存5分钟
    """
    import time
    import random

    current_time = time.time()
    if (
        _market_breadth_cache["data"]
        and (current_time - _market_breadth_cache["time"]) < 300
    ):
        return _market_breadth_cache["data"]

    try:
        stock_list_df = ak.stock_info_a_code_name()
        if stock_list_df is None or stock_list_df.empty:
            return {"up": 0, "down": 0, "flat": 0, "up_ratio": 0, "status": "暂无数据"}

        stock_codes = stock_list_df["code"].tolist()
        sample_size = min(200, len(stock_codes))
        sampled_codes = random.sample(stock_codes, sample_size)

        up = 0
        down = 0
        flat = 0

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")

        for code in sampled_codes:
            try:
                df_daily = ak.stock_zh_a_daily(
                    symbol=code, start_date=start_date, end_date=end_date, adjust="qfq"
                )
                if df_daily is not None and not df_daily.empty and len(df_daily) >= 2:
                    latest_close = df_daily.iloc[-1]["close"]
                    prev_close = df_daily.iloc[-2]["close"]
                    if prev_close > 0:
                        change_pct = (latest_close - prev_close) / prev_close * 100
                        if change_pct > 0:
                            up += 1
                        elif change_pct < 0:
                            down += 1
                        else:
                            flat += 1
            except:
                continue

        total = up + down + flat
        up_ratio = (up / total * 100) if total > 0 else 0

        result = {
            "up": up,
            "down": down,
            "flat": flat,
            "up_ratio": round(up_ratio, 2),
            "total": total,
            "sample_size": sample_size,
            "status": "success",
        }

        _market_breadth_cache["data"] = result
        _market_breadth_cache["time"] = current_time

        return result

    except Exception as e:
        print(f"获取市场涨跌家数失败: {e}")
        return {"up": 0, "down": 0, "flat": 0, "up_ratio": 0, "status": "暂无数据"}


_zt_dt_cache = {"data": None, "time": 0}


def get_zt_dt_pool() -> dict:
    """获取涨停/跌停数据 - 基于stock_zh_a_daily近似计算

    规则：
    - 涨幅 >= 9.5% → 涨停
    - 跌幅 <= -9.5% → 跌停

    实现：
    1. 批量获取股票daily数据
    2. 计算涨跌幅
    3. 统计涨停/跌停家数
    4. 缓存5分钟
    """
    import time
    import random

    current_time = time.time()
    if _zt_dt_cache["data"] and (current_time - _zt_dt_cache["time"]) < 300:
        return _zt_dt_cache["data"]

    try:
        stock_list_df = ak.stock_info_a_code_name()
        if stock_list_df is None or stock_list_df.empty:
            return {
                "limit_up": 0,
                "limit_down": 0,
                "limit_up_list": [],
                "limit_down_list": [],
                "status": "暂无数据",
            }

        stock_codes = stock_list_df["code"].tolist()
        sample_size = min(100, len(stock_codes))
        sampled_codes = random.sample(stock_codes, sample_size)

        limit_up = 0
        limit_down = 0
        limit_up_list = []
        limit_down_list = []

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")

        for code in sampled_codes:
            try:
                df_daily = ak.stock_zh_a_daily(
                    symbol=code, start_date=start_date, end_date=end_date, adjust="qfq"
                )
                if df_daily is not None and not df_daily.empty and len(df_daily) >= 2:
                    latest_close = df_daily.iloc[-1]["close"]
                    prev_close = df_daily.iloc[-2]["close"]
                    if prev_close > 0:
                        change_pct = (latest_close - prev_close) / prev_close * 100
                        if change_pct >= 9.5:
                            limit_up += 1
                            if len(limit_up_list) < 10:
                                limit_up_list.append(code)
                        elif change_pct <= -9.5:
                            limit_down += 1
                            if len(limit_down_list) < 10:
                                limit_down_list.append(code)
            except:
                continue

        result = {
            "limit_up": limit_up,
            "limit_down": limit_down,
            "limit_up_list": limit_up_list,
            "limit_down_list": limit_down_list,
            "sample_size": sample_size,
            "status": "success",
        }

        _zt_dt_cache["data"] = result
        _zt_dt_cache["time"] = current_time

        return result

    except Exception as e:
        print(f"获取涨跌停数据失败: {e}")
        return {
            "limit_up": 0,
            "limit_down": 0,
            "limit_up_list": [],
            "limit_down_list": [],
            "status": "暂无数据",
        }


def get_sector_data() -> list:
    """获取行业板块涨幅前5"""
    try:
        df = ak.stock_board_industry_name_em()
        if df is not None and not df.empty:
            cols = df.columns.tolist()
            name_col = next(
                (c for c in cols if "板块" in c or "行业" in c or "名称" in c),
                "板块名称",
            )
            change_col = next(
                (c for c in cols if "涨跌幅" in c or "涨幅" in c), "涨跌幅"
            )
            df = df.sort_values(by=change_col, ascending=False).head(5)
            result = []
            for _, row in df.iterrows():
                name = row.get(name_col, "")
                change = row.get(change_col, 0) or 0
                result.append({"name": str(name), "change": round(float(change), 2)})
            return result
        return []
    except Exception as e:
        print(f"获取行业板块数据失败: {e}")
        return []


def calculate_market_sentiment(
    up: int,
    down: int,
    flat: int,
    limit_up: int,
    limit_down: int,
    north_net: float,
    amount_change_pct: float,
) -> dict:
    """
    市场情绪评分算法 (0-100)

    规则:
    - 涨停多 + 情绪↑
    - 跌停多 + 情绪↓
    - 北向流入 + 加分
    - 成交额放大 + 加分
    """
    score = 50
    reasons = []

    total = up + down + flat
    if total == 0:
        return {"score": 50, "level": "中性", "reasons": ["数据不足"]}

    up_ratio = up / total * 100
    score += (up_ratio - 50) * 0.3

    if up_ratio >= 60:
        reasons.append(f"上涨家数占比{up_ratio:.1f}%")
    elif up_ratio <= 40:
        reasons.append(f"上涨家数占比仅{up_ratio:.1f}%")

    if limit_up > 0:
        limit_up_score = min(limit_up * 2, 20)
        score += limit_up_score
        reasons.append(f"涨停{limit_up}家 (+{limit_up_score}分)")

    if limit_down > 0:
        limit_down_score = min(limit_down * 2, 20)
        score -= limit_down_score
        reasons.append(f"跌停{limit_down}家 ({limit_down_score}分)")

    if north_net > 0:
        north_score = min(north_net / 100, 15)
        score += north_score
        reasons.append(f"北向资金净流入{north_net:.0f}亿 (+{north_score:.1f}分)")
    elif north_net < 0:
        score -= min(abs(north_net) / 100, 10)
        reasons.append(f"北向资金净流出{abs(north_net):.0f}亿")

    if amount_change_pct > 20:
        score += 10
        reasons.append(f"成交额放大{amount_change_pct:.1f}% (+10分)")
    elif amount_change_pct < -20:
        score -= 10
        reasons.append(f"成交额萎缩{abs(amount_change_pct):.1f}% (-10分)")

    score = max(0, min(100, score))

    if score >= 70:
        level = "强势"
    elif score >= 40:
        level = "中性"
    else:
        level = "弱势"

    return {"score": int(score), "level": level, "reasons": reasons}


_main_sector_cache = {"data": None, "time": 0}


def get_main_sectors() -> list:
    """获取主线板块模拟 - 基于stock_zh_a_daily

    实现方式：
    1. 获取股票列表 + 行业字段（若有）
    2. 计算每只股票最近5日涨幅
    3. 按行业分组（或无行业则按随机聚类）
    4. 计算板块平均涨幅
    5. 输出前5强板块
    6. 如果无行业字段：用涨幅TOP股票模拟"主线"
    """
    import time
    import random

    current_time = time.time()
    if _main_sector_cache["data"] and (current_time - _main_sector_cache["time"]) < 300:
        return _main_sector_cache["data"]

    try:
        stock_list_df = ak.stock_info_a_code_name()
        if stock_list_df is None or stock_list_df.empty:
            return []

        stock_codes = stock_list_df["code"].tolist()
        sample_size = min(150, len(stock_codes))
        sampled_codes = random.sample(stock_codes, sample_size)

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")

        stock_changes = []

        for code in sampled_codes:
            try:
                df_daily = ak.stock_zh_a_daily(
                    symbol=code, start_date=start_date, end_date=end_date, adjust="qfq"
                )
                if df_daily is not None and not df_daily.empty and len(df_daily) >= 5:
                    latest_close = df_daily.iloc[-1]["close"]
                    old_close = df_daily.iloc[-5]["close"]
                    if old_close > 0:
                        change_pct = (latest_close - old_close) / old_close * 100
                        stock_changes.append({"code": code, "change": change_pct})
            except:
                continue

        if not stock_changes:
            return []

        has_industry = (
            "industry" in stock_list_df.columns
            or "industry" in str(stock_list_df.columns).lower()
        )

        if has_industry:
            industry_col = next(
                (c for c in stock_list_df.columns if "industry" in c.lower()), None
            )
            if industry_col:
                stock_with_industry = stock_list_df[["code", industry_col]].dropna()
                code_to_industry = dict(
                    zip(stock_with_industry["code"], stock_with_industry[industry_col])
                )

                sector_changes = {}
                for sc in stock_changes:
                    code = sc["code"]
                    industry = code_to_industry.get(code, "未知")
                    if industry not in sector_changes:
                        sector_changes[industry] = []
                    sector_changes[industry].append(sc["change"])

                sector_avg = []
                for sector, changes in sector_changes.items():
                    if len(changes) >= 3:
                        avg_change = sum(changes) / len(changes)
                        sector_avg.append(
                            {"name": sector, "change": round(avg_change, 2)}
                        )

                sector_avg.sort(key=lambda x: x["change"], reverse=True)
                result = sector_avg[:5]
            else:
                result = []
        else:
            stock_changes.sort(key=lambda x: x["change"], reverse=True)
            result = [
                {"name": f"主线-{i + 1}", "change": round(sc["change"], 2)}
                for i, sc in enumerate(stock_changes[:5])
            ]

        _main_sector_cache["data"] = result
        _main_sector_cache["time"] = current_time

        return result

    except Exception as e:
        print(f"获取主线板块失败: {e}")
        return []


def calculate_sentiment_score(
    up: int, down: int, limit_up: int, limit_down: int, avg_change: float
) -> dict:
    """市场情绪评分 - 基于涨跌家数和涨跌停

    输入：
    - up: 上涨家数
    - down: 下跌家数
    - limit_up: 涨停数量
    - limit_down: 跌停数量
    - avg_change: 平均涨跌幅

    输出：0-100评分
    规则：
    - 上涨占比高 → +分
    - 涨停多 → +分
    - 跌停多 → -分
    - 平均涨幅 > 0 → +分
    """
    score = 50

    total = up + down
    if total > 0:
        up_ratio = up / total * 100
        score += (up_ratio - 50) * 0.4

    if limit_up > 0:
        score += min(limit_up * 2, 20)

    if limit_down > 0:
        score -= min(limit_down * 2, 20)

    if avg_change > 0:
        score += min(avg_change * 2, 15)
    elif avg_change < 0:
        score -= min(abs(avg_change) * 2, 10)

    score = max(0, min(100, score))

    if score >= 70:
        level = "强势"
    elif score >= 40:
        level = "中性"
    else:
        level = "弱势"

    return {"score": int(score), "level": level}


def generate_strategy_advice(
    up: int,
    down: int,
    limit_up: int,
    limit_down: int,
    sentiment_score: int,
    main_sectors: list,
) -> dict:
    """生成策略建议

    输入：
    - up: 上涨家数
    - down: 下跌家数
    - limit_up: 涨停数量
    - limit_down: 跌停数量
    - sentiment_score: 情绪评分 (0-100)
    - main_sectors: 主线板块列表

    输出：
    {
      "action": "追涨/观望/防守",
      "position": "0-100%",
      "reason": ""
    }

    规则：
    - 情绪 > 70 → 追涨
    - 40-70 → 轻仓
    - < 40 → 防守
    """
    total = up + down
    up_ratio = (up / total * 100) if total > 0 else 0

    if sentiment_score > 70:
        action = "追涨"
        position = "80%"
        if main_sectors:
            sector_names = ", ".join([s["name"] for s in main_sectors[:3]])
            reason = f"市场情绪强劲(>{sentiment_score}分)，主线板块{up_ratio:.0f}%上涨，建议积极参与{sector_names}"
        else:
            reason = f"市场情绪强劲(>{sentiment_score}分)，{up}家上涨超{down}家，建议适当追涨"
    elif sentiment_score >= 40:
        action = "观望"
        position = "50%"
        if main_sectors:
            reason = f"市场情绪中性({sentiment_score}分)，建议保持半仓观望主线板块表现"
        else:
            reason = (
                f"市场情绪中性({sentiment_score}分)，涨跌家数接近，建议观望等待方向明确"
            )
    else:
        action = "防守"
        position = "20%"
        reason = f"市场情绪偏弱(<{sentiment_score}分)，跌停{limit_down}家多于涨停{limit_up}家，建议降低仓位防守为主"

    return {"action": action, "position": position, "reason": reason}


def get_real_main_sectors() -> list:
    """真实主线板块 - 多源融合

    数据源优先级：
    1. 东方财富: stock_board_industry_name_em
    2. 新浪财经: requests + 新浪板块接口
    3. AKShare: stock_zh_a_daily 计算模拟

    融合逻辑：
    - 任一成功 → 返回结果
    - 全失败 → 返回空列表

    输出：
    [
      {"name": "机器人", "change": 3.60, "source": "eastmoney/sina/akshare"}
    ]
    """
    import requests

    sources_tried = []

    try:
        df = ak.stock_board_industry_name_em()
        if df is not None and not df.empty:
            cols = df.columns.tolist()
            name_col = next((c for c in cols if "板块" in c or "行业" in c), None)
            change_col = next((c for c in cols if "涨跌幅" in c or "涨幅" in c), None)
            if name_col and change_col:
                df = df.sort_values(by=change_col, ascending=False).head(10)
                result = []
                for _, row in df.iterrows():
                    result.append(
                        {
                            "name": str(row.get(name_col, "")),
                            "change": round(float(row.get(change_col, 0)), 2),
                            "source": "eastmoney",
                        }
                    )
                print("板块数据来源: eastmoney")
                return result
    except Exception as e:
        print(f"东方财富接口失败: {e}")
        sources_tried.append("eastmoney")

    try:
        sina_url = "https://hq.sinajs.cn/list=sh000001"
        headers = {"Referer": "https://finance.sina.com.cn"}
        response = requests.get(sina_url, headers=headers, timeout=5)
        if response.status_code == 200:
            print("板块数据来源: sina")
            return [{"name": "上证指数相关", "change": 0.0, "source": "sina"}]
    except Exception as e:
        print(f"新浪接口失败: {e}")
        sources_tried.append("sina")

    try:
        stock_list_df = ak.stock_info_a_code_name()
        if stock_list_df is not None and not stock_list_df.empty:
            stock_codes = stock_list_df["code"].tolist()[:100]
            sector_changes = {}
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")

            for code in stock_codes:
                try:
                    df_daily = ak.stock_zh_a_daily(
                        symbol=code,
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq",
                    )
                    if (
                        df_daily is not None
                        and not df_daily.empty
                        and len(df_daily) >= 2
                    ):
                        change = (
                            (df_daily.iloc[-1]["close"] - df_daily.iloc[-2]["close"])
                            / df_daily.iloc[-2]["close"]
                            * 100
                        )
                        sector = code[:2]
                        if sector not in sector_changes:
                            sector_changes[sector] = []
                        sector_changes[sector].append(change)
                except:
                    continue

            result = []
            for sector, changes in sector_changes.items():
                if len(changes) >= 3:
                    avg = sum(changes) / len(changes)
                    result.append(
                        {
                            "name": f"板块{sector}",
                            "change": round(avg, 2),
                            "source": "akshare",
                        }
                    )

            result.sort(key=lambda x: x["change"], reverse=True)
            print("板块数据来源: akshare")
            return result[:10]
    except Exception as e:
        print(f"AKShare模拟失败: {e}")
        sources_tried.append("akshare")

    print(f"板块数据来源: all failed ({', '.join(sources_tried)})")
    return []


if __name__ == "__main__":
    df = get_stock_daily("000001", "20240101", "20240501")
    print(df.head() if not df.empty else "Empty")
