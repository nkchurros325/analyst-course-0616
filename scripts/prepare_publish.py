"""
GitHub Pages公開用の「専用リポジトリ一式」を別フォルダに組み立てる。

data-analyst-course/ の必要ファイルだけを、コース内容がルートになる形でコピーし、
ルート直下に GitHub Actions のデプロイワークフローを置く。
（生成物・重いものは除外。CIで生成し直す。）

使い方:
    python scripts/prepare_publish.py                 # 既定: ../../da-course-site へ
    python scripts/prepare_publish.py <出力先パス>

出力後の流れ:
    1. GitHubで空のリポジトリを作る（READMEなし）
    2. cd <出力先>
       git init && git add -A && git commit -m "Initial: data analyst course (web)"
       git branch -M main
       git remote add origin https://github.com/<ユーザー>/<リポジトリ>.git
       git push -u origin main
    3. GitHub の Settings → Pages → Source を「GitHub Actions」にする
       （数分後 https://<ユーザー>.github.io/<リポジトリ>/ で公開）
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, ".."))  # data-analyst-course/
DEFAULT_OUT = os.path.normpath(os.path.join(SRC, "..", "..", "da-course-site"))

# コピーするトップレベル項目（生成物・重いものは除外）
INCLUDE_DIRS = ["docs", "scripts", "notebooks", "notebooks_src"]
INCLUDE_FILES = ["README.md", ".gitignore"]

# web/ は中身を選別してコピー（生成物は除外）
WEB_EXCLUDE = {"data", "lite", "lite_contents", "lessons.json", "data_manifest.json"}

DEPLOY_WORKFLOW = """name: Deploy (GitHub Pages)

# データアナリスト養成講座のブラウザ実行版を GitHub Pages に公開する。
# URLを知っている人だけ向け（noindex設定済み・検索除外）。

on:
  push:
    branches: [main, master]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pandas numpy matplotlib seaborn scipy
          pip install jupyterlite-core jupyterlite-pyodide-kernel jupyterlab-server
      - name: Generate datasets
        run: |
          python scripts/generate_data.py
          python scripts/generate_extra_datasets.py
      - name: Fetch Japanese font
        run: python scripts/fetch_font.py
      - name: Build web content
        run: python scripts/build_web.py
      - name: Build JupyterLite
        run: python scripts/build_lite.py
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: web

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
"""


def copy_web(dst_web):
    os.makedirs(dst_web, exist_ok=True)
    src_web = os.path.join(SRC, "web")
    for name in os.listdir(src_web):
        if name in WEB_EXCLUDE:
            continue
        s = os.path.join(src_web, name)
        d = os.path.join(dst_web, name)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)


def main():
    out = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)

    for d in INCLUDE_DIRS:
        shutil.copytree(os.path.join(SRC, d), os.path.join(out, d))
    for f in INCLUDE_FILES:
        src_f = os.path.join(SRC, f)
        if os.path.exists(src_f):
            shutil.copy2(src_f, os.path.join(out, f))

    copy_web(os.path.join(out, "web"))

    wf_dir = os.path.join(out, ".github", "workflows")
    os.makedirs(wf_dir, exist_ok=True)
    with open(os.path.join(wf_dir, "deploy.yml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(DEPLOY_WORKFLOW)

    print("公開用リポジトリ一式を組み立てました:")
    print(" ", out)
    print("\n次の手順:")
    print("  1) GitHubで空リポジトリを作成（READMEなし）")
    print(f"  2) cd {out}")
    print("     git init && git add -A && git commit -m \"Initial: data analyst course (web)\"")
    print("     git branch -M main")
    print("     git remote add origin https://github.com/<ユーザー>/<リポジトリ>.git")
    print("     git push -u origin main")
    print("  3) Settings → Pages → Source を「GitHub Actions」に設定")


if __name__ == "__main__":
    main()
