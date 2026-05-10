# -*- coding: utf-8 -*-
import streamlit as st
from src.version import get_version
from data.provider import (
    get_market_boards,
    get_market_snapshot,
    get_north_money,
    get_turnover_change,
)

st.set_page_config(page_title="A股系统 DEV", layout="wide")

if "market_data" not in st.session_state:
    with st.spinner("加载市场数据..."):
        st.session_state.market_data = {
            "boards": get_market_boards(),
            "snapshot": get_market_snapshot(),
            "north_money": get_north_money(),
            "turnover_change": get_turnover_change(),
        }

home_page = st.Page("pages/home.py", title="A股交易面板", icon="🏠")
main_page = st.Page("pages/main_sector.py", title="主线板块", icon="📊")
market_page = st.Page("pages/market_data.py", title="市场总览", icon="📈")
stock_page = st.Page("pages/stock_picker.py", title="选股系统", icon="🎯")

pg = st.navigation([home_page, main_page, market_page, stock_page])
pg.run()
