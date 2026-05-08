# -*- coding: utf-8 -*-
import os
import sys
import io
import csv
import re
from datetime import datetime
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("reports", exist_ok=True)

os.system("python src/sector.py > NUL 2>&1")

today = datetime.now().strftime("%Y-%m-%d")
report_file = f"reports/{today}.md"

if os.path.exists("data/processed/report.txt"):
    with open("data/processed/report.txt", "r", encoding="utf-8") as f:
        content = f.read()
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(content)

    lines = content.split("\n")
    main_sector = ""
    market_status = ""
    risk_level = ""
    strategy = ""
    position = ""
    system_score = ""

    for line in lines:
        if "市场状态:" in line:
            market_status = line.split("市场状态:")[1].strip().split("(")[0].strip()
        elif "风险等级:" in line:
            risk_level = line.split("风险等级:")[1].strip()
        elif "当前策略:" in line:
            strategy = line.split("当前策略:")[1].strip()
        elif "建议仓位:" in line:
            position = line.split("建议仓位:")[1].strip()
        elif "系统评分:" in line:
            system_score = line.split("系统评分:")[1].strip().split("/")[0]

    sectors = []
    for line in lines:
        if "板块名称 + 分数:" in line:
            continue
        match = re.match(r"\s+(\S+.*):\s+\d+分", line)
        if match:
            sectors.append(match.group(1))
    main_sector = ",".join(sectors[:3]) if sectors else ""

    history_file = "data/processed/market_history.csv"
    file_exists = os.path.exists(history_file)

    with open(history_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "date",
                    "main_sector",
                    "market_status",
                    "risk_level",
                    "strategy",
                    "position",
                    "system_score",
                ]
            )
        writer.writerow(
            [
                today,
                main_sector,
                market_status,
                risk_level,
                strategy,
                position,
                system_score,
            ]
        )

print("今日市场分析完成")
print(f"报告已保存至: {report_file}")
