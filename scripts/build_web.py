"""
軽量HTML学習サイト（Pyodide版）のコンテンツをビルドする。

- notebooks_src/*.py（percent形式）と docs/00,01 を解析して web/lessons.json を生成
- data/ 以下を web/data/ にコピーし、web/data_manifest.json を生成
- これらを web/index.html（別途用意）が読み込んでブラウザ内で実行する

依存ライブラリ不要（標準ライブラリのみ）。

使い方:
    python scripts/build_web.py
"""

import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
SRC_DIR = os.path.join(ROOT, "notebooks_src")
DOCS_DIR = os.path.join(ROOT, "docs")
DATA_DIR = os.path.join(ROOT, "data")
WEB_DIR = os.path.join(ROOT, "web")
WEB_DATA_DIR = os.path.join(WEB_DIR, "data")

# レッスンのタイトル（表示順）
LESSON_TITLES = {
    "00_introduction": "00. 環境構築とデータ理解",
    "01_analyst_mindset": "01. アナリストの思考法",
    "02_sql_basics": "02. SQL 基礎",
    "03_pandas_basics": "03. Python / pandas 基礎",
    "04_data_cleaning": "04. データクレンジング",
    "05_eda": "05. 記述統計とEDA",
    "06_visualization": "06. データ可視化",
    "07_statistics": "07. 統計的推論とA/Bテスト",
    "08_regression": "08. 相関と回帰分析",
    "09_capstone": "09. 総合演習",
    "10_extra_datasets": "10. 発展演習：いろいろなパターン",
}

# コード実行を伴う（=Pyodideで動かす）レッスン
NOTEBOOK_LESSONS = [
    "02_sql_basics", "03_pandas_basics", "04_data_cleaning", "05_eda",
    "06_visualization", "07_statistics", "08_regression", "09_capstone",
    "10_extra_datasets",
]
# 読み物のみ（docs の md をそのまま表示）
READING_LESSONS = ["00_introduction", "01_analyst_mindset"]


def parse_percent(text):
    """percent形式テキストを [{type, source}] のセル列に分解。"""
    lines = text.splitlines()
    cells = []
    cur_type = None
    cur = []

    def flush():
        if cur_type is None:
            return
        content = cur[:]
        while content and content[-1].strip() == "":
            content.pop()
        if cur_type == "markdown":
            stripped = []
            for ln in content:
                if ln.startswith("# "):
                    stripped.append(ln[2:])
                elif ln == "#":
                    stripped.append("")
                else:
                    stripped.append(ln)
            cells.append({"type": "markdown", "source": "\n".join(stripped)})
        else:
            cells.append({"type": "code", "source": "\n".join(content)})

    for ln in lines:
        s = ln.strip()
        if s.startswith("# %% [markdown]") or s == "# %%[markdown]":
            flush(); cur_type = "markdown"; cur = []
        elif s == "# %%" or s.startswith("# %% "):
            flush(); cur_type = "code"; cur = []
        else:
            if cur_type is not None:
                cur.append(ln)
    flush()
    return cells


def build_lessons():
    lessons = []

    # 読み物（docs md → 1つのmarkdownセル）
    for key in READING_LESSONS:
        path = os.path.join(DOCS_DIR, key + ".md")
        with open(path, encoding="utf-8") as f:
            md = f.read()
        lessons.append({
            "id": key,
            "title": LESSON_TITLES[key],
            "reading": True,
            "cells": [{"type": "markdown", "source": md}],
        })

    # ノートブック（percent .py → セル列）
    for key in NOTEBOOK_LESSONS:
        path = os.path.join(SRC_DIR, key + ".py")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        cells = parse_percent(text)
        lessons.append({
            "id": key,
            "title": LESSON_TITLES[key],
            "reading": False,
            "cells": cells,
        })

    # 表示順に並べる
    order = {k: i for i, k in enumerate(LESSON_TITLES)}
    lessons.sort(key=lambda L: order.get(L["id"], 999))
    return lessons


def copy_data():
    if os.path.exists(WEB_DATA_DIR):
        shutil.rmtree(WEB_DATA_DIR)
    shutil.copytree(DATA_DIR, WEB_DATA_DIR)

    manifest = []
    for dirpath, _dirs, files in os.walk(WEB_DATA_DIR):
        for fn in files:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, WEB_DATA_DIR).replace("\\", "/")
            binary = fn.endswith(".db")
            manifest.append({"path": rel, "binary": binary})
    manifest.sort(key=lambda m: m["path"])
    return manifest


def main():
    os.makedirs(WEB_DIR, exist_ok=True)

    lessons = build_lessons()
    with open(os.path.join(WEB_DIR, "lessons.json"), "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False)

    manifest = copy_data()
    with open(os.path.join(WEB_DIR, "data_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    n_code = sum(1 for L in lessons for c in L["cells"] if c["type"] == "code")
    print("web/lessons.json を生成:")
    for L in lessons:
        kind = "読み物" if L["reading"] else "演習"
        ncode = sum(1 for c in L["cells"] if c["type"] == "code")
        print(f"  [{kind}] {L['title']:<34s} cells={len(L['cells']):3d} (code={ncode})")
    print(f"\n合計コードセル: {n_code}")
    print(f"data_manifest.json: {len(manifest)} ファイルを web/data/ にコピー")
    print("完了。")


if __name__ == "__main__":
    main()
