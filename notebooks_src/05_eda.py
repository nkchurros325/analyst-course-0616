# %% [markdown]
# # 05. 記述統計とEDA（探索的データ分析）
#
# 🎯 **このモジュールのゴール**
#
# - データを触ったら、まず分布・代表値・ばらつき・外れ値を見て「素性」をつかむ。
# - 平均だけで語らず、中央値・標準偏差・外れ値とセットで読む。
# - 複数テーブルを merge して「分析用データセット（注文ごと・顧客ごと）」を組み立てる。
# - 各演習で「で、何が言えるか」を一言コメントする習慣をつける。
#
# **前提**：モジュール02〜04（SQL / pandas でのデータ取得・前処理）を終えていること。
#
# 解説の読み物は `docs/05_eda.md` も参照してください。

# %%
# === セットアップ（最初に必ず実行）===
import os
import numpy as np
import pandas as pd

# --- 可視化（matplotlib / seaborn）のセットアップ ---
# 注：matplotlib.use("Agg") は import pyplot より前に置く。
#     スクリプト実行時に plt.show() でブロックしないため（Jupyterではこの行は不要）。
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
for _c in ["Meiryo", "Yu Gothic", "MS Gothic", "Hiragino Sans", "IPAexGothic", "Noto Sans CJK JP"]:
    if _c in {f.name for f in font_manager.fontManager.ttflist}:
        rcParams["font.family"] = _c
        break
rcParams["axes.unicode_minus"] = False
import seaborn as sns
sns.set_theme(style="whitegrid", font=rcParams["font.family"])


def find_data_dir():
    for base in [".", "..", "../..", os.path.join("..", "data-analyst-course")]:
        cand = os.path.join(base, "data")
        if os.path.exists(os.path.join(cand, "customers.csv")):
            return cand
    raise FileNotFoundError("data フォルダが見つかりません。python scripts/generate_data.py を実行してください。")

DATA = find_data_dir()
print("データ:", os.path.abspath(DATA))

# %%
# データ読み込み（4テーブル）
customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
products = pd.read_csv(os.path.join(DATA, "products.csv"))
orders = pd.read_csv(os.path.join(DATA, "orders.csv"))
order_items = pd.read_csv(os.path.join(DATA, "order_items.csv"))

print("customers   :", customers.shape)
print("products    :", products.shape)
print("orders      :", orders.shape)
print("order_items :", order_items.shape)

# %% [markdown]
# ## 📖 5-1. 記述統計量と describe() の読み方
#
# データの素性は、いくつかの代表値（中心）とばらつき（散らばり）で要約できます。
#
# - 中心：平均(mean) / 中央値(median) / 最頻値(mode)
# - 散らばり：分散(var) / 標準偏差(std)
# - 位置：四分位数 Q1(25%) / Q2(50%=中央値) / Q3(75%) / パーセンタイル
# - 幅：範囲(range) = max - min
#
# これらを一気に出すのが `describe()` です。

# %%
# ▶️ 例：年齢(age)の記述統計を読む
print("=== describe() ===")
print(customers["age"].describe())

print("\n=== 個別に計算 ===")
print("平均     :", round(customers["age"].mean(), 2))
print("中央値   :", customers["age"].median())
print("最頻値   :", customers["age"].mode().tolist())
print("標準偏差 :", round(customers["age"].std(), 2))
print("分散     :", round(customers["age"].var(), 2))
print("Q1/Q3    :", customers["age"].quantile([0.25, 0.75]).tolist())
print("90%点    :", customers["age"].quantile(0.90))
print("範囲     :", customers["age"].max() - customers["age"].min())
# 読み：平均と中央値が近く、std は十数歳。釣鐘型に近い分布だと推測できる。

# %% [markdown]
# ## 🖊 EXERCISE 1（易）：age の代表値とばらつき
#
# `customers["age"]` について、**平均・中央値・標準偏差**を出し、
# **平均と中央値の差**から分布の歪み（左右対称か、どちらに裾が長いか）を考察してください。
#
# - ヒント：`.mean()`, `.median()`, `.std()`。
# - 期待：平均 ≒ 中央値 なら左右対称に近い。差が小さければ「ほぼ対称」と言える。
# - 最後に「で、何が言えるか」を一言。

# %%
# ここにコードを書く
# 例）mean = customers["age"].mean() ...
pass

# %% [markdown]
# ## 📖 5-2. 平均 vs 中央値（外れ値への頑健性）
#
# 平均は外れ値に弱く、中央値は強い。
# 「下限はあるが上限が青天井」のデータ（売上・購入額など）は右に歪みやすく、
# **平均 > 中央値** になりがちです。両方を出して差を見ると歪みに気づけます。

# %%
# ▶️ 例：外れ値が平均をどう動かすか（ミニ実験）
sample = pd.Series([400, 420, 450, 480, 9000])  # 最後の1つが外れ値
print("平均   :", sample.mean())     # 外れ値に引っ張られる
print("中央値 :", sample.median())   # 真ん中の人の感覚に近い
# 読み：平均2150は誰の実感とも合わない。中央値450の方が「典型」を表す。

# %% [markdown]
# ## 📖 5-3. 分析用データセットを組み立てる（merge）
#
# 生テーブルのままでは集計しづらいので、merge して「1行=1注文」「1行=1顧客」の
# 分析用テーブルを作ります。**売上は quantity × unit_price を合計し、status=='completed' のみ**。

# %%
# ▶️ 例：completed の注文だけで「注文ごとの金額」を作る
order_items = order_items.copy()
order_items["amount"] = order_items["quantity"] * order_items["unit_price"]

completed = orders[orders["status"] == "completed"]
oi = order_items.merge(completed, on="order_id")  # completed の明細だけが残る

# 1行=1注文（注文金額）
order_amount = (
    oi.groupby("order_id")
    .agg(customer_id=("customer_id", "first"), amount=("amount", "sum"))
    .reset_index()
)
print("completed の注文数 :", len(order_amount))
print(order_amount.head())

# 1行=1顧客（累計額・注文回数）
per_customer = (
    order_amount.groupby("customer_id")["amount"]
    .agg(total_amount="sum", n_orders="count")
    .reset_index()
)
print("\n購入のあった顧客数 :", len(per_customer))
print(per_customer.head())

# %% [markdown]
# ## 🖊 EXERCISE 2（易〜中）：注文ごとの金額を要約する
#
# 上で作った `order_amount["amount"]`（completed の注文ごと合計額）について、
# `describe()` を出し、さらに**ヒストグラム**を描いてください。
#
# - ヒント：`order_amount["amount"].describe()` と `.plot.hist(bins=40)`。
# - 図は `plt.savefig("...png")` で保存するか、Jupyterならそのまま表示。
# - 期待：右に裾が長い（平均 > 中央値）はず。
# - 「で、何が言えるか」を一言（典型的な注文額はいくらくらい？）。

# %%
# ここにコードを書く
# amt = order_amount["amount"]
# print(amt.describe())
# amt.plot.hist(bins=40); plt.title("注文金額の分布"); plt.savefig("ex2_hist.png")
pass

# %% [markdown]
# ## 🖊 EXERCISE 3（中）：客単価(AOV) を全体で計算
#
# **客単価 AOV = 売上合計 ÷ 注文数** を全体（completed のみ）で計算してください。
#
# - ヒント：`order_amount["amount"].sum() / len(order_amount)`。
#   これは `order_amount["amount"].mean()` と一致するはず（確認してみる）。
# - 期待：1注文あたり数千円規模。
# - 「で、何が言えるか」を一言（中央値と比べてどう？）。

# %%
# ここにコードを書く
pass

# %% [markdown]
# ## 🖊 EXERCISE 4（中）：顧客別の累計購入額と「偏り」
#
# `per_customer["total_amount"]`（顧客ごとの累計購入額, completed）を使い、
# **上位顧客に売上がどれだけ偏っているか**を確認してください。
#
# - ヒント：降順ソートして累積和 `cumsum()` を取り、全体に占める割合を見る。
#   例：上位10%/20% の顧客が売上の何%を占めるか。
# - 期待：少数の顧客が売上の大半を占める（パレートの法則っぽい偏り）。
# - 「で、何が言えるか」を一言。

# %%
# ここにコードを書く
# s = per_customer["total_amount"].sort_values(ascending=False).reset_index(drop=True)
# top10pct = int(len(s) * 0.1)
# share = s.head(top10pct).sum() / s.sum()
pass

# %% [markdown]
# ## 🖊 EXERCISE 5（中）：カテゴリ別の売上構成比
#
# 商品カテゴリ別に売上（completed）を集計し、**構成比（割合）**を出してください。
#
# - ヒント：`oi` に products を merge して category を付ける →
#   `groupby("category")["amount"].sum()` → 全体で割って構成比。
# - 期待：どのカテゴリが売上の柱か分かる。
# - 「で、何が言えるか」を一言（件数の多さと売上の大きさは一致する？）。

# %%
# ここにコードを書く
# m = oi.merge(products[["product_id", "category"]], on="product_id")
# by_cat = m.groupby("category")["amount"].sum().sort_values(ascending=False)
# share = by_cat / by_cat.sum()
pass

# %% [markdown]
# ## 🖊 EXERCISE 6（中〜難）：IQR法で「高額注文」の外れ値を検出
#
# 注文金額 `order_amount["amount"]` について **IQR法**で上側の外れ値（高額注文）を検出してください。
#
# - ヒント：Q1, Q3 = `quantile([0.25, 0.75])`、IQR = Q3 - Q1、
#   上側境界 = Q3 + 1.5 * IQR。これを超える注文を抽出。
# - 余裕があれば `boxplot` も描く。
# - 期待：全体の数%が「高額注文」候補。件数と最大額を確認。
# - 「で、何が言えるか」を一言（消すべき異常？ それとも大事な注文？）。

# %%
# ここにコードを書く
# q1, q3 = order_amount["amount"].quantile([0.25, 0.75])
# iqr = q3 - q1; upper = q3 + 1.5 * iqr
pass

# %% [markdown]
# ## 🖊 EXERCISE 7（難）：獲得経路別の客単価を比較
#
# `customers["acquisition_channel"]`（獲得経路）別に **客単価(AOV)** を比較してください。
#
# - ヒント：`order_amount` に customers の acquisition_channel を merge →
#   `groupby("acquisition_channel")["amount"].agg(["count","mean","median"])`。
# - 期待：経路によって客単価が違う（高単価を連れてくる経路はどこ？）。
# - 「で、何が言えるか」を一言（投資すべき経路の仮説）。

# %%
# ここにコードを書く
# oa = order_amount.merge(customers[["customer_id","acquisition_channel"]], on="customer_id")
# oa.groupby("acquisition_channel")["amount"].agg(["count","mean","median"])
pass

# %% [markdown]
# ## 🖊 EXERCISE 8（難・発展）：数値変数の相関を見る
#
# 顧客単位のテーブルに **年齢(age)** を足し、`age` / `n_orders` / `total_amount` の
# **相関行列**を出してください。
#
# - ヒント：`per_customer` に `customers[["customer_id","age"]]` を merge →
#   `df[["age","n_orders","total_amount"]].corr()`。
# - 注意：相関は「直線的な関係の強さ」であって因果ではない。
# - 「で、何が言えるか」を一言（年齢と購入額に関係はありそう？）。

# %%
# ここにコードを書く
pass

# %% [markdown]
# ## ✅ 解答例
#
# 以下は実データで動く解答例です。数値はデータ生成のシードに依存します。
# 各問の最後に「で、何が言えるか」のコメントを付けています。

# %%
# --- 解答1：age の代表値とばらつき ---
age = customers["age"]
mean_a, med_a, std_a = age.mean(), age.median(), age.std()
print(f"平均={mean_a:.2f} / 中央値={med_a:.1f} / 標準偏差={std_a:.2f}")
print(f"平均-中央値 = {mean_a - med_a:.2f}")
# で、何が言えるか：
# 平均と中央値がほぼ同じ（差は1歳未満）→ 年齢分布は左右対称に近い。
# std は約12歳で、平均±1std（およそ26〜50歳）に大半が収まる釣鐘型と読める。

# %%
# --- 解答2：注文ごとの金額の describe + ヒストグラム ---
amt = order_amount["amount"]
print(amt.describe())
print("歪度(skew):", round(amt.skew(), 3))

fig, ax = plt.subplots(figsize=(7, 4))
amt.plot.hist(bins=40, ax=ax)
ax.set_title("注文金額の分布（completed）")
ax.set_xlabel("注文金額（円）")
fig.tight_layout()
plt.show()  # Jupyterではこのセルの下に図が表示される
plt.close(fig)
print("注文金額のヒストグラムを描画しました。")
# で、何が言えるか：
# 平均 > 中央値 で歪度は正（右に裾が長い）。典型的な注文は中央値くらいだが、
# 一部の高額注文が平均を押し上げている。注文額は「平均だけ」で語ると過大評価になる。

# %%
# --- 解答3：客単価(AOV) ---
total_sales = order_amount["amount"].sum()
n_orders_all = len(order_amount)
aov = total_sales / n_orders_all
print(f"売上合計 = {total_sales:,.0f} 円")
print(f"注文数   = {n_orders_all:,} 件")
print(f"客単価AOV = {aov:,.1f} 円（= amount.mean(): {order_amount['amount'].mean():,.1f}）")
print(f"参考 中央値 = {order_amount['amount'].median():,.1f} 円")
# で、何が言えるか：
# AOV（平均）は中央値より高い。右歪みのため、AOVは「平均的な1注文」よりやや高めに出る。
# 施策評価では AOV と中央値の両方を見るのが安全。

# %%
# --- 解答4：顧客別累計額の偏り ---
s = per_customer["total_amount"].sort_values(ascending=False).reset_index(drop=True)
for pct in [0.1, 0.2]:
    k = max(1, int(len(s) * pct))
    share = s.head(k).sum() / s.sum()
    print(f"上位 {int(pct*100)}% の顧客（{k}人）が売上の {share*100:.1f}% を占める")
# で、何が言えるか：
# 上位2割の顧客が売上の大半を占める偏り（パレート的）。
# 全顧客を一律に扱うより、上位顧客の維持・育成が売上インパクト大、という仮説が立つ。

# %%
# --- 解答5：カテゴリ別の売上構成比 ---
m = oi.merge(products[["product_id", "category"]], on="product_id")
by_cat = m.groupby("category")["amount"].sum().sort_values(ascending=False)
share = (by_cat / by_cat.sum() * 100).round(1)
cnt = m.groupby("category")["amount"].count().reindex(by_cat.index)
summary = pd.DataFrame({"売上": by_cat.astype(int), "構成比%": share, "明細件数": cnt})
print(summary)
# で、何が言えるか：
# 売上構成比のトップ数カテゴリで全体の多くを占める。
# 「明細件数が多い＝売上が大きい」とは限らず、単価の高いカテゴリが効いている場合がある。

# %%
# --- 解答6：IQR法で高額注文を検出 + 箱ひげ図 ---
q1, q3 = order_amount["amount"].quantile([0.25, 0.75])
iqr = q3 - q1
upper = q3 + 1.5 * iqr
lower = q1 - 1.5 * iqr
high = order_amount[order_amount["amount"] > upper]
print(f"Q1={q1:,.0f} / Q3={q3:,.0f} / IQR={iqr:,.0f}")
print(f"上側境界={upper:,.0f} 円")
print(f"高額注文（外れ値候補）: {len(high)} 件 "
      f"（全体の {len(high)/len(order_amount)*100:.1f}%）, 最大 {high['amount'].max():,.0f} 円")

fig, ax = plt.subplots(figsize=(7, 3))
ax.boxplot(order_amount["amount"], vert=False, whis=1.5)
ax.set_title("注文金額の箱ひげ図（IQR法, completed）")
ax.set_xlabel("注文金額（円）")
fig.tight_layout()
plt.show()  # Jupyterではこのセルの下に図が表示される
plt.close(fig)
print("注文金額の箱ひげ図を描画しました。")
# で、何が言えるか：
# 高額注文は全体の数%。これは入力ミスではなく「まとめ買い」など本物の注文と考えられる。
# 機械的に削除せず、誰がどんな注文をしたかを別途確認する価値がある（大事な顧客の可能性）。

# %%
# --- 解答7：獲得経路別の客単価(AOV) ---
oa = order_amount.merge(
    customers[["customer_id", "acquisition_channel"]], on="customer_id"
)
by_ch = (
    oa.groupby("acquisition_channel")["amount"]
    .agg(注文数="count", 平均="mean", 中央値="median")
    .sort_values("平均", ascending=False)
)
by_ch["平均"] = by_ch["平均"].round(0)
by_ch["中央値"] = by_ch["中央値"].round(0)
print(by_ch)
# で、何が言えるか：
# 経路ごとに客単価に差が出る。客単価の高い経路は「単価の高い顧客を連れてくる」可能性。
# ただし注文数（母数）も併せて見る必要あり。差が偶然かどうかの検定はモジュール07で扱う。

# %%
# --- 解答8：数値変数の相関行列 ---
cust_feat = per_customer.merge(
    customers[["customer_id", "age"]], on="customer_id"
)
corr = cust_feat[["age", "n_orders", "total_amount"]].corr()
print(corr.round(3))
# で、何が言えるか：
# n_orders と total_amount は強い正の相関（たくさん買う人ほど累計額が大きい＝当然）。
# age と購入額の相関は弱い。年齢で購入額を説明するのは難しそう、という見立て。
# 注意：相関は直線関係の強さで、因果ではない。

# %%
# --- スモークチェック（通し実行が成功したことの確認）---
print("\n[OK] 05_eda.py：全セルの実行が完了しました。")
