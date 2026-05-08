# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import urllib3
from typing import List, Dict, Union
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="A股板块数据服务", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class SectorInfo(BaseModel):
    rank: int
    name: str
    change: float


@app.get("/")
def root():
    return {"message": "A股板块数据服务", "docs": "/docs"}


@app.get("/sectors", response_model=List[SectorInfo])
def get_sectors():
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
        "fields": "f12,f14,f2,f3,f62",
    }
    data = safe_request(url, params=params)
    if data is None:
        return {"status": "error", "message": "eastmoney 数据获取失败"}
    try:
        sectors = data["data"]["diff"]
        sectors_sorted = sorted(sectors, key=lambda x: x.get("f3", 0), reverse=True)
        result = []
        for i, sector in enumerate(sectors_sorted, 1):
            result.append(
                {
                    "rank": i,
                    "name": sector.get("f14", ""),
                    "change": sector.get("f3", 0),
                }
            )
        return result
    except Exception as e:
        return {"status": "error", "message": f"数据解析失败: {str(e)}"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
