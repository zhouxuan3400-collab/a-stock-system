# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
from typing import List, Dict
from pydantic import BaseModel

app = FastAPI(title="A股板块数据服务", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def safe_request(url, params=None, max_retries=3):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json,text/plain,*/*",
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"请求失败，第 {attempt + 1} 次重试: {e}")

            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print("所有重试失败")
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
    try:
        data = safe_request(url, params=params)
        if not data:
            return [{"rank": 0, "name": "数据获取失败", "change": 0.0}]
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
        return [{"rank": 0, "name": f"数据获取失败: {str(e)}", "change": 0.0}]


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
