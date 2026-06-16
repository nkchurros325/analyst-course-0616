# %% [markdown]
# # 09. 総合演習（ケーススタディ）
#
# 🎯 **このモジュールのゴール**：これまで学んだ SQL／pandas・前処理・EDA・可視化・統計・回帰を
# **一気通貫**で使い、1つのビジネス課題に「**結論 → 根拠 → 提案**」で答えきる。
#
# **前提**：モジュール01〜08。特に 01（アナリストの思考法）の5ステップをこの章で実際になぞります。
#
# ---
#
# ## ストーリー
#
# あなたは架空EC「**Sora Mart**」のデータアナリスト。経営からこう相談されました。
#
# > 「最近、**売上の伸びが鈍化している気がする**。
# > ① 現状を把握し、② 伸び悩みの要因仮説を立て、③ 次に打つべき施策を提案してほしい。
# > 特に『どの**顧客層・経路・カテゴリ**に注力すべきか』
# > 『先日の **A/Bテスト（ボタン色）** の結果は本番投入してよいか』を知りたい。」
#
# この章は **🖊 課題（あなたが分析する）** 形式です。各セクションにスケルトンを置いています。
# まず自分で手を動かし、最後の **✅ 解答例** と **経営向けサマリー** で答え合わせをしてください。
#
# > 🧭 総合演習の心構え：**正解は1つではありません**。大事なのは
# > （1）手順（型）をなぞること、（2）**示唆と提案まで言い切る**こと、（3）**不確実性を正直に添える**こと。

# %%
# === セットアップ（最初に必ず実行）===
import os
import numpy as np
import pandas as pd

# --- 可視化（Jupyter ではこの "Agg" の行は不要。スクリプト実行時にブロックしないため）---
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

# --- 統計・検定（sklearn / statsmodels は使わない。回帰は scipy / numpy で）---
from scipy import stats


def find_data_dir():
    for base in [".", "..", "../..", os.path.join("..", "data-analyst-course")]:
        cand = os.path.join(base, "data")
        if os.path.exists(os.path.join(cand, "customers.csv")):
            return cand
    raise FileNotFoundError("data フォルダが見つかりません。python scripts/generate_data.py を実行してください。")


DATA = find_data_dir()
print("データ:", os.path.abspath(DATA))

# %% [markdown]
# ## 1. 課題設定 ── ビジネス課題を「分析の問い」に翻訳する
#
# ふわっとした相談を、**データで答えられる問い**に分解します（モジュール01の①問い・②設計）。
#
# | ステップ | このケースでの中身 |
# |---------|------------------|
# | ① 問い | 売上の伸びは本当に鈍化したか？ 鈍化なら客数・客単価・頻度のどれが効く？ 注力セグメントは？ A/Bは投入可か？ |
# | ② 設計 | KPIを定義（下表）。比較軸を決める（前年比・MoM・セグメント間・A vs B）。 |
# | ③ 取得・加工 | 4テーブルを merge し、`completed` のみで分析用データセットを作る。 |
# | ④ 分析・解釈 | 推移 → 要因分解 → セグメント → リピート → A/Bテスト → 回帰。 |
# | ⑤ 伝達 | 経営向けサマリー（結論ファースト）。 |
#
# ### KPIの定義（先に決めるのが肝心）
#
# | 指標 | 定義 |
# |------|------|
# | 売上（GMV） | Σ(`quantity × unit_price`)、**`status='completed'` のみ** |
# | 注文数 | `completed` の注文数 |
# | 購入顧客数 | `completed` の注文を持つ顧客数 |
# | 客単価（AOV） | 売上 ÷ 注文数 |
# | 購入頻度 | 注文数 ÷ 購入顧客数 |
# | リピート率 | 2回以上購入した顧客の割合 |
# | CVR（A/B） | converted=1 ÷ ユーザー数 |
#
# > 💡 売上を語るには分解が要る：`売上 = 購入顧客数 × 購入頻度 × 客単価`。
# > どの項が効いているかで、打つ手（獲得／リピート促進／単価アップ）が変わります。

# %% [markdown]
# ## 2. データ準備 ── 分析用データセットを作る
#
# ### 📖 解説：売上分析の土台は「明細レベルのロングテーブル」
#
# 4つのテーブルを `merge` でつなぎ、**1行＝1注文明細**のロングテーブルを作ります。
# このとき **`status='completed'` だけに絞る** のが鉄則でした（cancelled/returned は売上ではない）。
#
# 列を足しておくと後が楽：`amount`（明細金額）、`year`、`ym`（年月）、`age_band`（年代）。

# %%
# ▶️ 例：4テーブルを読み込み、merge して分析用ロングテーブル li を作る
customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
products = pd.read_csv(os.path.join(DATA, "products.csv"))
orders = pd.read_csv(os.path.join(DATA, "orders.csv"))
order_items = pd.read_csv(os.path.join(DATA, "order_items.csv"))

order_items = order_items.copy()
order_items["amount"] = order_items["quantity"] * order_items["unit_price"]

# 明細 → 注文 → 商品 → 顧客 の順に結合
li = (
    order_items
    .merge(orders, on="order_id", how="left")
    .merge(products, on="product_id", how="left")
    .merge(customers, on="customer_id", how="left")
)

# 🔑 売上は completed のみ
li = li[li["status"] == "completed"].copy()

# 分析しやすい派生列
li["order_date"] = pd.to_datetime(li["order_date"])
li["year"] = li["order_date"].dt.year
li["ym"] = li["order_date"].dt.to_period("M").astype(str)
bins = [17, 29, 39, 49, 59, 120]
labels = ["20代以下", "30代", "40代", "50代", "60代以上"]
li["age_band"] = pd.cut(li["age"], bins=bins, labels=labels)

print("ロングテーブル li:", li.shape)
print("総売上（completed）:", f"{int(li['amount'].sum()):,} 円")
print("注文数:", li["order_id"].nunique(), " 購入顧客数:", li["customer_id"].nunique())
print(li[["order_id", "amount", "category", "acquisition_channel", "ym"]].head())

# %% [markdown]
# ### 🖊 課題1（やさしい）：分析用データセットを自分で作る
#
# 上の例にならって、`completed` のみの分析用ロングテーブルを自分で組み立ててください。
#
# - 4テーブルを merge する
# - `amount = quantity × unit_price` を持たせる
# - `status == 'completed'` で絞る
# - 総売上・注文数・購入顧客数を print する
#
# **期待される答えのヒント**：総売上はおよそ **1.2億円**、注文数 5,000件台、顧客 1,400人台。

# %%
# ここに分析を書く
# my_li = order_items.merge(...).merge(...)...
# my_li = my_li[my_li["status"] == "completed"]
# print(...)
pass

# %% [markdown]
# ## 3. 現状把握 ── 推移・前年比・季節性
#
# ### 📖 解説：「鈍化している気がする」は、まず推移を描いて事実確認
#
# 相談の「伸び悩み」は仮説にすぎません。**月次推移**と**前年比・MoM（前月比）**を描いて確かめます。
# 全体は伸びていても、**直近の伸び率（MoM）が頭打ち**という“ねじれ”が見えることがあります。

# %%
# ▶️ 例：月次売上の推移と、前月比（MoM）成長率を描く
monthly = li.groupby("ym")["amount"].sum().sort_index()

fig, axes = plt.subplots(1, 2, figsize=(13, 4))
axes[0].plot(monthly.index, monthly.values, marker="o")
axes[0].set_title("月次売上は右肩上がり（事業の立ち上がり期）")
axes[0].set_xlabel("年月"); axes[0].set_ylabel("売上(円)")
axes[0].tick_params(axis="x", rotation=90)

mom = monthly.pct_change() * 100
axes[1].bar(mom.index, mom.values, color=np.where(mom.values < 0, "#d9534f", "#5b9bd5"))
axes[1].axhline(0, color="black", lw=0.8)
axes[1].set_title("だが直近の前月比(MoM)は頭打ち・マイナス月も")
axes[1].set_xlabel("年月"); axes[1].set_ylabel("前月比(%)")
axes[1].tick_params(axis="x", rotation=90)
fig.tight_layout()
plt.show()  # Jupyterではこのセルの下に図が表示される
plt.close(fig)

print("直近6か月の売上:")
print(monthly.tail(6).map(lambda v: f"{int(v):,}"))
print("\n2024年のMoM(%):")
print((monthly[monthly.index >= "2024-01"].pct_change() * 100).round(1).dropna())

# %% [markdown]
# ### 🖊 課題2：年次の売上と前年比、季節性を見る
#
# 1. **年次売上**（2023 vs 2024）を出し、伸び率（前年比）を計算する。
# 2. **月（1〜12月）ごとの平均売上**を見て、季節性（売れる月／売れない月）があるか確かめる。
# 3. グラフを1枚描き、タイトルに**気づいたこと**を書く。
#
# **期待される答えのヒント**：2024年は2023年の数倍（事業拡大期）。
# 月別では年末（11〜12月）が高め。ただし2023年は前半データが薄いので解釈に注意。

# %%
# ここに分析を書く
# yearly = li.groupby("year")["amount"].sum()
# print(yearly, yearly.pct_change())
# by_month = li.groupby(li["order_date"].dt.month)["amount"].mean()
pass

# %% [markdown]
# ## 4. 要因分解 ── 売上 = 客数 × 頻度 × 客単価、そしてセグメント比較
#
# ### 📖 解説：どこが効いているかを「分解」で語る
#
# `売上 = 購入顧客数 × 購入頻度 × 客単価(AOV)`。
# 年ごとにこの3項を出すと、「成長は獲得（客数）で起きたのか、単価で起きたのか」が言えます。
# さらに **経路別・カテゴリ別・地域別・年代別** で構成を比べ、注力先を探します。

# %%
# ▶️ 例：年ごとに「客数 × 頻度 × 客単価」に分解する
order_amt = li.groupby("order_id").agg(
    amount=("amount", "sum"),
    customer_id=("customer_id", "first"),
    year=("year", "first"),
)
decomp = order_amt.groupby("year").agg(
    rev=("amount", "sum"),
    orders=("amount", "count"),
    customers=("customer_id", "nunique"),
)
decomp["AOV"] = decomp["rev"] / decomp["orders"]
decomp["頻度"] = decomp["orders"] / decomp["customers"]
print("年次の要因分解：")
print(decomp.assign(
    rev=decomp["rev"].map(lambda v: f"{int(v):,}"),
    AOV=decomp["AOV"].round(0),
    頻度=decomp["頻度"].round(2),
))
print("\n→ 客単価(AOV)はほぼ横ばい。成長は主に『購入顧客数』の増加で起きている。")

# %%
# ▶️ 例：セグメント別の売上構成（経路別・カテゴリ別）を1枚で
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
ch = li.groupby("acquisition_channel")["amount"].sum().sort_values()
ch.plot(kind="barh", ax=axes[0], color="#5b9bd5")
axes[0].set_title("経路別売上：検索広告とオーガニックが二本柱")
axes[0].set_xlabel("売上(円)"); axes[0].set_ylabel("")

cat = li.groupby("category")["amount"].sum().sort_values()
cat.plot(kind="barh", ax=axes[1], color="#70ad47")
axes[1].set_title("カテゴリ別売上：インテリアが突出、次いで美容")
axes[1].set_xlabel("売上(円)"); axes[1].set_ylabel("")
fig.tight_layout()
plt.close(fig)

print("経路別売上 上位:")
print(ch.sort_values(ascending=False).map(lambda v: f"{int(v):,}"))
print("\nカテゴリ別売上 上位:")
print(cat.sort_values(ascending=False).map(lambda v: f"{int(v):,}"))

# %% [markdown]
# ### 🖊 課題3：地域別・年代別の売上を比較する
#
# 1. **都道府県別**の売上 上位5を出す（どこが太い市場か）。
# 2. **年代別**（`age_band`）の売上を出し、どの層が中心か見る。
# 3. 「注力すべき顧客層・地域」について、**一文で示唆**を書く（コメントでよい）。
#
# **期待される答えのヒント**：都市部（東京・神奈川など）が太い。年代は30〜40代が中心になりやすい。
# 「太い層をさらに伸ばす」か「薄い層を開拓する」かは戦略次第＝正解は1つではない。

# %%
# ここに分析を書く
# by_pref = li.groupby("prefecture")["amount"].sum().sort_values(ascending=False)
# by_age = li.groupby("age_band", observed=True)["amount"].sum()
pass

# %% [markdown]
# ### 🖊 課題4（やや難）：カテゴリ × 年 のクロス集計で「伸びているカテゴリ」を探す
#
# 2023→2024 でどのカテゴリが伸びたか／鈍いかを見たい。
#
# 1. `pivot_table` で 行=カテゴリ・列=年・値=売上 のクロス集計を作る。
# 2. 各カテゴリの **2024/2023 の伸び率** を計算して並べる。
# 3. 「注力カテゴリ」の候補を1つ挙げ、理由を一言。
#
# **期待される答えのヒント**：2023は立ち上がり期で値が小さいため伸び率は全カテゴリ大。
# **構成比（シェア）** と合わせて見ると解釈しやすい。`normalize` や `div(axis=...)` が便利。

# %%
# ここに分析を書く
# pv = li.pivot_table(index="category", columns="year", values="amount", aggfunc="sum")
# pv["伸び率"] = pv[2024] / pv[2023]
pass

# %% [markdown]
# ## 5. リピート/離脱の視点 ── 新規 vs リピート、購入回数の分布
#
# ### 📖 解説：成長の「質」を見る
#
# 売上が新規獲得だけで成り立っていると、獲得が鈍ると成長も止まります。
# **リピート顧客がどれだけ売上を支えているか**、**購入回数の分布**を見ます。
#
# 各注文が「その顧客の何回目か」を `cumcount()` で数え、1回目を **新規**、2回目以降を **リピート** とします。

# %%
# ▶️ 例：注文を新規 / リピートに分け、それぞれの売上シェアを見る
oa = (
    li.groupby("order_id")
    .agg(amount=("amount", "sum"),
         customer_id=("customer_id", "first"),
         order_date=("order_date", "first"),
         year=("year", "first"))
    .sort_values("order_date")
)
oa["nth"] = oa.groupby("customer_id").cumcount()  # 0 が初回
oa["type"] = np.where(oa["nth"] == 0, "新規", "リピート")

share = oa.groupby(["year", "type"])["amount"].sum().unstack()
share_pct = share.div(share.sum(axis=1), axis=0) * 100
print("年×タイプ 売上シェア(%):")
print(share_pct.round(1))

# 購入回数の分布
cnt = oa.groupby("customer_id").size()
repeat_rate = (cnt >= 2).mean()
print(f"\n購入顧客数: {cnt.shape[0]} 人 / リピート率(2回以上): {repeat_rate:.1%}")
print("購入回数の分布(上位):")
print(cnt.value_counts().sort_index().head(6))

fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(cnt.values, bins=range(1, cnt.max() + 2), color="#5b9bd5", edgecolor="white", align="left")
ax.set_title(f"購入回数の分布：リピート率{repeat_rate:.0%}、売上はリピーターが大半を牽引")
ax.set_xlabel("1顧客あたり購入回数"); ax.set_ylabel("顧客数")
fig.tight_layout()
plt.close(fig)

# %% [markdown]
# ### 🖊 課題5：リピート顧客の重要性を数字で示す
#
# 1. 2024年について、**リピート注文の売上シェア**を出す（新規 vs リピートの割合）。
# 2. リピート顧客（2回以上）一人あたりの平均売上 と、1回だけの顧客の平均売上を比べる。
# 3. 「リピートを伸ばすべきか」について一文で示唆を書く。
#
# **期待される答えのヒント**：2024年はリピートが売上の大半（7割超）。
# → 新規獲得だけでなく**リピート促進が成長の鍵**、という主張が立つ。

# %%
# ここに分析を書く
# share2024 = oa[oa["year"] == 2024].groupby("type")["amount"].sum()
pass

# %% [markdown]
# ## 6. A/Bテストの判断 ── 本番投入してよいか？
#
# ### 📖 解説：差が「偶然」か「本物」かを検定で判断（モジュール07の応用）
#
# 商品ページの購入ボタンの色を **A（現行）/ B（新色）** で出し分けたテスト結果が `ab_test.csv` にあります
# （`group`, `converted`=購入したか0/1, `session_seconds`）。
#
# 比べたいのは**コンバージョン率（CVR）**。2群×2値（購入/非購入）なので **カイ二乗検定** が定番です。
# 報告は必ず **「p値・リフト・ビジネス判断」をセット** で。

# %%
# ▶️ 例：A/Bテストをカイ二乗検定で判断する
ab = pd.read_csv(os.path.join(DATA, "ab_test.csv"))
summary = ab.groupby("group")["converted"].agg(n="count", conv="sum", cvr="mean")
print("A/Bテスト集計:")
print(summary.assign(cvr=summary["cvr"].map(lambda v: f"{v:.2%}")))

# 分割表（行=group, 列=converted）でカイ二乗検定
table = pd.crosstab(ab["group"], ab["converted"])
chi2, p, dof, expected = stats.chi2_contingency(table)
lift = summary.loc["B", "cvr"] / summary.loc["A", "cvr"] - 1

print(f"\nカイ二乗統計量 = {chi2:.2f},  p値 = {p:.4f}")
print(f"CVR: A={summary.loc['A','cvr']:.2%}, B={summary.loc['B','cvr']:.2%}  → リフト = {lift:+.1%}")
print("判断:", "有意差あり（偶然では起きにくい）。Bが優勢→本番投入を推奨" if p < 0.05
      else "有意差なし。投入は保留しデータを増やす")

fig, ax = plt.subplots(figsize=(5.5, 4))
ax.bar(summary.index, summary["cvr"] * 100, color=["#9aa0a6", "#5b9bd5"])
ax.set_title(f"ボタン色B はCVR {lift:+.0%}（p={p:.3f}）→ 投入推奨")
ax.set_ylabel("CVR(%)")
for i, v in enumerate(summary["cvr"] * 100):
    ax.text(i, v + 0.1, f"{v:.2f}%", ha="center")
fig.tight_layout()
plt.close(fig)

# %% [markdown]
# ### 🖊 課題6：A/Bテストの結論を自分で出す
#
# 1. A群・B群の CVR を計算する。
# 2. カイ二乗検定（または2標本の比率の検定）で **p値** を出す。
# 3. **リフト（B/A − 1）** を計算する。
# 4. **本番投入の是非**を、p値・リフト・ビジネス視点でひとことで結論する。
#    （おまけ：`session_seconds` に差があるか t検定で見てもよい）
#
# **期待される答えのヒント**：B の CVR が有意に高い（p < 0.05）。リフトは＋3割前後。
# → 「投入推奨」。ただし**検定期間・季節要因・新色の慣れ**などの不確実性も添える。

# %%
# ここに分析を書く
# table = pd.crosstab(ab["group"], ab["converted"])
# chi2, p, dof, expected = stats.chi2_contingency(table)
pass

# %% [markdown]
# ## 7. 回帰での補足 ── 顧客の購入額を説明する要因
#
# ### 📖 解説：sklearn/statsmodels なしで重回帰（numpy の最小二乗）
#
# 「顧客1人の年間購入額」は何で説明できるか、ざっくり見ます。
# 説明変数：`age`（年齢）、`購入回数`、（カテゴリカルは one-hot）。
# 回帰は **`np.linalg.lstsq`**（最小二乗）で係数を求めます（モジュール08の手法）。
#
# > ⚠️ これは**説明（記述）**であって因果ではありません。「効く要因の当たりをつける」程度に。

# %%
# ▶️ 例：顧客単位に集計し、numpy で重回帰
cust_df = (
    li.groupby("customer_id")
    .agg(total_amount=("amount", "sum"),
         n_orders=("order_id", "nunique"),
         age=("age", "first"),
         channel=("acquisition_channel", "first"))
    .reset_index()
)
# 説明変数: age, n_orders, channel(one-hot)
X = pd.get_dummies(cust_df[["age", "n_orders", "channel"]], columns=["channel"], drop_first=True)
X = X.astype(float)
feat_names = ["切片"] + list(X.columns)
Xmat = np.column_stack([np.ones(len(X)), X.values])
y = cust_df["total_amount"].values.astype(float)

coef, *_ = np.linalg.lstsq(Xmat, y, rcond=None)
pred = Xmat @ coef
ss_res = ((y - pred) ** 2).sum()
ss_tot = ((y - y.mean()) ** 2).sum()
r2 = 1 - ss_res / ss_tot

print("重回帰：顧客の年間購入額を説明する（np.linalg.lstsq）")
for name, c in zip(feat_names, coef):
    print(f"  {name:<28} 係数 = {c:>12,.0f}")
print(f"\n決定係数 R^2 = {r2:.3f}")
print("→ 圧倒的に効くのは『購入回数』。1回増えるごとに購入額が大きく伸びる（=リピートの価値）。")

# %% [markdown]
# ### 🖊 課題7（難）：単回帰で「購入回数 → 購入額」の関係を確かめる
#
# 重回帰だと解釈が難しいので、まずは単純に「購入回数」と「年間購入額」の関係を見ます。
#
# 1. `scipy.stats.linregress` で `n_orders`（説明）→ `total_amount`（目的）を回帰する。
# 2. 傾き・切片・相関係数 r・p値 を出す。
# 3. 散布図＋回帰直線を描き、「リピートが1回増えると購入額がいくら増えるか」を一文で。
#
# **期待される答えのヒント**：傾きは正で有意（p≈0）。
# 「購入回数はLTV（顧客生涯価値）の強い説明因子」→ リピート促進の根拠になる。

# %%
# ここに分析を書く
# res = stats.linregress(cust_df["n_orders"], cust_df["total_amount"])
# print(res.slope, res.intercept, res.rvalue, res.pvalue)
pass

# %% [markdown]
# ## 8. 統合 ── 結論 → 根拠 → 提案
#
# ### 🖊 課題8（仕上げ）：経営向けサマリーを書く
#
# ここまでの分析を、**意思決定者が動ける**形にまとめます。次の構成で、Markdownセルに文章で書いてください。
#
# - **【結論】** 問いへの答えを一文で（伸びは鈍化したか？）。
# - **【根拠】** 数字を3〜4点（推移／要因分解／セグメント／リピート／A/B）。
# - **【示唆】** その数字が意味すること。
# - **【提案】** 次に打つべき施策（経路・カテゴリ・リピート・A/B投入）。
# - **【不確実性】** このデータで言えないこと（購入者のみ／因果は不明 等）。
#
# **期待される答えのヒント**：下の「✅ 解答例」の経営向けサマリーと見比べてください。
# 数字や強調点が違っても構いません。**提案まで言い切れているか**が評価ポイントです。

# %% [markdown]
# ---
# # ✅ 解答例（分析の進め方の一例）
#
# > ここからは模範解答です。**正解は1つではありません**。
# > あなたの分析が違う切り口でも、「事実→示唆→提案」がつながっていればOKです。

# %%
# --- 解答1：分析用データセットを作る ---
oi = order_items.copy()
oi["amount"] = oi["quantity"] * oi["unit_price"]
sol_li = (
    oi.merge(orders, on="order_id")
      .merge(products, on="product_id")
      .merge(customers, on="customer_id")
)
sol_li = sol_li[sol_li["status"] == "completed"].copy()
sol_li["order_date"] = pd.to_datetime(sol_li["order_date"])

print("総売上:", f"{int(sol_li['amount'].sum()):,} 円")
print("注文数:", sol_li["order_id"].nunique())
print("購入顧客数:", sol_li["customer_id"].nunique())

# %%
# --- 解答2：年次売上・前年比・季節性 ---
yearly = li.groupby("year")["amount"].sum()
print("年次売上:")
print(yearly.map(lambda v: f"{int(v):,}"))
print("前年比:", f"{yearly.pct_change().iloc[-1]:.1%}",
      "（2023は事業立ち上がりで前半データが薄い点に注意）")

by_month = li.groupby(li["order_date"].dt.month)["amount"].mean()
print("\n月別 平均売上（季節性）:")
print(by_month.map(lambda v: f"{int(v):,}"))
print("→ 年末(11〜12月)が高めの傾向。明確な季節性は弱いが年末商戦は意識する価値あり。")

# %%
# --- 解答3：地域別・年代別 ---
by_pref = li.groupby("prefecture")["amount"].sum().sort_values(ascending=False)
print("都道府県別売上 上位5:")
print(by_pref.head(5).map(lambda v: f"{int(v):,}"))

by_age = li.groupby("age_band", observed=True)["amount"].sum().sort_values(ascending=False)
print("\n年代別売上:")
print(by_age.map(lambda v: f"{int(v):,}"))
print("\n示唆：都市部・働き盛り層が太い。まずは太い層の取りこぼし防止（在庫・配送・再訪促進）が効率的。"
      "\n      ただし『薄い層の開拓』も成長余地。どちらに賭けるかは経営判断＝正解は1つではない。")

# %%
# --- 解答4：カテゴリ × 年 のクロス集計 ---
pv = li.pivot_table(index="category", columns="year", values="amount", aggfunc="sum").fillna(0)
pv["伸び率(24/23)"] = (pv[2024] / pv[2023]).round(1)
pv["2024シェア(%)"] = (pv[2024] / pv[2024].sum() * 100).round(1)
disp = pv.sort_values("2024シェア(%)", ascending=False).copy()
disp[2023] = disp[2023].map(lambda v: f"{int(v):,}")
disp[2024] = disp[2024].map(lambda v: f"{int(v):,}")
print(disp)
print("\n注力候補：売上シェア最大の『インテリア』。2024シェアが高く絶対額も大きいので、"
      "ここの品揃え・訴求を厚くするのが最も売上インパクトが大きい。")

# %%
# --- 解答5：リピート顧客の重要性 ---
oa2 = (
    li.groupby("order_id")
    .agg(amount=("amount", "sum"), customer_id=("customer_id", "first"),
         order_date=("order_date", "first"), year=("year", "first"))
    .sort_values("order_date")
)
oa2["nth"] = oa2.groupby("customer_id").cumcount()
oa2["type"] = np.where(oa2["nth"] == 0, "新規", "リピート")

s24 = oa2[oa2["year"] == 2024].groupby("type")["amount"].sum()
print("2024年 売上（新規 vs リピート）:")
print(s24.map(lambda v: f"{int(v):,}"))
print("リピートの売上シェア:", f"{s24['リピート'] / s24.sum():.1%}")

cnt = oa2.groupby("customer_id").size()
one = li[li["customer_id"].isin(cnt[cnt == 1].index)].groupby("customer_id")["amount"].sum().mean()
rep = li[li["customer_id"].isin(cnt[cnt >= 2].index)].groupby("customer_id")["amount"].sum().mean()
print(f"\n1回だけ顧客の平均購入額: {one:,.0f} 円 / リピート顧客の平均購入額: {rep:,.0f} 円")
print("示唆：2024年の売上の大半をリピーターが牽引。新規一本足では成長が鈍る。"
      "\n      → リピート促進（メルマガ・再訪クーポン・定期便）が成長の鍵。")

# %%
# --- 解答6：A/Bテストの判断 ---
ab = pd.read_csv(os.path.join(DATA, "ab_test.csv"))
summ = ab.groupby("group")["converted"].agg(n="count", conv="sum", cvr="mean")
table = pd.crosstab(ab["group"], ab["converted"])
chi2, p, dof, expected = stats.chi2_contingency(table)
lift = summ.loc["B", "cvr"] / summ.loc["A", "cvr"] - 1

print(f"CVR  A={summ.loc['A','cvr']:.2%}  B={summ.loc['B','cvr']:.2%}")
print(f"カイ二乗 = {chi2:.2f}, p = {p:.4f}, リフト = {lift:+.1%}")

# おまけ：滞在時間に差があるか t検定
ta = ab[ab["group"] == "A"]["session_seconds"].dropna()
tb = ab[ab["group"] == "B"]["session_seconds"].dropna()
t_stat, t_p = stats.ttest_ind(ta, tb, equal_var=False)
print(f"滞在時間 t検定: t={t_stat:.2f}, p={t_p:.3f}（{'差あり' if t_p < 0.05 else '差は明確でない'}）")

print("\n結論：B（新色）はCVRが有意に高い（p<0.05, リフト約+35%）。→ 本番投入を推奨。"
      "\n不確実性：テスト期間が限られ季節要因や『新色の目新しさ』の影響が残る可能性。"
      "\n          投入後も2〜4週間モニタリングし、効果が持続するか確認する。")

# %%
# --- 解答7：単回帰（購入回数 → 購入額）---
cust = (
    li.groupby("customer_id")
    .agg(total_amount=("amount", "sum"), n_orders=("order_id", "nunique"))
    .reset_index()
)
res = stats.linregress(cust["n_orders"], cust["total_amount"])
print(f"傾き = {res.slope:,.0f} 円/回, 切片 = {res.intercept:,.0f} 円")
print(f"相関 r = {res.rvalue:.3f}, p値 = {res.pvalue:.2e}, R^2 = {res.rvalue**2:.3f}")

fig, ax = plt.subplots(figsize=(6.5, 4.5))
ax.scatter(cust["n_orders"], cust["total_amount"], alpha=0.3, s=14, color="#5b9bd5")
xs = np.array([cust["n_orders"].min(), cust["n_orders"].max()])
ax.plot(xs, res.intercept + res.slope * xs, color="#d9534f", lw=2)
ax.set_title(f"購入回数1回↑で購入額 約{res.slope:,.0f}円↑（r={res.rvalue:.2f}）：リピートはLTVの核")
ax.set_xlabel("購入回数"); ax.set_ylabel("年間購入額(円)")
fig.tight_layout()
plt.close(fig)
print("\n示唆：購入回数は購入額(LTV)の強い説明因子。リピートを1回増やす施策の価値は大きい。")

# %% [markdown]
# ## 📣 解答8：経営向けサマリー（結論ファースト）
#
# > 以下は意思決定者にそのまま渡せる形のサマリー例です。**結論→根拠→示唆→提案→不確実性**の順。
#
# ### 【結論】
# 売上は前年比では**大きく伸びた（事業拡大期）**が、**直近半年の月次の伸び率（MoM）は頭打ち**で、
# マイナスの月も出てきている。「伸び悩みの気配」は事実として確認できた。
# 伸びの主因は**新規顧客の獲得**で、**客単価（AOV）はほぼ横ばい**。成長を支えているのは**リピート顧客**。
#
# ### 【根拠】
# - **推移**：月次売上は右肩上がりだが、2024年後半のMoMは 0% 近辺でマイナス月も発生。
# - **要因分解**（売上＝客数×頻度×客単価）：成長はほぼ**客数増**による。AOVは約2.2万円で横ばい、頻度は微増。
# - **セグメント**：経路は**検索広告＋オーガニック検索**が二本柱。カテゴリは**インテリア**が突出（次いで美容・アパレル）。市場は都市部・働き盛り層が太い。
# - **リピート**：2024年売上の**約7割をリピーターが牽引**。リピート率は高め。購入回数は購入額(LTV)の強い説明因子（単回帰で有意）。
# - **A/Bテスト**：新色ボタンBのCVRは**有意に高い（p<0.05, リフト約+35%）**。
#
# ### 【示唆】
# - 新規獲得“一本足”では、獲得効率が鈍ると成長が止まる。**リピート（LTV）を伸ばす**ことが次の成長ドライバー。
# - 売上インパクトは**上位経路・上位カテゴリ**に集中しているため、まずはここの取りこぼし防止が効率的。
#
# ### 【提案】
# 1. **経路**：検索広告・オーガニック検索（二本柱）に予算を集中。SNS広告は費用対効果を再点検。
# 2. **カテゴリ**：インテリア（＋美容）の品揃え・訴求・在庫を厚くし、関連商品のクロスセルを強化。
# 3. **リピート促進**：初回購入者への再訪クーポン／メルマガ／定期便で2回目購入率を引き上げる（LTV施策）。
# 4. **A/Bテスト**：新色ボタンBは**本番投入を推奨**。投入後2〜4週間モニタリングし効果の持続を確認。
#
# ### 【不確実性（言えないこと）】
# - 本データは**購入者中心**で、非購入者・離脱者・サイト訪問数は含まないため CVR全体や離脱要因は別途計測が必要。
# - 観測データのため、セグメント差は**相関**であり**因果ではない**（施策の効果検証はA/Bテストで）。
# - 2023年は立ち上がり期でデータが薄く、前年比の大きさは割り引いて解釈する。
#
# ---
#
# おつかれさまでした。これで全モジュール完了です。
# 解説は [docs/09_capstone.md](../docs/09_capstone.md)（講座のまとめ・次に学ぶこと）も参照してください。🎉
