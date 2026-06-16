"""
percent形式の .py ファイルを Jupyter Notebook (.ipynb) に変換するビルダー。

依存ライブラリ不要（標準ライブラリのみ）。nbformat が無い環境でも動きます。

percent形式のルール:
    # %% [markdown]   ... これ以降をマークダウンセルとして扱う（各行頭の "# " を除去）
    # %%              ... これ以降をコードセルとして扱う
    ファイル冒頭のセルマーカー前のテキストは無視されます。

使い方:
    python scripts/build_notebooks.py            # notebooks_src/*.py をすべて変換
    python scripts/build_notebooks.py foo.py     # 指定ファイルのみ変換
"""

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.normpath(os.path.join(HERE, "..", "notebooks_src"))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "notebooks"))


def parse_cells(text):
    """percent形式テキストをセルのリストに分解する。"""
    lines = text.splitlines()
    cells = []
    cur_type = None
    cur_lines = []

    def flush():
        if cur_type is None:
            return
        # 末尾の空行を削る
        content = cur_lines[:]
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
            cells.append(("markdown", stripped))
        else:
            cells.append(("code", content))

    for ln in lines:
        s = ln.strip()
        if s.startswith("# %% [markdown]") or s == "# %%[markdown]":
            flush()
            cur_type = "markdown"
            cur_lines = []
        elif s == "# %%" or s.startswith("# %% "):
            flush()
            cur_type = "code"
            cur_lines = []
        else:
            if cur_type is not None:
                cur_lines.append(ln)
    flush()
    return cells


def to_notebook(cells):
    nb_cells = []
    for ctype, content in cells:
        # 各行に改行を付与（最終行以外）
        src = []
        for i, ln in enumerate(content):
            if i < len(content) - 1:
                src.append(ln + "\n")
            else:
                src.append(ln)
        if ctype == "markdown":
            nb_cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": src,
            })
        else:
            nb_cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": src,
            })
    return {
        "cells": nb_cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def convert(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    cells = parse_cells(text)
    nb = to_notebook(cells)
    os.makedirs(OUT_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(OUT_DIR, base + ".ipynb")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f"  {os.path.basename(path)} -> notebooks/{base}.ipynb  ({len(cells)} cells)")


def main():
    args = sys.argv[1:]
    if args:
        targets = []
        for a in args:
            if os.path.isabs(a):
                targets.append(a)
            else:
                targets.append(os.path.join(SRC_DIR, a))
    else:
        targets = sorted(glob.glob(os.path.join(SRC_DIR, "*.py")))
    print(f"{len(targets)} 個のファイルを変換します ...")
    for t in targets:
        convert(t)
    print("完了。")


if __name__ == "__main__":
    main()
