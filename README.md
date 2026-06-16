# データアナリスト養成講座 📊

データアナリストに必要な素養を、**実際に手を動かしながら**身につけるための実践教材です。
SQL・Python（pandas）・統計・可視化を、ひとつの一貫したデータセットを題材に、初級から中級まで段階的に学びます。

---

## 🎯 この教材で身につく力

| 領域 | 学べること |
|------|-----------|
| **データ抽出** | SQL で必要なデータを正確に取り出す・集計する・結合する |
| **データ加工** | Python / pandas で前処理・クレンジング・整形を行う |
| **探索と要約** | 記述統計と探索的データ分析（EDA）でデータの素性をつかむ |
| **可視化** | 目的に合ったグラフを選び、伝わる図を作る |
| **統計的推論** | 仮説検定・信頼区間・A/Bテストで「差」を判断する |
| **モデリング入門** | 相関・回帰で関係性を読み解く |
| **問題解決** | ビジネス課題を分析タスクに翻訳し、示唆を出す |

技術スキルだけでなく、**「分析の問いの立て方」「結果の解釈」「伝え方」** という、
アナリストの“素養”にあたる部分も各章に織り込んでいます。

> 🌐 **インストールせずブラウザだけで試したい方へ**
> PC・スマホのブラウザで、Pythonを実行しながら学べる「ブラウザ実行版」があります（サーバー不要）。
> 使い方・公開方法は **[docs/web_version.md](docs/web_version.md)** を参照してください。
> （ローカルでは `python scripts/build_web.py` 後に `python scripts/serve.py` で起動）

---

## 🗂 カリキュラム

各モジュールは **解説（docs/）** と **演習ノートブック（notebooks/）** のセットです。
解説を読んでから、ノートブックで手を動かしてください。

| # | モジュール | 解説 | 演習 | 主な内容 |
|---|-----------|------|------|---------|
| 0 | 環境構築とデータ理解 | [docs/00](docs/00_introduction.md) | — | 分析の進め方、データセットの全体像 |
| 1 | アナリストの思考法 | [docs/01](docs/01_analyst_mindset.md) | — | 問いの立て方、分析プロセス、指標設計 |
| 2 | SQL 基礎 | [docs/02](docs/02_sql_basics.md) | [nb 02](notebooks/02_sql_basics.ipynb) | SELECT〜JOIN、集計、サブクエリ、ウィンドウ関数 |
| 3 | Python / pandas 基礎 | [docs/03](docs/03_pandas_basics.md) | [nb 03](notebooks/03_pandas_basics.ipynb) | 読み込み、抽出、集計、結合、整形 |
| 4 | データクレンジング | [docs/04](docs/04_data_cleaning.md) | [nb 04](notebooks/04_data_cleaning.ipynb) | 欠損・重複・異常値・表記ゆれの処理 |
| 5 | 記述統計とEDA | [docs/05](docs/05_eda.md) | [nb 05](notebooks/05_eda.ipynb) | 要約統計量、分布、外れ値、クロス集計 |
| 6 | データ可視化 | [docs/06](docs/06_visualization.md) | [nb 06](notebooks/06_visualization.ipynb) | グラフの選択、matplotlib/seaborn、伝え方 |
| 7 | 統計的推論とA/Bテスト | [docs/07](docs/07_statistics.md) | [nb 07](notebooks/07_statistics.ipynb) | 分布、信頼区間、仮説検定、A/Bテスト |
| 8 | 相関と回帰分析 | [docs/08](docs/08_regression.md) | [nb 08](notebooks/08_regression.ipynb) | 相関、単回帰・重回帰、結果の解釈 |
| 9 | 総合演習（ケーススタディ） | [docs/09](docs/09_capstone.md) | [nb 09](notebooks/09_capstone.ipynb) | 実務想定の課題を一気通貫で分析 |
| 10 | 発展演習：いろいろなパターンのデータ | [カタログ](docs/data_catalog.md) | [nb 10](notebooks/10_extra_datasets.ipynb) | 時系列・ファネル・アンケート・人事・IoT・株価を実践 |

---

## 🛒 題材データ：架空EC「Sora Mart（ソラマート）」

オンライン雑貨店の取引データを使います（すべて自動生成された架空データで、実在の人物・企業とは無関係です）。

```
data/
├── customers.csv      顧客マスタ      （2,000 行）
├── products.csv       商品マスタ      （  80 行）
├── orders.csv         注文ヘッダ      （約 5,900 行）
├── order_items.csv    注文明細        （約14,800 行）
├── customers_raw.csv  汚い顧客データ  （前処理演習用）
├── ab_test.csv        A/Bテスト結果   （統計演習用）
└── sora_mart.db       SQLite DB（上記マスタ4種を収録／SQL演習用）
```

### テーブル定義（ER図）

```
customers (顧客)                      products (商品)
├─ customer_id        PK             ├─ product_id      PK
├─ name                              ├─ product_name
├─ gender                            ├─ category
├─ age                               ├─ price   (販売価格・円)
├─ prefecture                        └─ cost    (原価・円)
├─ registration_date
└─ acquisition_channel  (獲得経路)

      │ 1                                    │ 1
      │                                      │
      │ N                                    │ N
orders (注文)                          order_items (注文明細)
├─ order_id          PK  ───────┐     ├─ order_item_id   PK
├─ customer_id       FK         └────▶├─ order_id        FK
├─ order_date                         ├─ product_id      FK ◀── products
├─ status  (completed/cancelled/returned)  ├─ quantity
└─ payment_method                     └─ unit_price
```

- **金額の出し方**：`order_items.quantity × order_items.unit_price` が明細金額。
  注文の売上は明細を合計します。**売上を語るときは原則 `status = 'completed'` だけ**を対象にします
  （cancelled / returned は売上ではない）。
- データは 2023-01-01 〜 2024-12-31 の2年分。

### 🧩 発展用データセット（いろいろなパターン）

ECデータだけだと「結合・集計」中心に偏るので、**データの“形”が異なる練習用データ**も用意しています。
時系列・広告ファネル・アンケート・人事・IoTセンサー・株価など、分野ごとに見るべき指標も手法も変わります。

```
data/
├── timeseries/web_traffic_daily.csv   日次Webアクセス  （時系列：トレンド/季節性/欠測/急増）
├── marketing/ad_campaigns.csv         広告チャネル実績  （比率・ファネル：CTR/CVR/CPA/ROAS）
├── survey/customer_survey.csv         顧客アンケート    （カテゴリ・リッカート・NPS）
├── hr/employees.csv                   従業員データ      （混合型：群比較・回帰・離職）
├── iot/sensor_readings.csv            センサーデータ    （高頻度・異常検知・欠損・外れ値）
└── finance/stock_prices.csv           株価              （複数時系列：リターン・ボラ・相関）
```

➡️ 各データの列・特徴・練習できる問いは **[docs/data_catalog.md](docs/data_catalog.md)** にまとめています。
生成は `python scripts/generate_extra_datasets.py`。

---

## 🚀 はじめかた

### 1. 必要なライブラリ

Python 3.9 以上を想定しています。以下が入っていれば動きます。

```bash
pip install pandas numpy matplotlib seaborn scipy jupyter
```

> SQL演習は Python標準の `sqlite3` を使うので追加インストール不要です。

### 2. データの生成（初回のみ）

`data/` フォルダが空の場合、または作り直したい場合：

```bash
python scripts/generate_data.py            # メインのECデータ（必須）
python scripts/generate_extra_datasets.py  # 発展用の多様なデータ（任意）
```

何度実行しても（乱数シード固定のため）同じデータが再現されます。

### 3. ノートブックの起動

```bash
jupyter notebook        # または jupyter lab
```

`notebooks/` の中の番号順のノートブックを開いて進めてください。

> **ノートブックを作り直したいとき**：`notebooks_src/*.py`（読みやすいpercent形式）が元ファイルです。
> 編集後 `python scripts/build_notebooks.py` で `.ipynb` を再生成できます。

---

## 📝 進め方のおすすめ

1. **docs の解説を読む**（概念と「なぜそうするか」を理解）
2. **notebook の例を実行する**（コードの動きを目で確認）
3. **演習問題（🖊 EXERCISE）を自力で解く** ← ここが一番大事
4. **ノートブック末尾の解答例と照合する**

各ノートブックには次の3種類のセルがあります。

- 📖 **解説セル**：概念のおさらい
- ▶️ **例（実行して確認）**：写経して動きを見る
- 🖊 **EXERCISE（あなたが書く）**：`# ここにコードを書く` を自分で埋める

> 💡 答えを写すのではなく、**まず自分で書いてエラーを出すこと**が上達の近道です。

---

## 学習の見取り図

```
   [2] SQL ──┐
             ├──▶ [4] クレンジング ──▶ [5] EDA ──▶ [6] 可視化 ──┐
   [3] pandas┘                                                  ├──▶ [9] 総合演習
                              [7] 統計的推論 ──▶ [8] 回帰 ───────┘
   ─────────────────────────────────────────────────────────────
   [1] アナリストの思考法（全章を貫く土台）
```

それでは、[docs/00_introduction.md](docs/00_introduction.md) から始めましょう！
