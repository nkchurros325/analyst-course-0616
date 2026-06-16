"""
JupyterLite版（ブラウザでそのままノートブックを実行）をビルドする。

- notebooks/*.ipynb と data/ を JupyterLite のコンテンツとして取り込む
- 各ノートブックの先頭に「JupyterLite用セットアップ」セルを注入
  （日本語フォント登録 + seaborn の取得）。元の notebooks/ は変更しない。
- `jupyter lite build` で web/lite/ に静的サイトを生成

前提: venv (.venv-lite) に jupyterlite-core / jupyterlite-pyodide-kernel が入っていること。
    python -m venv .venv-lite
    .venv-lite/Scripts/python -m pip install jupyterlite-core jupyterlite-pyodide-kernel

使い方（venvのpythonで実行）:
    .venv-lite/Scripts/python scripts/build_lite.py
"""

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
NB_DIR = os.path.join(ROOT, "notebooks")
DATA_DIR = os.path.join(ROOT, "data")
FONT = os.path.join(ROOT, "web", "fonts", "jp.ttf")
CONTENTS = os.path.join(ROOT, "web", "lite_contents")
OUTPUT = os.path.join(ROOT, "web", "lite")

# 各ノートブック先頭に挿入するセットアップセル
SETUP_CODE = '''# === JupyterLite用セットアップ（最初に必ず実行してください）===
# ブラウザ内Python(Pyodide)で動かすための準備：日本語フォントと追加ライブラリ
import os
try:
    import piplite
    await piplite.install(["seaborn"])  # noqa: F704 (JupyterLiteはtop-level awaitに対応)
except Exception as _e:
    print("seabornの取得をスキップ:", _e)

import matplotlib.font_manager as _fm
from matplotlib import rcParams as _rc
if os.path.exists("fonts/jp.ttf"):
    _fm.fontManager.addfont("fonts/jp.ttf")
    _JP = _fm.FontProperties(fname="fonts/jp.ttf").get_name()
    # 既存ノートブックのフォント探索でヒットするようエイリアス登録
    for _a in ["Meiryo", "Yu Gothic", "IPAexGothic", "Noto Sans CJK JP", "MS Gothic"]:
        try:
            _fm.fontManager.ttflist.append(_fm.FontEntry(fname="fonts/jp.ttf", name=_a))
        except Exception:
            pass
    _rc["font.family"] = _JP
    _rc["axes.unicode_minus"] = False
    print("日本語フォント準備OK:", _JP)
else:
    print("注意: fonts/jp.ttf が見つかりません（グラフの日本語が□になる可能性）")
'''

SETUP_MD = (
    "## ⚙️ JupyterLite版について\n\n"
    "これはブラウザの中だけでPythonを動かす環境です。**下のセットアップセルを最初に実行**してください"
    "（日本語フォントと追加ライブラリを準備します）。あとは通常のノートブックと同じです。\n\n"
    "> データは `data/` フォルダにあります（このノートと同じ場所）。"
)


def make_cell_code(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": src.splitlines(keepends=True)}


def make_cell_md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}


def prepare_contents():
    if os.path.exists(CONTENTS):
        shutil.rmtree(CONTENTS)
    os.makedirs(CONTENTS)

    # データとフォントをコンテンツ直下に
    shutil.copytree(DATA_DIR, os.path.join(CONTENTS, "data"))
    os.makedirs(os.path.join(CONTENTS, "fonts"), exist_ok=True)
    shutil.copy(FONT, os.path.join(CONTENTS, "fonts", "jp.ttf"))

    # ノートブックを取り込み、セットアップセルを先頭に注入
    count = 0
    for fn in sorted(os.listdir(NB_DIR)):
        if not fn.endswith(".ipynb"):
            continue
        with open(os.path.join(NB_DIR, fn), encoding="utf-8") as f:
            nb = json.load(f)
        nb["cells"] = [make_cell_md(SETUP_MD), make_cell_code(SETUP_CODE)] + nb["cells"]
        with open(os.path.join(CONTENTS, fn), "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False)
        count += 1
    print(f"コンテンツ準備完了: ノートブック{count}冊 + data/ + fonts/")


NOINDEX_META = (
    '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">'
    '<meta name="googlebot" content="noindex, nofollow">'
)


def inject_noindex():
    """生成された全HTMLに noindex メタタグを入れる（URLを知る人だけ向けの限定公開）。"""
    n = 0
    for dirpath, _dirs, files in os.walk(OUTPUT):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                html = f.read()
            if "noindex" in html:
                continue
            low = html.lower()
            idx = low.find("<head>")
            if idx != -1:
                insert_at = idx + len("<head>")
            else:
                idx = low.find("<head")
                if idx == -1:
                    continue
                insert_at = low.find(">", idx) + 1
            html = html[:insert_at] + NOINDEX_META + html[insert_at:]
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            n += 1
    print(f"noindex メタタグを {n} 個のHTMLに注入しました。")


def build():
    if os.path.exists(OUTPUT):
        shutil.rmtree(OUTPUT)
    cmd = [
        sys.executable, "-m", "jupyter", "lite", "build",
        "--contents", CONTENTS,
        "--output-dir", OUTPUT,
    ]
    print("実行:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)
    inject_noindex()
    print(f"\nJupyterLite を {OUTPUT} に生成しました。")


def main():
    prepare_contents()
    build()


if __name__ == "__main__":
    main()
