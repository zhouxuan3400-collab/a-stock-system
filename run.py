# -*- coding: utf-8 -*-
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

result = os.system("python src/sector.py > NUL 2>&1")

if os.path.exists("data/processed/report.txt"):
    with open("data/processed/report.txt", "r", encoding="utf-8") as f:
        for line in f:
            print(line.rstrip())
