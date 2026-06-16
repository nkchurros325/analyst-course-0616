# %% [markdown]
# # 06. データ可視化 ── 伝わるグラフの作り方と選び方
#
# > 🎯 **このモジュールのゴール**
# > - matplotlib / seaborn でグラフを描く基本を身につける
# > - 「目的」に合ったグラフの種類を選べるようになる
# > - 数字を見せるだけでなく、**1グラフ1メッセージで「伝わる」**図にできる
#
# **前提**：モジュール02〜05（SQL・pandas・前処理・集計）まで。
# pandas の `merge` / `groupby` は使える前提で進めます。
#
# このモジュールでも分析規約は厳守です：
# **売上 = `quantity × unit_price` の合計、ただし注文 `status == 'completed'` のみ。**

# %%
# === セットアップ（最初に必ず実行）===
# 可視化モジュールなので matplotlib / seaborn を設定します。
import os
import numpy as np
import pandas as pd

# --- matplotlib を「画面に出さない」Agg バックエンドにする ---
# スクリプト(.py)として実行すると plt.show() が画面待ちでブロックしないように。
# ★ Jupyter で動かすときは、この use("Agg") の行は不要（むしろ書かない方が図が表示される）。
import matplotlib
matplotlib.use("Agg")  # ← Jupyterではこの1行は削除/コメントアウトしてOK
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams

# 日本語フォントを探して設定（無いと日本語が豆腐□になる）
for _c in ["Meiryo", "Yu Gothic", "MS Gothic", "Hiragino Sans", "IPAexGothic", "Noto Sans CJK JP"]:
    if _c in {f.name for f in font_manager.fontManager.ttflist}:
        rcParams["font.family"] = _c
        break
rcParams["axes.unicode_minus"] = False  # マイナス記号が□にならないように

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
print("使用フォント:", rcParams["font.family"])

# %%
# === データを読み込んで merge し、分析用テーブルを作る ===
customers = pd.read_csv(os.path.join(DATA, "customers.csv"), parse_dates=["registration_date"])
products = pd.read_csv(os.path.join(DATA, "products.csv"))
orders = pd.read_csv(os.path.join(DATA, "orders.csv"), parse_dates=["order_date"])
order_items = pd.read_csv(os.path.join(DATA, "order_items.csv"))

# 売上行 = 明細 × 単価。まずは明細ごとの金額を作る。
order_items = order_items.assign(amount=order_items["quantity"] * order_items["unit_price"])

# 明細 → 注文 → 顧客 / 商品 をすべて結合した「ワイドな1枚」を作る。
sales = (
    order_items
    .merge(orders, on="order_id", how="left")
    .merge(customers, on="customer_id", how="left")
    .merge(products, on="product_id", how="left")
)

# ★ 売上は completed のみ。これ以降「売上」と言ったらこの sales_done を使う。
sales_done = sales[sales["status"] == "completed"].copy()

print("全明細:", len(sales), "行 / うち completed:", len(sales_done), "行")
print("売上合計:", f"{sales_done['amount'].sum():,.0f} 円")
sales_done[["order_date", "category", "amount", "age", "acquisition_channel"]].head()

# %% [markdown]
# ## 6-1. matplotlib の基本 ── figure と axes
#
# matplotlib の図は **2階建て**です。
#
# - **Figure（figure）**：キャンバス全体（1枚の紙）。
# - **Axes（axes / ax）**：その上に置く「1つのグラフ領域」。軸・目盛・線はここに描く。
#
# `fig, ax = plt.subplots()` で「紙1枚 + グラフ1つ」を作り、`ax.plot(...)` のように
# **ax に対して**描いていくのがおすすめです（どこに何を描くか明確になる）。
#
# グラフには最低限これを付けます。付いていないグラフは「伝わらない」と思ってください。
#
# | 要素 | メソッド | なぜ必要か |
# |------|----------|-----------|
# | タイトル | `ax.set_title()` | 何のグラフか一言で |
# | 軸ラベル | `ax.set_xlabel()` / `ax.set_ylabel()` | **単位**まで書く（円・人・%） |
# | 凡例 | `ax.legend()` | 複数系列があるとき、どれが何か |
#
# > 💡 `plt.show()` は「描いたものを表示」する命令。今回は `Agg` なので画面には出ませんが、
# > **Jupyter で開くとセル直下に図が表示されます**。スクリプト実行では出ないだけでエラーにはなりません。

# %%
# ▶️ 例：一番シンプルな折れ線。x と y を渡すだけ。
x = np.arange(1, 13)                      # 1〜12月
y = np.array([12, 15, 14, 18, 20, 19, 25, 30, 28, 26, 22, 24])  # ダミーの売上(万円)

fig, ax = plt.subplots(figsize=(8, 4))    # 紙1枚 + グラフ1つ
ax.plot(x, y, marker="o", label="2024年")  # ax に折れ線を描く
ax.set_title("月別の売上（ダミーデータ）")    # タイトル
ax.set_xlabel("月")                        # x軸ラベル
ax.set_ylabel("売上（万円）")               # y軸ラベル（単位つき！）
ax.legend()                               # 凡例
plt.show()   # Jupyterならここで図が表示される（Aggでは表示されないだけ）

print("figとaxができた:", type(fig).__name__, "/", type(ax).__name__)
plt.close("all")  # 図を閉じてメモリを解放（たくさん描くときの作法）

# %% [markdown]
# ## 6-2. seaborn で簡潔に描く
#
# **seaborn** は matplotlib の上に乗ったライブラリで、
# 「DataFrame と列名」を渡すだけで集計＋見栄えの良いグラフを描いてくれます。
#
# - `sns.barplot(data=df, x="...", y="...")` … 棒グラフ（自動で平均＋誤差棒）
# - `sns.histplot(...)` … ヒストグラム、`sns.boxplot(...)` … 箱ひげ図
# - `sns.scatterplot(...)` … 散布図、`sns.heatmap(...)` … ヒートマップ
#
# matplotlib より短く書けるのが利点。細かい調整（タイトル等）は返ってきた `ax` に対して行います。
#
# > 💡 使い分け：**素早く探索するなら seaborn、1px単位で作り込むなら matplotlib**。
# > 本講座では「seabornで描いて、matplotlibで仕上げる」を基本にします。

# %%
# ▶️ 例：seaborn でカテゴリ別の売上合計を棒グラフに。
cat_sales = (
    sales_done.groupby("category", as_index=False)["amount"].sum()
    .sort_values("amount", ascending=False)   # ★ 棒グラフは必ず大きい順に並べる（後述6-4）
)
print(cat_sales)

fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(data=cat_sales, x="category", y="amount", ax=ax, color="#4C72B0")
ax.set_title("カテゴリ別の売上（completedのみ）")
ax.set_xlabel("カテゴリ")
ax.set_ylabel("売上（円）")
plt.show()
plt.close("all")

# %% [markdown]
# ## 6-3. グラフの選び方 ── 目的で決める早見表
#
# 「何を伝えたいか（目的）」が決まれば、グラフはほぼ自動的に決まります。
#
# | 伝えたいこと（目的） | 向いているグラフ | このモジュールの例 |
# |--------------------|-----------------|-------------------|
# | 時間に沿った**推移** | 折れ線 | 月次売上 |
# | カテゴリ間の**比較** | 棒（横棒も可） | カテゴリ別売上 |
# | 1変数の**分布** | ヒストグラム / 箱ひげ図 | 年齢、注文金額 |
# | 2変数の**関係** | 散布図 | 年齢 vs 累計購入額 |
# | **構成比**（内訳） | 棒（積み上げ） | 経路×カテゴリ |
# | 多変数の**相関の俯瞰** | ヒートマップ | 数値項目の相関 |
#
# 迷ったら「**推移=線 / 比較=棒 / 分布=ヒスト・箱 / 関係=散布図**」とだけ覚えればOK。

# %%
# ▶️ 例：時系列の推移 → 折れ線（月次売上）
# order_date を「月」に丸めて集計する。Series.dt.to_period("M") が便利。
monthly = (
    sales_done
    .assign(month=sales_done["order_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)["amount"].sum()
)
print(monthly.head())

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(monthly["month"], monthly["amount"], marker="o")
ax.set_title("月次売上の推移（2023-2024, completedのみ）")
ax.set_xlabel("年月")
ax.set_ylabel("売上（円）")
plt.show()
plt.close("all")

# %% [markdown]
# 上の折れ線で「夏〜年末にかけて高い」「年初に落ちる」などの**季節性**が読めれば成功です。
# 推移は線でつなぐことで「上がっている / 下がっている」が一目で分かります。

# %%
# ▶️ 例：分布 → ヒストグラムと箱ひげ図
# 年齢の分布（ヒストグラム）。何歳の顧客が多いのか？
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

sns.histplot(data=customers, x="age", bins=20, ax=axes[0], color="#55A868")
axes[0].set_title("顧客の年齢分布（ヒストグラム）")
axes[0].set_xlabel("年齢")
axes[0].set_ylabel("人数")

# 注文金額の分布（箱ひげ図）。中央値・四分位・外れ値が分かる。
# 注文単位の金額にするため order_id ごとに合計してから箱ひげにする。
order_amount = sales_done.groupby("order_id", as_index=False)["amount"].sum()
sns.boxplot(data=order_amount, y="amount", ax=axes[1], color="#C44E52")
axes[1].set_title("注文1件あたり金額の分布（箱ひげ）")
axes[1].set_ylabel("注文金額（円）")

plt.show()
print("注文金額の中央値:", f"{order_amount['amount'].median():,.0f} 円")
plt.close("all")

# %% [markdown]
# **ヒストグラム**は「どの値にどれだけ集まっているか（山の形）」、
# **箱ひげ図**は「中央値・ばらつき・外れ値」を見るのに向きます。
# 箱の中の線が中央値、箱の上下が四分位、ひげの外の点が外れ値です。

# %%
# ▶️ 例：2変数の関係 → 散布図（年齢 vs 顧客別の累計購入額）
# 顧客ごとに「売上の累計」を出し、年齢と並べる。
cust_total = (
    sales_done.groupby("customer_id", as_index=False)["amount"].sum()
    .merge(customers[["customer_id", "age"]], on="customer_id", how="left")
)
print(cust_total.head())

fig, ax = plt.subplots(figsize=(8, 5))
sns.scatterplot(data=cust_total, x="age", y="amount", ax=ax, alpha=0.4)
ax.set_title("年齢 と 累計購入額 の関係")
ax.set_xlabel("年齢")
ax.set_ylabel("累計購入額（円）")
plt.show()

# 相関係数も数値で確認（散布図とセットで見ると説得力が増す）
r = cust_total["age"].corr(cust_total["amount"])
print("年齢と累計購入額の相関係数 r =", round(r, 3))
plt.close("all")

# %% [markdown]
# ## 6-4. 「伝わる」グラフの原則
#
# 同じデータでも、見せ方で伝わり方は大きく変わります。実務で効く原則：
#
# 1. **1グラフ1メッセージ**：そのグラフで言いたいことを1つに絞る。欲張らない。
# 2. **軸ラベルと単位**：「売上」ではなく「売上（円）」。読み手は単位を推測したくない。
# 3. **棒グラフはソートする**：カテゴリ比較は**大きい順**に並べると順位が一瞬で分かる。
#    （月・曜日など「順序に意味がある」軸はソートしない。）
# 4. **装飾を減らす**：3D・影・過剰な色は情報を埋もれさせる。インクは情報のために使う。
# 5. **誤解を生む表現を避ける**：棒グラフの**y軸は0から**始める。途中で切ると差が誇張される。
#
# ### ❌ 悪い例 / ⭕ 良い例（y軸の切り詰め）
# 下のセルで、同じ数字でも y軸の起点を変えると印象が激変することを体感します。

# %%
# ▶️ 例：y軸の切り詰めが「差」を誇張する（左:悪い / 右:良い）
labels = ["A店", "B店", "C店"]
values = [102, 100, 104]   # 実際にはほぼ横並び（102, 100, 104）

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# ❌ 悪い例：y軸を 99 から始めると、わずかな差が「大差」に見える
axes[0].bar(labels, values, color="#C44E52")
axes[0].set_ylim(99, 105)
axes[0].set_title("❌ 悪い例：y軸を99から（差が誇張される）")
axes[0].set_ylabel("売上（万円）")

# ⭕ 良い例：y軸を0から。ほぼ横並びだと正しく伝わる
axes[1].bar(labels, values, color="#4C72B0")
axes[1].set_ylim(0, 120)
axes[1].set_title("⭕ 良い例：y軸を0から（差は小さいと正しく伝わる）")
axes[1].set_ylabel("売上（万円）")

plt.show()
print("3店舗はほぼ同じ（100〜104）。左の図は差を誤認させる。")
plt.close("all")

# %% [markdown]
# ### 円グラフの注意点
# 構成比＝円グラフ、と反射的に選びがちですが、円グラフは
# **「角度の比較が人間には苦手」「項目が多いと読めない」「並べ替えで順位が分かりにくい」**
# という弱点があります。多くの場合、**降順の棒グラフ**や**積み上げ棒**の方が正確に伝わります。
# 円グラフを使うなら「項目2〜3個」「合計が100%だと強調したい」ときに限定しましょう。

# %% [markdown]
# ## 6-5. 構成比 ── 積み上げ棒グラフ
#
# 「全体に占める内訳」を、複数グループで**比べたい**ときは積み上げ棒が便利です。
# 例：獲得経路ごとに、売上がどのカテゴリで構成されているか。

# %%
# ▶️ 例：獲得経路 × カテゴリ の売上（積み上げ棒）
# pivot_table で「行=経路, 列=カテゴリ, 値=売上」の表にしてから .plot(kind="bar", stacked=True)
pivot = sales_done.pivot_table(
    index="acquisition_channel", columns="category", values="amount", aggfunc="sum", fill_value=0
)
# 行（経路）を売上合計の大きい順に並べる
pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
print(pivot.round(0))

fig, ax = plt.subplots(figsize=(10, 5))
pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
ax.set_title("獲得経路別 売上のカテゴリ構成（積み上げ）")
ax.set_xlabel("獲得経路")
ax.set_ylabel("売上（円）")
ax.legend(title="カテゴリ", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.xticks(rotation=20)
plt.tight_layout()
plt.show()
plt.close("all")

# %% [markdown]
# ## 6-6. 相関の俯瞰 ── ヒートマップ
#
# 数値項目どうしの相関を**一覧**したいときはヒートマップ。
# `df.corr()` で相関行列を作り、`sns.heatmap(..., annot=True)` で数値も重ねます。

# %%
# ▶️ 例：顧客単位の数値項目で相関ヒートマップ
# 顧客ごとに「年齢・累計購入額・注文回数・平均単価」を作って相関を見る。
cust_feat = sales_done.groupby("customer_id").agg(
    purchase_total=("amount", "sum"),
    n_orders=("order_id", "nunique"),
).reset_index()
cust_feat["avg_order"] = cust_feat["purchase_total"] / cust_feat["n_orders"]
cust_feat = cust_feat.merge(customers[["customer_id", "age"]], on="customer_id", how="left")

corr = cust_feat[["age", "purchase_total", "n_orders", "avg_order"]].corr()
print(corr.round(2))

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-1, vmax=1, ax=ax)
ax.set_title("顧客指標の相関ヒートマップ")
plt.tight_layout()
plt.show()
plt.close("all")

# %% [markdown]
# 色（赤=正の相関 / 青=負の相関）と数値で、どの項目どうしが連動するかが一目で分かります。
# 「累計購入額」と「注文回数」が強く相関する、などが読めれば成功です。

# %% [markdown]
# ## 6-7. 複数グラフを並べる ── subplots でミニダッシュボード
#
# `plt.subplots(行数, 列数)` で複数の axes を一度に作り、`axes[行, 列]` に描き分けます。
# 1枚に関連する図をまとめると「全体像」を伝えるダッシュボードになります。

# %%
# ▶️ 例：2x2 のミニダッシュボード（推移・比較・分布・関係）
fig, axes = plt.subplots(2, 2, figsize=(13, 9))

# 左上：月次売上の推移（折れ線）
axes[0, 0].plot(monthly["month"], monthly["amount"], marker="o", color="#4C72B0")
axes[0, 0].set_title("月次売上の推移")
axes[0, 0].set_xlabel("年月"); axes[0, 0].set_ylabel("売上（円）")

# 右上：カテゴリ別売上（棒・降順）
sns.barplot(data=cat_sales, x="category", y="amount", ax=axes[0, 1], color="#55A868")
axes[0, 1].set_title("カテゴリ別売上"); axes[0, 1].set_xlabel("カテゴリ"); axes[0, 1].set_ylabel("売上（円）")
axes[0, 1].tick_params(axis="x", rotation=20)

# 左下：年齢分布（ヒストグラム）
sns.histplot(data=customers, x="age", bins=20, ax=axes[1, 0], color="#C44E52")
axes[1, 0].set_title("顧客の年齢分布"); axes[1, 0].set_xlabel("年齢"); axes[1, 0].set_ylabel("人数")

# 右下：年齢 vs 累計購入額（散布図）
sns.scatterplot(data=cust_total, x="age", y="amount", ax=axes[1, 1], alpha=0.3)
axes[1, 1].set_title("年齢 vs 累計購入額"); axes[1, 1].set_xlabel("年齢"); axes[1, 1].set_ylabel("累計購入額（円）")

fig.suptitle("Sora Mart ミニダッシュボード", fontsize=14)
plt.tight_layout()
plt.show()
plt.close("all")

# %% [markdown]
# ## 6-8. ビジネスでの見せ方 ── 色と注釈で「主役」を立てる
#
# 全部を同じ色で描くと「どこを見ればいいか」が伝わりません。
# **強調したい1本だけ色を変え、残りはグレー**にすると、視線が一瞬でそこへ向かいます。
# さらに `ax.annotate()` で「ピーク」「ここが言いたい」という注釈を直接置きましょう。

# %%
# ▶️ 例：最大売上のカテゴリだけ色を変え、注釈を付ける
cat = cat_sales.reset_index(drop=True)
colors = ["#B0B0B0"] * len(cat)         # まず全部グレー
colors[0] = "#C44E52"                    # 1位（降順なので先頭）だけ赤で強調

fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(cat["category"], cat["amount"], color=colors)
ax.set_title("売上トップのカテゴリを強調する")
ax.set_xlabel("カテゴリ"); ax.set_ylabel("売上（円）")

top_name = cat.loc[0, "category"]
top_val = cat.loc[0, "amount"]
ax.annotate(
    f"最大: {top_name}\n{top_val:,.0f}円",
    xy=(0, top_val), xytext=(0.8, top_val * 0.92),
    arrowprops=dict(arrowstyle="->", color="black"),
)
plt.show()
print("主役:", top_name)
plt.close("all")

# %% [markdown]
# ## 🖊 EXERCISE（演習）
#
# ここから演習です。各セルの **`# ここにコードを書く`** を埋めてください。
# **どの問題でも、最後にコメントで「このグラフで何を伝えたいか」を一文で書くこと。**
# （例：`# 伝えたいこと：売上は夏に伸び、年初に落ちる季節性がある`）
#
# 末尾に `## ✅ 解答例` があります。詰まったら見てOK。

# %% [markdown]
# ### 問1（易）月次売上の折れ線グラフ
# `sales_done` から月次売上を集計し、折れ線で描いてください。
# タイトル・軸ラベル（単位つき）を必ず付け、読み取れる季節性をコメントに書くこと。
# ヒント：`order_date.dt.to_period("M")` で月に丸める。`ax.plot(...)`。

# %%
# 問1：月次売上の折れ線
# ヒント：monthly = ... groupby("month")["amount"].sum()
# ここにコードを書く

# 伝えたいこと：（一文で書く）
pass

# %% [markdown]
# ### 問2（易）カテゴリ別売上の棒グラフ（降順ソート）
# カテゴリ別の売上合計を**大きい順**に並べた棒グラフにしてください。
# ヒント：`groupby("category")["amount"].sum().sort_values(ascending=False)`。

# %%
# 問2：カテゴリ別売上（降順）
# ここにコードを書く

# 伝えたいこと：（一文で書く）
pass

# %% [markdown]
# ### 問3（易）年齢のヒストグラム
# `customers` の年齢分布をヒストグラムで描いてください（bins は20程度）。
# ヒント：`sns.histplot(data=customers, x="age", bins=20)`。

# %%
# 問3：年齢のヒストグラム
# ここにコードを書く

# 伝えたいこと：（一文で書く）
pass

# %% [markdown]
# ### 問4（中）獲得経路別の客単価（棒グラフ）
# 獲得経路ごとの**客単価（=売上 / 注文数）**を計算し、降順の棒グラフにしてください。
# ヒント：注文数は `nunique("order_id")`。経路ごとに 売上合計 ÷ 注文数。

# %%
# 問4：獲得経路別の客単価
# ここにコードを書く

# 伝えたいこと：（一文で書く）
pass

# %% [markdown]
# ### 問5（中）注文金額の箱ひげ図（カテゴリ別）
# 注文×カテゴリ単位の金額の分布を、カテゴリ別の箱ひげ図で比べてください。
# ヒント：`groupby(["order_id","category"])["amount"].sum()` → `sns.boxplot(x="category", y="amount")`。
# 外れ値が多いと見にくいので `ax.set_ylim(0, 上限)` で切ってもよい（切ったとコメントに明記）。

# %%
# 問5：注文金額の箱ひげ図（カテゴリ別）
# ここにコードを書く

# 伝えたいこと：（一文で書く）
pass

# %% [markdown]
# ### 問6（中）年齢 vs 顧客別累計購入額 の散布図
# 顧客ごとの累計購入額を出し、年齢との散布図を描いてください。相関係数も print すること。
# ヒント：`groupby("customer_id")["amount"].sum()` を `customers` の age と merge。

# %%
# 問6：年齢 vs 累計購入額 の散布図
# ここにコードを書く

# 伝えたいこと：（一文で書く）
pass

# %% [markdown]
# ### 問7（難）数値項目の相関ヒートマップ
# 顧客単位で「年齢・累計購入額・注文回数・平均単価」を作り、相関ヒートマップを描いてください。
# ヒント：`df.corr()` → `sns.heatmap(corr, annot=True, cmap="coolwarm", center=0)`。

# %%
# 問7：相関ヒートマップ
# ここにコードを書く

# 伝えたいこと：（一文で書く）
pass

# %% [markdown]
# ### 問8（難）subplots で「ミニダッシュボード」
# これまでに作った図から **2つ以上**を `plt.subplots` で1枚に並べてください。
# 全体タイトル（`fig.suptitle`）を付け、`tight_layout()` で重なりを防ぐこと。
# ヒント：`fig, axes = plt.subplots(1, 2, figsize=(13,4))` → `axes[0]` / `axes[1]` に描く。

# %%
# 問8：ミニダッシュボード
# ここにコードを書く

# 伝えたいこと：（一文で書く・ダッシュボード全体で何を見せたいか）
pass

# %% [markdown]
# ## ✅ 解答例
#
# 以下は実データで動く解答例です。数値や色は一例なので、あなたの図と多少違っても構いません。
# 大切なのは **目的に合ったグラフ種** と **タイトル・軸ラベル・単位・ソート** が揃っていることです。

# %%
# --- 解答1：月次売上の折れ線 ---
ans_monthly = (
    sales_done
    .assign(month=sales_done["order_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)["amount"].sum()
)
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(ans_monthly["month"], ans_monthly["amount"], marker="o")
ax.set_title("月次売上の推移（completedのみ）")
ax.set_xlabel("年月"); ax.set_ylabel("売上（円）")
plt.show()
print("月次の最大:", ans_monthly.loc[ans_monthly["amount"].idxmax(), "month"].strftime("%Y-%m"))
# 伝えたいこと：売上は夏〜年末に高まり年初に落ちる、という季節性がある。
plt.close("all")

# %%
# --- 解答2：カテゴリ別売上（降順） ---
ans_cat = (
    sales_done.groupby("category", as_index=False)["amount"].sum()
    .sort_values("amount", ascending=False)
)
fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(data=ans_cat, x="category", y="amount", ax=ax, color="#4C72B0")
ax.set_title("カテゴリ別売上（降順）")
ax.set_xlabel("カテゴリ"); ax.set_ylabel("売上（円）")
ax.tick_params(axis="x", rotation=20)
plt.tight_layout(); plt.show()
print(ans_cat.to_string(index=False))
# 伝えたいこと：売上に最も貢献しているカテゴリはどれかを順位で示す。
plt.close("all")

# %%
# --- 解答3：年齢のヒストグラム ---
fig, ax = plt.subplots(figsize=(8, 4))
sns.histplot(data=customers, x="age", bins=20, ax=ax, color="#55A868")
ax.set_title("顧客の年齢分布")
ax.set_xlabel("年齢"); ax.set_ylabel("人数")
plt.show()
print("年齢の中央値:", customers["age"].median())
# 伝えたいこと：顧客の年齢がどの層に集中しているかを示す。
plt.close("all")

# %%
# --- 解答4：獲得経路別の客単価 ---
ans_aov = (
    sales_done.groupby("acquisition_channel")
    .agg(sales=("amount", "sum"), n_orders=("order_id", "nunique"))
    .assign(aov=lambda d: d["sales"] / d["n_orders"])
    .sort_values("aov", ascending=False)
    .reset_index()
)
fig, ax = plt.subplots(figsize=(9, 4))
sns.barplot(data=ans_aov, x="acquisition_channel", y="aov", ax=ax, color="#8172B3")
ax.set_title("獲得経路別の客単価（売上 / 注文数）")
ax.set_xlabel("獲得経路"); ax.set_ylabel("客単価（円/注文）")
ax.tick_params(axis="x", rotation=20)
plt.tight_layout(); plt.show()
print(ans_aov[["acquisition_channel", "aov"]].round(0).to_string(index=False))
# 伝えたいこと：どの獲得経路の顧客が1注文あたり高く買うかを比較する。
plt.close("all")

# %%
# --- 解答5：注文金額の箱ひげ図（カテゴリ別） ---
order_cat = (
    sales_done.groupby(["order_id", "category"], as_index=False)["amount"].sum()
)
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=order_cat, x="category", y="amount", ax=ax)
ax.set_title("カテゴリ別の注文金額分布（箱ひげ）")
ax.set_xlabel("カテゴリ"); ax.set_ylabel("注文金額（円）")
ax.set_ylim(0, order_cat["amount"].quantile(0.99))  # 上位1%の外れ値を切って見やすく
ax.tick_params(axis="x", rotation=20)
plt.tight_layout(); plt.show()
# 伝えたいこと：注文金額の中央値とばらつきがカテゴリでどう違うかを比べる（y軸は上位1%を切った）。
plt.close("all")

# %%
# --- 解答6：年齢 vs 累計購入額 の散布図 ---
ans_total = (
    sales_done.groupby("customer_id", as_index=False)["amount"].sum()
    .merge(customers[["customer_id", "age"]], on="customer_id", how="left")
)
fig, ax = plt.subplots(figsize=(8, 5))
sns.scatterplot(data=ans_total, x="age", y="amount", ax=ax, alpha=0.4)
ax.set_title("年齢 vs 累計購入額")
ax.set_xlabel("年齢"); ax.set_ylabel("累計購入額（円）")
plt.show()
print("相関係数 r =", round(ans_total["age"].corr(ans_total["amount"]), 3))
# 伝えたいこと：年齢と累計購入額に関係があるか（相関の強さ）を示す。
plt.close("all")

# %%
# --- 解答7：相関ヒートマップ ---
ans_feat = sales_done.groupby("customer_id").agg(
    purchase_total=("amount", "sum"),
    n_orders=("order_id", "nunique"),
).reset_index()
ans_feat["avg_order"] = ans_feat["purchase_total"] / ans_feat["n_orders"]
ans_feat = ans_feat.merge(customers[["customer_id", "age"]], on="customer_id", how="left")
ans_corr = ans_feat[["age", "purchase_total", "n_orders", "avg_order"]].corr()
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(ans_corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-1, vmax=1, ax=ax)
ax.set_title("顧客指標の相関ヒートマップ")
plt.tight_layout(); plt.show()
print(ans_corr.round(2))
# 伝えたいこと：どの顧客指標どうしが連動するか（例：累計額と注文回数）を俯瞰する。
plt.close("all")

# %%
# --- 解答8：ミニダッシュボード（2つ並べる） ---
fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
# 左：月次推移
axes[0].plot(ans_monthly["month"], ans_monthly["amount"], marker="o", color="#4C72B0")
axes[0].set_title("月次売上の推移")
axes[0].set_xlabel("年月"); axes[0].set_ylabel("売上（円）")
# 右：カテゴリ別売上（降順）
sns.barplot(data=ans_cat, x="category", y="amount", ax=axes[1], color="#55A868")
axes[1].set_title("カテゴリ別売上")
axes[1].set_xlabel("カテゴリ"); axes[1].set_ylabel("売上（円）")
axes[1].tick_params(axis="x", rotation=20)
fig.suptitle("Sora Mart 売上ダッシュボード", fontsize=14)
plt.tight_layout(); plt.show()
# 伝えたいこと：いつ（推移）と何が（カテゴリ）売れているかを1枚で俯瞰させる。
plt.close("all")

# %% [markdown]
# ## おつかれさまでした 🎉
#
# このモジュールで身につけたこと：
# - matplotlib の figure/axes、seaborn での簡潔な描画
# - **目的（推移・比較・分布・関係・構成比・相関）→ グラフ種**の選び方
# - 1グラフ1メッセージ、軸ラベル・単位、ソート、誤解を生む表現の回避
# - subplots でのダッシュボード、色と注釈での強調
#
# グラフは「描けた」がゴールではなく、**「相手が次の一手を決められる」**がゴールです。
#
# 次は、見えた差が「偶然か・意味があるか」を数字で判断する統計へ。
#
# 👉 次のモジュール：**07. 統計**（`docs/07_statistics.md`）
