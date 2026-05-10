# -*- coding: utf-8 -*-
import streamlit as st
from src.version import get_version

st.set_page_config(page_title="A股系统 DEV", layout="wide")

main_page = st.Page("pages/main_sector.py", title="主线板块", icon="📊")
market_page = st.Page("pages/market_data.py", title="市场总览", icon="📈")
stock_page = st.Page("pages/stock_picker.py", title="选股系统", icon="🎯")

pg = st.navigation([main_page, market_page, stock_page])
pg.run()
