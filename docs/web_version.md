# 🌐 ブラウザ実行版（PC・スマホ対応）

この講座は、**ブラウザの中だけでPythonを実行**できます（サーバー不要・インストール不要）。
PCでもスマホでも、ページを開くだけで解説を読みながらコードを書いて動かせます。

仕組みは [Pyodide](https://pyodide.org/)（PythonをWebAssemblyに載せた技術）です。
`pandas` / `numpy` / `matplotlib` / `scipy` / `seaborn` / `sqlite3` がブラウザ内で動きます。

---

## 2つの実行版

| | 軽量HTML学習サイト（推奨） | JupyterLite版 |
|---|---|---|
| 入口 | `web/index.html` | `web/lite/`（サイト内の「JupyterLite版 →」リンク） |
| 中身 | 解説を読みながら各コードセルを「▶実行」。スマホ最適 | 本物のJupyter Notebookをそのままブラウザで |
| 向き | 初学者・スマホ・サッと写経 | 自由にセル追加・本格的に手を動かす |
| 日本語グラフ | 自動対応 | 最初の「セットアップセル」を実行すれば対応 |

> 💡 スマホで学ぶなら **軽量HTML学習サイト** がおすすめです。

---

## ローカルで試す

### 1. 元データと教材コンテンツを用意

```bash
cd data-analyst-course
pip install pandas numpy matplotlib seaborn scipy   # 生成スクリプト用

python scripts/generate_data.py            # ECデータ
python scripts/generate_extra_datasets.py  # 発展用データ
python scripts/fetch_font.py               # 日本語フォント（初回のみ）
python scripts/build_web.py                # 教材を web/ 用に変換＋データをコピー
```

### 2. ローカルサーバーで開く

```bash
python scripts/serve.py        # http://127.0.0.1:8766 で配信（キャッシュ無効）
```

ブラウザで **http://127.0.0.1:8766** を開いてください。
（`file://` で直接開くとデータ読み込みに失敗します。必ずサーバー経由で。）

> 初回はライブラリのダウンロードで30秒ほどかかります。2回目以降はブラウザキャッシュで速くなります。

### 3.（任意）JupyterLite版もローカルで作る

JupyterLiteのビルドには専用ライブラリが必要なので、仮想環境を使うのがおすすめです。

```bash
python -m venv .venv-lite
.venv-lite/Scripts/python -m pip install jupyterlite-core jupyterlite-pyodide-kernel jupyterlab-server   # Windows
# macOS/Linux は .venv-lite/bin/python ...

.venv-lite/Scripts/python scripts/build_lite.py   # web/lite/ に生成
```

その後 `python scripts/serve.py` で配信すれば、サイト右上の「JupyterLite版 →」から開けます。

---

## スマホからも使えるように公開する（GitHub Pages）

リポジトリを GitHub に置けば、付属のワークフローで自動公開できます。

1. このリポジトリを GitHub に push する。
2. GitHub の **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にする。
3. `master`（または `main`）に push するか、**Actions タブ → Deploy data-analyst-course → Run workflow** を実行。
4. 数分後、`https://<ユーザー名>.github.io/<リポジトリ名>/` で公開されます（スマホのブラウザでもOK）。

ワークフロー（[.github/workflows/deploy-da-course.yml](../../.github/workflows/deploy-da-course.yml)）が、
データ生成 → 教材変換 → JupyterLiteビルド → デプロイまで自動で行います。

### 「URLを知っている人だけ」見れるようにする（設定済み）

このサイトは **検索エンジンにインデックスさせない**設定を入れてあります。
つまり **URLを知っている人以外には見つからない**（検索に出てこない）状態です。

- 全HTMLに `<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">` を付与
  （カスタムサイトの `web/index.html` と、`build_lite.py` が JupyterLite の生成HTML全てに自動注入）
- サイトルートに `web/robots.txt`（`Disallow: /`）

> ⚠️ **重要な注意**：これは「検索に出さない」ための設定で、**アクセスを技術的に禁止するものではありません**。
> URLを知っていれば誰でも開けます（パスワードや認証はかかりません）。
> また GitHub の**プロジェクトページ（`ユーザー名.github.io/リポジトリ名/`）では `robots.txt` はドメイン直下しか参照されない**ため、
> 実効的に効くのは各ページの `noindex` メタタグです（こちらは設定済み）。
>
> **見つかりにくくするコツ**：リポジトリ名を推測されにくい文字列にする（例: `da-course-9f3a2`）。URLの一部になります。

### 本当に認証で制限したい場合（任意）

「URLを知っていても、許可した人しか開けない」ようにするには、無料の公開Pagesでは不可で、次のいずれかが必要です。

- **プライベートリポジトリ + Private Pages**：GitHub Pro / Team / Enterprise なら組織・メンバー限定の認証付きPagesにできます。
- **Cloudflare Access / Netlify のパスワード保護**を前段に置く。
- 社内サーバーや Basic認証付きの静的ホスティングに `web/` を置く。

---

## よくある質問

**Q. データはどこ？**
`web/data/` にコピーされ、ブラウザ起動時に仮想ファイルシステムへ読み込まれます。
コードからは `pd.read_csv("data/xxx.csv")` のように相対パスで読めます（教材のセットアップセルが自動で解決します）。

**Q. 自分で書いたコードは保存される？**
軽量HTML版は、レッスンを切り替えると編集内容はリセットされます（学習用のため）。
保存して続きをやりたい場合は JupyterLite版を使うか、ローカルのJupyterで `notebooks/*.ipynb` を開いてください。

**Q. 動作が重い／止まる**
ブラウザ内でPythonを動かすため、重い処理は時間がかかります。1セルずつ実行し、巨大なループは避けてください。

**Q. グラフの日本語が□になる**
軽量HTML版は自動対応です。JupyterLite版は冒頭の「セットアップセル」を実行してください。
ローカルJupyterの場合はOSの日本語フォント（Meiryo等）が使われます。
