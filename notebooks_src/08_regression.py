# %% [markdown]
# # 08. 相関と回帰分析
#
# 🎯 **このモジュールのゴール**：2つ以上の変数の関係を「相関」と「回帰」で読み解き、
# 傾き・係数・R²（決定係数）を **日本語で正しく解釈** できるようになる。
#
# **前提**：モジュール05（記述統計・分布）、06（可視化）。相関と因果の話は01の再確認です。
#
# **このノートでやること**
# - 相関：散布図・相関行列・ヒートマップ・ピアソン相関係数
# - 単回帰：`scipy.stats.linregress` で直線あてはめ・R²・残差
# - 重回帰：`np.linalg.lstsq` で複数説明変数・係数の解釈・R²の手計算
# - カテゴリ変数：`pd.get_dummies` で獲得経路を回帰に入れる
# - 解釈の注意：外挿・過学習・相関と因果
#
# > ⚠️ このモジュールでは **sklearn / statsmodels は使いません**。回帰は scipy と numpy だけで実装します。

# %%
# === セットアップ（最初に必ず実行）===
import os
import sys

# Windows のコンソールが cp932 だと「²」などが print で文字化け/エラーになるため UTF-8 に統一
# （Jupyter では何も起きません。スクリプト実行時の保険です）
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")  # スクリプト実行時に plt.show() でブロックしないため（Jupyterではこの行は不要）
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
for _c in ["Meiryo", "Yu Gothic", "MS Gothic", "Hiragino Sans", "IPAexGothic", "Noto Sans CJK JP"]:
    if _c in {f.name for f in font_manager.fontManager.ttflist}:
        rcParams["font.family"] = _c
        break
rcParams["axes.unicode_minus"] = False
import seaborn as sns
sns.set_theme(style="whitegrid", font=rcParams["font.family"])

import numpy as np
import pandas as pd
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
# ## 📖 解説：分析用テーブルを作る（顧客ごとに集計）
#
# 回帰の出発点は「**1行が何を表すか（集計の単位）**」を決めること。今回は **1行 = 1顧客**。
#
# 講座の規約どおり、売上は
# **`order_items.quantity × order_items.unit_price` を合計し、`status=='completed'` のみ** を対象にします。
#
# 手順：
# 1. orders と order_items を結合し、明細の金額を計算
# 2. `completed` だけ残す
# 3. 注文ごとに金額を合計 → さらに顧客ごとに `total_spend`（累計購入額）と `n_orders`（注文回数）を集計
# 4. 顧客マスタ（age, gender, acquisition_channel, prefecture）と結合

# %%
customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
orders = pd.read_csv(os.path.join(DATA, "orders.csv"))
items = pd.read_csv(os.path.join(DATA, "order_items.csv"))

# 明細に注文情報を結合し、明細金額を計算
oi = orders.merge(items, on="order_id")
oi["amount"] = oi["quantity"] * oi["unit_price"]

# 売上は completed のみ
completed = oi[oi["status"] == "completed"].copy()

# まず注文単位で金額を合計（1注文=複数明細のため）
order_amount = (
    completed.groupby(["customer_id", "order_id"])["amount"].sum().reset_index()
)

# 顧客単位に集計
agg = (
    order_amount.groupby("customer_id")
    .agg(total_spend=("amount", "sum"), n_orders=("order_id", "nunique"))
    .reset_index()
)
agg["avg_order"] = agg["total_spend"] / agg["n_orders"]  # 平均客単価

# 顧客マスタと結合（completed 注文がある顧客だけが残る）
cust = customers.merge(agg, on="customer_id", how="inner")

print("分析対象の顧客数:", len(cust))
print(cust[["age", "acquisition_channel", "total_spend", "n_orders", "avg_order"]].head())

# %% [markdown]
# ## 📖 解説：相関 ── 一緒に動くか
#
# 2変数が「一緒に動くか」を1つの数字で測るのが **ピアソン相関係数 `r`**（−1〜+1）。
#
# - `+1`：完全な右上がり / `0`：直線関係なし / `−1`：完全な右下がり
# - 計算前に **必ず散布図** を見る（曲線関係や外れ値を見落とさないため）。
#
# | \|r\| | 目安 |
# |------|------|
# | 0.0〜0.2 | ほぼなし |
# | 0.2〜0.4 | 弱い |
# | 0.4〜0.7 | 中程度 |
# | 0.7〜1.0 | 強い |
#
# ⚠️ **相関 ≠ 因果**：強い相関でも「AがBの原因」とは限らない（第3の変数・逆向き・偶然）。

# %%
# 数値列の相関行列
num_cols = ["age", "total_spend", "n_orders", "avg_order"]
corr = cust[num_cols].corr()
print("相関行列:")
print(corr.round(3))

# ヒートマップで可視化
fig, ax = plt.subplots(figsize=(5.5, 4.5))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-1, vmax=1, ax=ax)
ax.set_title("数値変数の相関行列")
plt.tight_layout()
plt.close(fig)  # スクリプト実行時はファイルに残さず閉じる（Jupyterでは plt.show() でOK）

# 2変数だけなら scipy で相関係数と p値の両方が得られる
r, p = stats.pearsonr(cust["n_orders"], cust["total_spend"])
print(f"\nn_orders と total_spend: r = {r:.3f}, p = {p:.3g}")

# %% [markdown]
# ## 📖 解説：単回帰 ── 直線をあてはめる
#
# 1つの説明変数 `x` で目的変数 `y` を説明する直線 `y = a*x + b` を、
# データに最もよく合うように引きます（最小二乗法）。`scipy.stats.linregress` を使います。
#
# - **傾き `a`**：x が1増えると y は平均 `a` 変わる。
# - **切片 `b`**：x=0 のときの予測値（x=0 が非現実的なら意味は薄い）。
# - **R²（決定係数）**：y のばらつきのうち式で説明できた割合。**単回帰では R² = r²**。
# - 残差（実測−予測）をプロットして、ランダムに散らばっていればあてはまりは妥当。

# %%
res = stats.linregress(cust["n_orders"], cust["total_spend"])
print(f"傾き a      = {res.slope:,.1f} 円/回")
print(f"切片 b      = {res.intercept:,.1f} 円")
print(f"相関係数 r  = {res.rvalue:.3f}")
print(f"R²          = {res.rvalue**2:.3f}")
print(f"傾きのp値    = {res.pvalue:.3g}")
print(f"傾きの標準誤差= {res.stderr:,.1f}")

# 散布図 + 回帰直線
x = cust["n_orders"]
fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(x, cust["total_spend"], s=10, alpha=0.4)
xs = np.array([x.min(), x.max()])
ax.plot(xs, res.slope * xs + res.intercept, color="red", lw=2, label="回帰直線")
ax.set_xlabel("注文回数 n_orders")
ax.set_ylabel("累計購入額 total_spend")
ax.set_title("単回帰：n_orders → total_spend")
ax.legend()
plt.tight_layout()
plt.close(fig)

# 残差プロット
y_hat = res.slope * cust["n_orders"] + res.intercept
resid = cust["total_spend"] - y_hat
fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(y_hat, resid, s=10, alpha=0.4)
ax.axhline(0, color="red", lw=1)
ax.set_xlabel("予測値")
ax.set_ylabel("残差（実測 − 予測）")
ax.set_title("残差プロット")
plt.tight_layout()
plt.close(fig)
print("\n解釈例：注文が1回増えると累計購入額は平均で約",
      f"{res.slope:,.0f} 円増える。R²は約 {res.rvalue**2:.2f}",
      "（購入額のばらつきの約8割を注文回数で説明）。")

# %% [markdown]
# ## 📖 解説：重回帰 ── 複数の説明変数（np.linalg.lstsq）
#
# 説明変数を複数にすると `y = b + a1*x1 + a2*x2 + ...`。
# sklearn は使わず **numpy の最小二乗 `np.linalg.lstsq`** で解きます。
# **切片を入れるため「全部1の列（定数項）」を足す** のがポイント。
#
# - 係数 `a_j` は **「他の変数を固定したまま」** x_j を1増やしたときの y の平均変化量。
# - R²（決定係数）は手計算：`R² = 1 - 残差平方和 / 全平方和`。

# %%
def fit_ols(X, y):
    """定数項を足して最小二乗で回帰。係数(切片含む)・予測・R²を返す。"""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    Xc = np.column_stack([np.ones(len(X)), X])      # 先頭に切片用の1列
    beta, *_ = np.linalg.lstsq(Xc, y, rcond=None)   # beta[0]=切片, 以降が各説明変数
    y_hat = Xc @ beta
    ss_res = ((y - y_hat) ** 2).sum()               # 残差平方和
    ss_tot = ((y - y.mean()) ** 2).sum()            # 全平方和
    r2 = 1 - ss_res / ss_tot                         # 決定係数（手計算）
    return beta, y_hat, r2


X = cust[["age", "n_orders"]].to_numpy(float)
y = cust["total_spend"].to_numpy(float)
beta, y_hat, r2 = fit_ols(X, y)

print(f"切片            = {beta[0]:,.1f}")
print(f"age の係数      = {beta[1]:,.1f} 円/歳")
print(f"n_orders の係数 = {beta[2]:,.1f} 円/回")
print(f"R²              = {r2:.3f}")
print("\n解釈：他を一定としたとき、注文が1回増えると累計購入額は平均約",
      f"{beta[2]:,.0f} 円増える。年齢の係数は小さく、購入額への寄与はほぼない。")

# %% [markdown]
# ## 📖 解説：カテゴリ変数をダミー化して回帰に入れる
#
# `acquisition_channel`（検索広告/SNS広告/…）はそのまま回帰に入れられないので
# **ダミー変数（0/1）** に展開します。`pd.get_dummies(..., drop_first=True)` で
# 1カテゴリを基準として落とす（ダミー変数の罠の回避）。
#
# - ダミーの係数は **「基準カテゴリと比べた差」** と読む。
# - 説明変数を増やすと R² は基本下がらない。だから **「R²が上がった＝良いモデル」とは限らない**（過学習のさわり）。

# %%
dum = pd.get_dummies(cust["acquisition_channel"], prefix="ch", drop_first=True).astype(float)
base_channel = sorted(cust["acquisition_channel"].unique())[0]  # 落とされた基準カテゴリ
print("ダミー列:", list(dum.columns))

X2 = np.column_stack([cust[["age", "n_orders"]].to_numpy(float), dum.to_numpy()])
beta2, _, r2_dum = fit_ols(X2, y)

names = ["切片", "age", "n_orders"] + list(dum.columns)
print("\n係数:")
for nm, b in zip(names, beta2):
    print(f"  {nm:18s} = {b:,.1f}")
print(f"\nR²（ダミーあり）= {r2_dum:.3f}  / R²（ダミーなし）= {r2:.3f}")
print(f"基準カテゴリ（係数0扱い）= {base_channel}")
print("解釈：各ダミー係数は基準経路と比べた累計購入額の差（他を一定として）。R²の変化はごくわずか。")

# %% [markdown]
# ## 📖 解説：解釈の注意 ── ここを外すと事故る
#
# - **外挿の危険**：データ範囲外（例：注文100回）の予測は保証外。
# - **過学習のさわり**：変数を増やすほど学習データのR²は上がるが、未知データに弱くなることも。
# - **相関と因果**：回帰の係数は関係の強さであって因果ではない。
# - **見せかけの回帰**：共通トレンドで無関係同士でも高いR²が出ることがある。
# - **欠損・スケール**：欠損は方針を決めて処理。単位が違う変数は係数の大小を直接比較しない。
#
# 🧭 合言葉：**「この回帰から言えること／言えないこと」を1文ずつ書く。**

# %% [markdown]
# ## 🖊 EXERCISE
#
# 上で作った `cust`（1行=1顧客の集計テーブル）を使って解きます。
# **各問、係数やR²の「日本語での解釈」を必ず一言書くこと。**
#
# 1. （易）数値4列の相関行列を作り、ヒートマップで描く。**最も相関の強いペア**を答える。
#    - ヒント：`cust[num_cols].corr()`、対角(=1.0)は除いて最大を探す。
# 2. （易）`n_orders` と `total_spend` の散布図を描き、`pearsonr` で相関係数とp値を出す。
#    - ヒント：`plt.scatter` と `stats.pearsonr`。
# 3. （中）`linregress` で `n_orders → total_spend` の単回帰。傾きとR²を解釈し、回帰直線を散布図に重ねる。
#    - ヒント：傾き＝「注文1回増で購入額が平均いくら増えるか」。
# 4. （中）問3の残差プロット（横軸=予測値、縦軸=残差）を描き、あてはまりが妥当か一言。
#    - ヒント：残差が0周りにランダムなら妥当。
# 5. （中）`np.linalg.lstsq` で `age, n_orders → total_spend` の重回帰。各係数を「他を一定として」解釈する。
#    - ヒント：定数項列を足す。`fit_ols` を使ってよい。
# 6. （難）`get_dummies` で `acquisition_channel` を加えた重回帰。R²がどう変わるか、ダミー係数を1つ解釈する。
#    - ヒント：`drop_first=True`。係数は基準経路との差。
# 7. （難）`avg_order`（平均客単価）を `age` で単回帰。傾き・R²から「年齢で客単価を説明できるか」を述べる。
#    - ヒント：R²が小さければ「ほとんど説明できない」。
# 8. （難・記述）この一連の回帰から **言えること / 言えないこと** を、因果に踏み込まずに2〜3文で書く。
#    - ヒント：言える＝関係の向き・強さ。言えない＝因果、範囲外の予測。

# %%
# --- 演習用スケルトン（ここに自分のコードを書く）---
num_cols = ["age", "total_spend", "n_orders", "avg_order"]

# 問1: 相関行列とヒートマップ、最強ペア
# ここにコードを書く

# 問2: 散布図 + pearsonr
# ここにコードを書く

# 問3: linregress 単回帰 + 回帰直線
# ここにコードを書く

# 問4: 残差プロット
# ここにコードを書く

# 問5: lstsq 重回帰（age, n_orders）
# ここにコードを書く

# 問6: ダミーを加えた重回帰
# ここにコードを書く

# 問7: age -> avg_order の単回帰
# ここにコードを書く

# 問8: 言えること/言えないこと（文章で）
# ここにコードを書く

pass

# %% [markdown]
# ## ✅ 解答例
#
# 以下は実データで動く解答例です。グラフはスクリプト実行時にブロックしないよう `plt.close()` していますが、
# Jupyter では `plt.close(fig)` を消して `plt.show()` にすると表示されます。

# %%
# --- 解答1 ---  相関行列とヒートマップ、最強ペア
corr = cust[num_cols].corr()
print(corr.round(3))

fig, ax = plt.subplots(figsize=(5.5, 4.5))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-1, vmax=1, ax=ax)
ax.set_title("相関行列")
plt.tight_layout()
plt.close(fig)

# 対角(自己相関=1)を除いて絶対値最大のペアを探す
c = corr.abs().copy()
np.fill_diagonal(c.values, 0.0)
i, j = np.unravel_index(np.argmax(c.values), c.shape)
print(f"最も相関が強いペア: {c.index[i]} × {c.columns[j]} (r={corr.iloc[i, j]:.3f})")
print("解釈：total_spend と n_orders が最も強い正の相関。注文が多い顧客ほど累計購入額が大きい。")

# %%
# --- 解答2 ---  散布図 + pearsonr
fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(cust["n_orders"], cust["total_spend"], s=10, alpha=0.4)
ax.set_xlabel("注文回数")
ax.set_ylabel("累計購入額")
ax.set_title("n_orders × total_spend")
plt.tight_layout()
plt.close(fig)

r, p = stats.pearsonr(cust["n_orders"], cust["total_spend"])
print(f"r = {r:.3f}, p = {p:.3g}")
print("解釈：r は0.9前後の強い正の相関。p値はほぼ0で、偶然この相関が出たとは考えにくい。")

# %%
# --- 解答3 ---  linregress 単回帰 + 回帰直線
res = stats.linregress(cust["n_orders"], cust["total_spend"])
print(f"傾き={res.slope:,.1f} 円/回, 切片={res.intercept:,.1f}, R²={res.rvalue**2:.3f}")

x = cust["n_orders"]
fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(x, cust["total_spend"], s=10, alpha=0.4)
xs = np.array([x.min(), x.max()])
ax.plot(xs, res.slope * xs + res.intercept, color="red", lw=2, label="回帰直線")
ax.set_xlabel("注文回数")
ax.set_ylabel("累計購入額")
ax.legend()
plt.tight_layout()
plt.close(fig)
print("解釈：注文が1回増えると累計購入額は平均約",
      f"{res.slope:,.0f} 円増える。R²≒{res.rvalue**2:.2f} で購入額のばらつきの約8割を説明。")

# %%
# --- 解答4 ---  残差プロット
y_hat = res.slope * cust["n_orders"] + res.intercept
resid = cust["total_spend"] - y_hat
fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(y_hat, resid, s=10, alpha=0.4)
ax.axhline(0, color="red", lw=1)
ax.set_xlabel("予測値")
ax.set_ylabel("残差")
ax.set_title("残差プロット")
plt.tight_layout()
plt.close(fig)
print("解釈：残差は0の周りに散らばるが、予測値が大きいほど残差の幅も広がるラッパ状の傾向がある。",
      "概ね直線で説明できるが、客単価のばらつきが大きい顧客では誤差が大きい。")

# %%
# --- 解答5 ---  lstsq 重回帰（age, n_orders）
X = cust[["age", "n_orders"]].to_numpy(float)
y = cust["total_spend"].to_numpy(float)
beta, _, r2 = fit_ols(X, y)
print(f"切片={beta[0]:,.1f}, age係数={beta[1]:,.1f}, n_orders係数={beta[2]:,.1f}, R²={r2:.3f}")
print("解釈：他を一定としたとき、注文1回増で購入額は平均約",
      f"{beta[2]:,.0f} 円増える。年齢の係数は小さく、購入額への寄与はほぼない。")

# %%
# --- 解答6 ---  ダミーを加えた重回帰
dum = pd.get_dummies(cust["acquisition_channel"], prefix="ch", drop_first=True).astype(float)
base_channel = sorted(cust["acquisition_channel"].unique())[0]
X2 = np.column_stack([cust[["age", "n_orders"]].to_numpy(float), dum.to_numpy()])
beta2, _, r2_dum = fit_ols(X2, y)

names = ["切片", "age", "n_orders"] + list(dum.columns)
for nm, b in zip(names, beta2):
    print(f"  {nm:18s} = {b:,.1f}")
print(f"R²（ダミーあり）={r2_dum:.3f} / R²（なし）={r2:.3f}  基準経路={base_channel}")
# 1つのダミーを取り上げて解釈
ex_name = dum.columns[0]
ex_coef = beta2[3]
print(f"解釈：'{ex_name}' の係数 {ex_coef:,.0f} は、基準（{base_channel}）に比べた累計購入額の差（他を一定として）。",
      "R²の改善はごくわずかで、獲得経路は購入額をほとんど説明しない。")

# %%
# --- 解答7 ---  age -> avg_order の単回帰
res7 = stats.linregress(cust["age"], cust["avg_order"])
print(f"傾き={res7.slope:,.2f} 円/歳, R²={res7.rvalue**2:.4f}")
print("解釈：R²はほぼ0で、年齢では平均客単価をほとんど説明できない。",
      "年齢と客単価の間に実質的な直線関係は見られない。")

# %%
# --- 解答8 ---  言えること/言えないこと（文章）
print(
    "言えること：\n"
    " ・注文回数と累計購入額には強い正の相関があり、注文が多い顧客ほど累計購入額が大きい（関係の向きと強さ）。\n"
    " ・年齢や獲得経路を加えても説明力（R²）はほとんど上がらず、累計購入額は主に注文回数で決まる。\n"
    "言えないこと：\n"
    " ・『注文を増やせば購入額が上がる』という因果は、この回帰だけでは言えない（相関≠因果）。\n"
    " ・観測範囲（注文0〜数十回）の外を予測することはできない（外挿の危険）。"
)
