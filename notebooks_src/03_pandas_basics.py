# %% [markdown]
# # 03. Python / pandas 基礎
#
# 🎯 **このモジュールのゴール**：pandas でデータを「読む・選ぶ・絞る・並べる・集計する・結合する・整える」一連の操作ができるようになる。
#
# **前提**：02. SQL 基礎を終えていること。SQL で解いた問い（月次売上・カテゴリ別売上・顧客別購入額）を、ここでは pandas で解き直します。
#
# 解説の読み物は `docs/03_pandas_basics.md` にあります。あわせて読むと理解が深まります。

# %%
# === セットアップ（最初に必ず実行）===
import os
import numpy as np
import pandas as pd

def find_data_dir():
    for base in [".", "..", "../..", os.path.join("..", "data-analyst-course")]:
        cand = os.path.join(base, "data")
        if os.path.exists(os.path.join(cand, "customers.csv")):
            return cand
    raise FileNotFoundError("data フォルダが見つかりません。python scripts/generate_data.py を実行してください。")

DATA = find_data_dir()
print("データ:", os.path.abspath(DATA))

# 4つのテーブルを読み込む（以降ずっと使う）
customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
products = pd.read_csv(os.path.join(DATA, "products.csv"))
orders = pd.read_csv(os.path.join(DATA, "orders.csv"))
order_items = pd.read_csv(os.path.join(DATA, "order_items.csv"))
print("読み込み完了:",
      "customers", customers.shape,
      "products", products.shape,
      "orders", orders.shape,
      "order_items", order_items.shape)

# %% [markdown]
# ## 📖 3-1. DataFrame と Series ── 2つの基本の型
#
# - **DataFrame**＝表全体（2次元）。 **Series**＝表の1列分（1次元、ラベル付き）。
# - 「1列だけ選ぶと Series、2列以上だと DataFrame」と覚える。
# - DataFrame には行ラベル（index）と列ラベル（columns）がある。

# %%
# ▶️ 例：DataFrame と Series の違いを確かめる
print("型(products):", type(products))      # DataFrame
print("型(1列だけ):", type(products["price"]))  # Series
print()
print("列名:", list(products.columns))
print("先頭のindex:", products.index[:5].tolist())

# %% [markdown]
# ## 📖 3-2. まず全体を把握する（読み込み〜要約）
#
# データを受け取ったら、いきなり集計せず **まず全体像を掴む**。
#
# - `head` / `tail`：先頭・末尾を見て中身のイメージを掴む
# - `shape`：(行数, 列数)
# - `info`：列名・型・非欠損数（欠損の発見に必須）
# - `describe`：数値列の要約統計（min/max がおかしくないか）
# - `dtypes`：型（日付が文字列のままになっていないか）

# %%
# ▶️ 例：customers の健康診断
print("--- shape ---")
print(customers.shape)
print("\n--- head(3) ---")
print(customers.head(3))
print("\n--- dtypes ---")
print(customers.dtypes)
print("\n--- describe（数値列）---")
print(customers.describe())
print("\n--- info ---")
customers.info()

# %% [markdown]
# ## 🖊 EXERCISE 1（易）：顧客データの基本把握と性別構成
#
# 1. `customers` の行数・列数を表示する。
# 2. 性別（`gender`）の **構成比** を表示する（割合で）。
#
# ヒント：行数列数は `.shape`。構成比は `value_counts(normalize=True)`。
# （期待される答え：女性・男性・回答なし の3カテゴリの割合が出る）

# %%
# ここにコードを書く
# 1. 行数・列数
# 2. 性別の構成比

# %% [markdown]
# ## 📖 3-3. 列と行の選択（loc / iloc）
#
# - 列：`df["age"]`（1列=Series）、`df[["name","age"]]`（複数列=DataFrame）
# - 行：`loc` は **ラベル** で、`iloc` は **位置（整数）** で指定。
# - 実務で一番使う形：`df.loc[条件, ["列A","列B"]]`（条件で行、ラベルで列）。

# %%
# ▶️ 例：loc と iloc
print("--- 1列（Series）---")
print(customers["age"].head(3))
print("\n--- 複数列（DataFrame）---")
print(customers[["name", "age"]].head(3))
print("\n--- iloc：先頭3行・先頭3列（位置指定）---")
print(customers.iloc[:3, :3])
print("\n--- loc：条件で行、ラベルで列 ---")
print(customers.loc[customers["age"] >= 70, ["name", "age", "prefecture"]].head(3))

# %% [markdown]
# ## 📖 3-4. 条件で絞り込む（ブールインデックス）
#
# - `df[条件]` の「条件」は各行 True/False の Series。
# - **複数条件は `&`（かつ） `|`（または）。各条件は `( )` で囲む**（`and/or` はエラーになる）。
# - `isin([...])`＝SQLのIN、`between(a, b)`＝両端含む範囲、`query("...")`＝文字列で書ける。

# %%
# ▶️ 例：いろいろな絞り込み
tokyo_30 = customers[(customers["age"] >= 30) & (customers["prefecture"] == "東京都")]
print("30歳以上・東京都:", tokyo_30.shape[0], "人")

big_city = customers[customers["prefecture"].isin(["東京都", "大阪府", "愛知県"])]
print("3大都市圏:", big_city.shape[0], "人")

thirties = customers[customers["age"].between(30, 39)]
print("30代:", thirties.shape[0], "人")

# query は同じことを文字列で書ける
print("query版:", customers.query("age >= 30 and prefecture == '東京都'").shape[0], "人")

# %% [markdown]
# ## 🖊 EXERCISE 2（易）：30歳以上・東京都の顧客抽出
#
# `customers` から **30歳以上かつ東京都** の顧客を抽出し、
# `name`, `age`, `acquisition_channel` の3列だけを先頭5行表示する。
#
# ヒント：`df[(条件1) & (条件2)]` で行を絞り、`[["列",...]]` で列を選ぶ。`query` でもOK。
# （期待される答え：条件に合う顧客の一覧。人数も確認するとよい）

# %%
# ここにコードを書く

# %% [markdown]
# ## 📖 3-5. 並べ替えと上位N件
#
# - `sort_values("列", ascending=False)`：降順で並べ替え。
# - 複数キー：`sort_values(["a","b"], ascending=[True, False])`。
# - `nlargest(N, "列")`：上位N件の近道（= sort_values + head）。

# %%
# ▶️ 例：価格の高い商品トップ5
top5 = products.nlargest(5, "price")[["product_name", "category", "price"]]
print(top5)
print("\n--- sort_values + head でも同じ ---")
print(products.sort_values("price", ascending=False).head(5)[["product_name", "price"]])

# %% [markdown]
# ## 🖊 EXERCISE 3（易〜中）：価格の高い商品 TOP10
#
# `products` を価格（`price`）の高い順に並べ、上位10商品の
# `product_name`, `category`, `price` を表示する。
#
# ヒント：`nlargest(10, "price")` または `sort_values(..., ascending=False).head(10)`。
# （期待される答え：高価格な商品が10行。カテゴリの偏りも眺めてみよう）

# %%
# ここにコードを書く

# %% [markdown]
# ## 📖 3-6. 新しい列を作る
#
# - 直接代入：`df["利益"] = df["price"] - df["cost"]`（列同士の **ベクトル演算** は速い）。
# - `assign(...)`：元を壊さず新DataFrameを返す（メソッドチェーンで便利）。
# - `apply(関数)`：1値ずつ関数適用。柔軟だが遅いので「ベクトル演算で書けないとき」だけ。

# %%
# ▶️ 例：利益と粗利率の列を作る
prod2 = products.assign(
    profit=products["price"] - products["cost"],
    margin=(products["price"] - products["cost"]) / products["price"],
)
print(prod2[["product_name", "price", "cost", "profit", "margin"]].head(3))

# apply の軽い紹介：価格帯ラベルを付ける
prod2["price_band"] = prod2["price"].apply(
    lambda p: "高" if p >= 5000 else ("中" if p >= 2000 else "低")
)
print("\n価格帯の内訳:")
print(prod2["price_band"].value_counts())

# %% [markdown]
# ## 🖊 EXERCISE 4（中）：カテゴリ別の平均価格と商品数
#
# `products` をカテゴリ（`category`）でグループ化し、
# **平均価格** と **商品数** を1つの表にまとめる。平均価格の高い順に並べる。
#
# ヒント：`groupby("category").agg(avg_price=("price","mean"), n=("product_id","count"))`、
# そのあと `.sort_values("avg_price", ascending=False)`。
# （期待される答え：6カテゴリ × [avg_price, n] の表）

# %%
# ここにコードを書く

# %% [markdown]
# ## 📖 3-7. value_counts と groupby + agg
#
# - `value_counts()`：カテゴリ列の件数を多い順に。`normalize=True` で構成比。
# - `groupby("キー").agg(新列名=("対象列","集計方法"))`：グループごとに集計（SQLのGROUP BY）。
# - 集計方法は `sum / mean / count / min / max / median / nunique` など。
# - 複数キー：`groupby(["k1","k2"])`。結果を表に戻すには `.reset_index()`。

# %%
# ▶️ 例：value_counts と groupby
print("--- 獲得経路の件数 ---")
print(customers["acquisition_channel"].value_counts())

print("\n--- 都道府県別の平均年齢 上位5 ---")
g = customers.groupby("prefecture").agg(
    avg_age=("age", "mean"),
    n=("customer_id", "count"),
).sort_values("avg_age", ascending=False)
print(g.head(5))

# %% [markdown]
# ## 📖 3-8. merge ── テーブルの結合と「売上」の作り方
#
# 複数の表をキーでつなぐのが `merge`（SQLのJOIN）。`how` で結合方法を選ぶ
# （inner=共通部分のみ / left=左を全部残す / right / outer=全部）。
#
# **【このコースの厳守ルール】売上 = `quantity × unit_price` を合計。
# `status == 'completed'` の注文のみ**（cancelled / returned は売上に含めない）。
#
# まず `order_items` に `orders` を結合し、completed に絞り、金額列 `amount` を作ります。
# この `sales` を以降の集計の出発点にします。

# %%
# ▶️ 例：売上テーブル sales を作る（このあと何度も使う）
sales = order_items.merge(
    orders[["order_id", "customer_id", "order_date", "status"]],
    on="order_id",
    how="inner",   # 注文に紐付く明細だけを残す
)
print("merge直後:", sales.shape)

sales = sales[sales["status"] == "completed"].copy()  # completed のみ
sales["amount"] = sales["quantity"] * sales["unit_price"]
print("completed のみ:", sales.shape)
print("総売上:", int(sales["amount"].sum()), "円")

# how の違いを体感：left だと明細(order_items)が全部残る
left_join = order_items.merge(orders[["order_id", "status"]], on="order_id", how="left")
print("\n明細件数:", len(order_items), "/ left結合後:", len(left_join), "（件数が保たれる）")

# %% [markdown]
# ## 🖊 EXERCISE 5（中）：カテゴリ別の売上
#
# 売上テーブル `sales` に `products` を結合し、**カテゴリ別の売上合計** を
# 高い順に表示する。
#
# ヒント：`sales.merge(products[["product_id","category"]], on="product_id")` で
# カテゴリを付け、`groupby("category")["amount"].sum().sort_values(ascending=False)`。
# （期待される答え：6カテゴリの売上ランキング。02 SQL の結果と一致するはず）

# %%
# ここにコードを書く

# %% [markdown]
# ## 📖 3-9. 日付を扱う（to_datetime と .dt）
#
# CSV から読むと日付は文字列（object）。`pd.to_datetime` で日付型に変換すると
# `.dt.year` `.dt.month` `.dt.to_period("M")` などで年・月を取り出せる。
# 月次集計は `to_period("M")` をキーにすると楽。

# %%
# ▶️ 例：月次売上
sales["order_date"] = pd.to_datetime(sales["order_date"])
sales["ym"] = sales["order_date"].dt.to_period("M")
monthly = sales.groupby("ym")["amount"].sum()
print("月次売上（先頭6か月）:")
print(monthly.head(6))
print("\n集計対象の月数:", monthly.shape[0])

# %% [markdown]
# ## 🖊 EXERCISE 6（中〜難）：月次売上の集計
#
# `sales` から **年・月ごとの売上合計** を求め、時系列順に表示する。
# さらに「最も売上が大きかった月」を1つ取り出す。
#
# ヒント：`order_date` を `to_datetime` →（既に上の例で変換済みでもOK）→
# `groupby(sales["order_date"].dt.to_period("M"))["amount"].sum()`。
# 最大月は `.idxmax()` / `.max()`。
# （期待される答え：月次の売上推移と、ピーク月）

# %%
# ここにコードを書く

# %% [markdown]
# ## 📖 3-10. pivot_table ── クロス集計
#
# 行と列の2軸で集計するのが `pivot_table`（Excelのピボット）。
# `index`＝行の軸、`columns`＝列の軸、`values`＝集計値、`aggfunc`＝集計方法。
# `fill_value=0` で空セルを0に、`margins=True` で総計を追加。

# %%
# ▶️ 例：獲得経路 × 性別 の人数クロス集計
pt = customers.pivot_table(
    index="acquisition_channel",
    columns="gender",
    values="customer_id",
    aggfunc="count",
    fill_value=0,
)
print(pt)

# %% [markdown]
# ## 🖊 EXERCISE 7（難）：獲得経路 × 性別 のクロス集計
#
# 上の例を参考に、**獲得経路（行）× 性別（列）の人数** をクロス集計し、
# さらに各セルを「その獲得経路内での構成比（%）」に変換して表示する。
#
# ヒント：人数の pivot_table を作り、各行を行合計で割る
# （`pt.div(pt.sum(axis=1), axis=0)`）。`* 100` で%に。
# （期待される答え：経路ごとに男女比がどう違うか）

# %%
# ここにコードを書く

# %% [markdown]
# ## 🖊 EXERCISE 8（難）：顧客別の累計購入額 TOP10
#
# `sales` を使い、**顧客ごとの累計購入額** を求めて上位10人を表示する。
# さらに `customers` を結合して、その顧客の `prefecture` と `age` も並べる。
#
# ヒント：`sales.groupby("customer_id")["amount"].sum()` →
# `.nlargest(10)` または `sort_values(ascending=False).head(10)`、
# その結果（`reset_index()`）に `customers` を merge。
# （期待される答え：優良顧客トップ10の購入額・地域・年齢）

# %%
# ここにコードを書く

# %% [markdown]
# ## ✅ 解答例
#
# 以下は各演習の解答例です。実データで動作します。まず自分で書いてから答え合わせを。

# %%
# --- 解答1：基本把握と性別構成 ---
print("行数・列数:", customers.shape)
print("\n性別の構成比:")
print(customers["gender"].value_counts(normalize=True).round(3))

# %%
# --- 解答2：30歳以上・東京都の顧客 ---
ans2 = customers[(customers["age"] >= 30) & (customers["prefecture"] == "東京都")]
print("該当人数:", len(ans2))
print(ans2[["name", "age", "acquisition_channel"]].head(5))

# %%
# --- 解答3：価格の高い商品 TOP10 ---
ans3 = products.nlargest(10, "price")[["product_name", "category", "price"]]
print(ans3.to_string(index=False))

# %%
# --- 解答4：カテゴリ別の平均価格と商品数 ---
ans4 = (
    products.groupby("category")
    .agg(avg_price=("price", "mean"), n_products=("product_id", "count"))
    .sort_values("avg_price", ascending=False)
    .round(0)
)
print(ans4)

# %%
# --- 解答5：カテゴリ別の売上 ---
ans5 = (
    sales.merge(products[["product_id", "category"]], on="product_id")
    .groupby("category")["amount"].sum()
    .sort_values(ascending=False)
)
print(ans5.apply(lambda x: f"{int(x):,} 円"))

# %%
# --- 解答6：月次売上の集計 ---
ans6 = (
    sales.groupby(sales["order_date"].dt.to_period("M"))["amount"]
    .sum()
    .sort_index()
)
print("月次売上:")
print(ans6)
print("\nピーク月:", ans6.idxmax(), "/", f"{int(ans6.max()):,} 円")

# %%
# --- 解答7：獲得経路 × 性別 の構成比 ---
pt7 = customers.pivot_table(
    index="acquisition_channel", columns="gender",
    values="customer_id", aggfunc="count", fill_value=0,
)
ratio7 = (pt7.div(pt7.sum(axis=1), axis=0) * 100).round(1)
print("各獲得経路内の性別構成比（%）:")
print(ratio7)

# %%
# --- 解答8：顧客別の累計購入額 TOP10 ---
by_cust = (
    sales.groupby("customer_id")["amount"].sum()
    .nlargest(10)
    .reset_index(name="total_amount")
)
ans8 = by_cust.merge(
    customers[["customer_id", "name", "prefecture", "age"]],
    on="customer_id",
)
ans8["total_amount"] = ans8["total_amount"].apply(lambda x: f"{int(x):,} 円")
print(ans8[["customer_id", "name", "prefecture", "age", "total_amount"]].to_string(index=False))

# %% [markdown]
# ## 🎉 おつかれさまでした
#
# pandas でデータを読み・選び・絞り・並べ・集計し・結合し・整える流れを一通り体験しました。
# SQL（モジュール02）と同じ問いを pandas でも解けたはずです。**道具に依らず問いに答える**感覚を大切に。
#
# 👉 次は **04. データクレンジング**。欠損・重複・表記ゆれだらけの現実のデータを、分析できる状態に整えます。
