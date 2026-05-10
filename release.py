# -*- coding: utf-8 -*-
import os
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")

from src.version import get_version


def run_release():
    version = get_version()
    print(f"开始发布版本: {version}")

    try:
        subprocess.run(
            [
                "git",
                "add",
                "app.py",
                "auto_run.py",
                "src/",
                "services/",
                "version.txt",
                "release.py",
                ".gitignore",
            ],
            check=True,
        )
        print("git add 完成")

        commit_msg = f"release: {version}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"git commit 完成: {commit_msg}")

        subprocess.run(["git", "tag", version], check=True)
        print(f"git tag 创建: {version}")

        subprocess.run(["git", "push", "origin", "dev"], check=True)
        print("git push origin dev 完成")

        subprocess.run(["git", "push", "origin", "--tags"], check=True)
        print("git push --tags 完成")

        print(f"\n发布成功! 版本: {version}")

    except subprocess.CalledProcessError as e:
        print(f"发布失败: {e}")
    except Exception as e:
        print(f"未知错误: {e}")


if __name__ == "__main__":
    run_release()
