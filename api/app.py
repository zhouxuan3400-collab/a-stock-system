# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
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

    response = requests.get(url, params=params)
    data = response.json()
    sectors = data["data"]["diff"]

    sectors_sorted = sorted(sectors, key=lambda x: x.get("f3", 0), reverse=True)

    result = []
    for i, sector in enumerate(sectors_sorted, 1):
        result.append(
            {"rank": i, "name": sector.get("f14", ""), "change": sector.get("f3", 0)}
        )

    return result


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
