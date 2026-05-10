"""
🧠 registry 启动器（必须执行）
确保所有 provider 被加载
"""

import importlib
import pkgutil
import data


def auto_load_providers():
    """
    自动加载 data/ 目录下所有 provider
    触发 register()
    """

    for module in pkgutil.iter_modules(data.__path__):
        if (
            "provider" in module.name
            or "market" in module.name
            or "boards" in module.name
        ):
            importlib.import_module(f"data.{module.name}")


# 🚨 必须在 app 启动时调用
def init_registry():
    auto_load_providers()
