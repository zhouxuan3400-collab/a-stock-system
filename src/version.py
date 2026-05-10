# -*- coding: utf-8 -*-
import os

VERSION_FILE = "version.txt"


def get_version() -> str:
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "1.0.0"


def update_version():
    current = get_version()
    if current.startswith("v"):
        current = current[1:]
    parts = current.split(".")
    if len(parts) == 3:
        try:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            patch += 1
            new_version = f"v{major}.{minor}.{patch}"
        except:
            new_version = "v1.0.1"
    else:
        new_version = "v1.0.1"

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(new_version)

    return new_version


if __name__ == "__main__":
    print(f"当前版本: {get_version()}")
    print(f"更新后: {update_version()}")
