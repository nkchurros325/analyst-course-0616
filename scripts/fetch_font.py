"""
日本語フォント（Sawarabi Gothic, SIL OFL ライセンス）を web/fonts/jp.ttf に取得する。

ブラウザ実行版（Pyodide）で matplotlib のグラフに日本語を表示するために使います。
すでに存在する場合は再取得しません（--force で上書き）。

使い方:
    python scripts/fetch_font.py
    python scripts/fetch_font.py --force
"""

import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.normpath(os.path.join(HERE, "..", "web", "fonts", "jp.ttf"))

# Sawarabi Gothic（SIL Open Font License 1.1）。日本語の常用漢字・かなをカバー。
URL = "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/sawarabigothic/SawarabiGothic-Regular.ttf"


def main():
    force = "--force" in sys.argv
    if os.path.exists(DEST) and not force:
        print(f"既に存在します: {DEST}（再取得は --force）")
        return
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    print(f"ダウンロード中: {URL}")
    urllib.request.urlretrieve(URL, DEST)
    size = os.path.getsize(DEST)
    print(f"保存しました: {DEST} ({size:,} bytes)")
    print("ライセンス: SIL Open Font License 1.1 (Sawarabi Gothic)")


if __name__ == "__main__":
    main()
