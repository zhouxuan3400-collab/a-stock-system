# -*- coding: utf-8 -*-
import os
import json

LATEST_RESULT_FILE = "data/latest_result.json"
HISTORY_FILE = "data/history.json"


def get_latest_result():
    if os.path.exists(LATEST_RESULT_FILE):
        with open(LATEST_RESULT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_latest_result(data):
    os.makedirs("data", exist_ok=True)
    with open(LATEST_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def get_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def append_history(record):
    history = get_history()
    history.append(record)
    history = history[-30:]
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False)
