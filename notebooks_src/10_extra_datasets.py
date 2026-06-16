# %% [markdown]
# # 10. 発展演習：いろいろなパターンのデータ
#
# 🎯 **このモジュールのゴール**：メイン教材（02〜09）で学んだ手法を、
# **データの“形”が異なる6つのデータセット**で実際に手を動かして試す。
# 「データが変われば、見るべき指標も手法も変わる」を体感する総合演習です。
#
# 💡 **メイン教材（02〜09）を一通りやってから取り組むと効果的**です。
# ここでは新しい理論は増やさず、学んだ型（**分布と欠損を見る → 比較軸を決める → 可視化 → 解釈**）を
# いろいろな題材で繰り返します。
#
# **扱う6つのデータ（カタログ docs/data_catalog.md 参照）**
# 1. `timeseries/web_traffic_daily.csv` … 日次Webアクセス（**単一の時系列**）
# 2. `marketing/ad_campaigns.csv` … 広告チャネル別実績（**比率・ファネル**）
# 3. `survey/customer_survey.csv` … 顧客アンケート（**カテゴリ・リッカート。欠損あり**）
# 4. `hr/employees.csv` … 従業員データ（**混合型・回帰・離職**）
# 5. `iot/sensor_readings.csv` … センサー（**高頻度時系列・異常検知。欠損・外れ値あり**）
# 6. `finance/stock_prices.csv` … 株価（**複数時系列ロング形式・相関**）
#
# 各セクションは「📖 このデータの形」→「▶️ 代表的な分析の例」→「🖊 EXERCISE（スケルトン）」の順。
# 演習の答えは末尾の **## ✅ 解答例** にまとめてあります。
#
# > ⚠️ この講座の規約どおり **sklearn / statsmodels は使いません**。回帰は scipy と numpy で実装します。

# %%
# === セットアップ（最初に必ず実行）===
import os
import sys

# Windows のコンソールが cp932 だと日本語の print で文字化け/エラーになるため UTF-8 に統一
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
# ---
# # 1. 📈 web_traffic_daily — 日次Webアクセス（時系列パターン）
#
# ## 📖 このデータの形と「まず何を見るか」
# 1行 = 1日の Web アクセス指標（`sessions / users / pageviews / bounce_rate / conversions / revenue`）。
# **単一の時系列**なので、まず見るのは **トレンド（右肩上がり？）／季節性（曜日・週末効果）／欠測・異常日**。
# 生の日次データはギザギザなので、**集計（月次）** や **移動平均（7日）** でならして傾向を読みます。
# このデータには **8日分の欠測（NaN）** が仕込まれています。

# %%
# ▶️ 例：月次集計の折れ線 ＋ 7日移動平均でトレンドを見る
web = pd.read_csv(os.path.join(DATA, "timeseries", "web_traffic_daily.csv"), parse_dates=["date"])
print("期間:", web["date"].min().date(), "〜", web["date"].max().date(), " 行数:", len(web))
print("欠測のある行数（sessions）:", int(web["sessions"].isna().sum()))

web = web.sort_values("date").set_index("date")

# 月次合計（NaN は自動でスキップされる）
monthly = web["sessions"].resample("MS").sum()
print("\n月次セッション合計（先頭3か月）:")
print(monthly.head(3))

# 7日移動平均（min_periods=1 で端も計算。欠測は前方補完してからならす）
web["sessions_filled"] = web["sessions"].interpolate(method="linear")
web["ma7"] = web["sessions_filled"].rolling(7, min_periods=1).mean()

fig, ax = plt.subplots(1, 2, figsize=(13, 4))
monthly.plot(ax=ax[0], marker="o")
ax[0].set_title("月次セッション合計の推移")
ax[0].set_ylabel("セッション数")
web["sessions"].plot(ax=ax[1], alpha=0.4, label="日次（生）")
web["ma7"].plot(ax=ax[1], color="crimson", label="7日移動平均")
ax[1].set_title("日次セッション と 7日移動平均")
ax[1].legend()
plt.tight_layout()
plt.show()
plt.close("all")

# %% [markdown]
# ## 🖊 EXERCISE 1
#
# **問1-1**：曜日別の平均セッション数を比較してください（平日 vs 週末はどうか？）。
# ヒント：`web.index.dayofweek`（0=月〜6=日）で `groupby`。土日が低いはず。
#
# **問1-2**：平常時から大きく外れた「異常な日」を検出してください（**平均±3σ**）。
# ヒント：`sessions` の平均 `m` と標準偏差 `s` を出し、`m+3s` を超える日を抽出。キャンペーンのスパイクが見えるはず。

# %%
# ここにコードを書く（問1-1：曜日別の平均セッション）
# dow_mean = web.groupby(web.index.dayofweek)["sessions"].mean()
# print(dow_mean)

# ここにコードを書く（問1-2：±3σ で異常日を検出）
# m, s = ...
# anomalies = web[...]
pass

# %% [markdown]
# ---
# # 2. 🎯 ad_campaigns — 広告チャネル別実績（比率・ファネルパターン）
#
# ## 📖 このデータの形と「まず何を見るか」
# 1行 = ある日・あるチャネルの広告実績。`impressions → clicks → conversions` という**ファネル構造**で、
# 売上(`revenue`)と広告費(`cost`)も入っています。生の数値そのものより、
# **比率の指標（CTR/CVR/CPA/ROAS）で“効率”を比較**するのが主役です。
#
# | 指標 | 計算 | 意味 |
# |------|------|------|
# | CTR  | clicks / impressions | クリック率 |
# | CVR  | conversions / clicks | コンバージョン率 |
# | CPA  | cost / conversions | 獲得単価（低いほど良い） |
# | ROAS | revenue / cost | 広告費用対効果（高いほど良い） |

# %%
# ▶️ 例：チャネル別に CTR / CVR / CPA / ROAS を計算して比較
ad = pd.read_csv(os.path.join(DATA, "marketing", "ad_campaigns.csv"), parse_dates=["date"])
print("チャネル:", list(ad["channel"].unique()))

# 比率は「合計してから割る」のが鉄則（日次の比率を平均すると小さい日に引っ張られる）
g = ad.groupby("channel")[["impressions", "clicks", "cost", "conversions", "revenue"]].sum()
g["CTR(%)"] = g["clicks"] / g["impressions"] * 100
g["CVR(%)"] = g["conversions"] / g["clicks"] * 100
g["CPA(円)"] = g["cost"] / g["conversions"]
g["ROAS(倍)"] = g["revenue"] / g["cost"]

summary = g[["CTR(%)", "CVR(%)", "CPA(円)", "ROAS(倍)"]].round(2).sort_values("ROAS(倍)", ascending=False)
print("\nチャネル別の効率（ROAS降順）:")
print(summary.to_string())
print("\n最も ROAS が高いチャネル:", summary.index[0], f"({summary['ROAS(倍)'].iloc[0]:.2f} 倍)")

fig, ax = plt.subplots(figsize=(8, 4))
summary["ROAS(倍)"].plot(kind="bar", ax=ax, color="seagreen")
ax.axhline(1.0, color="gray", ls="--", label="ROAS=1（損益分岐）")
ax.set_title("チャネル別 ROAS")
ax.set_ylabel("ROAS（倍）")
ax.legend()
plt.tight_layout()
plt.show()
plt.close("all")

# %% [markdown]
# ## 🖊 EXERCISE 2
#
# **問2-1**：「クリックは多いが CVR が低い（＝ファネルの後半で落ちている）」チャネルを見つけてください。
# ヒント：`clicks` の合計が多いのに `CVR(%)` が低いチャネルを `summary` から読む。
#
# **問2-2**：予算を移すなら「どこから・どこへ」が妥当か、ROAS と CPA を根拠に一言で述べてください（print で結論）。
# ヒント：ROAS が最も低い（または CPA が最も高い）チャネル → ROAS が最も高いチャネルへ。

# %%
# ここにコードを書く（問2-1：クリック多いのにCVR低いチャネル）
# tmp = g[["clicks"]].copy(); tmp["CVR(%)"] = ...
# print(tmp.sort_values("clicks", ascending=False))

# ここにコードを書く（問2-2：予算移管の考察を print）
# print("予算移管案: ... から ... へ")
pass

# %% [markdown]
# ---
# # 3. 🗳 customer_survey — 顧客アンケート（カテゴリ・リッカートパターン）
#
# ## 📖 このデータの形と「まず何を見るか」
# 1行 = 1人の回答。`satisfaction` や `q_quality/q_price/q_support` は **1〜5のリッカート尺度**、
# `recommend_score` は **0〜10（NPS用）**。**複数列に欠損（未回答）**があります。
# まず見るのは **欠損の量／NPS／セグメント（会員種別など）による満足度の違い**。
#
# 💡 **NPS**：推奨度 9-10 を「推奨者」、0-6 を「批判者」とし、`NPS = 推奨者割合 − 批判者割合`（%）。

# %%
# ▶️ 例：欠損の確認 → NPS算出 → 会員種別 × 満足度クロス集計
sv = pd.read_csv(os.path.join(DATA, "survey", "customer_survey.csv"))
print("回答者数:", len(sv))
print("\n列ごとの欠損数:")
print(sv.isna().sum()[sv.isna().sum() > 0])


def calc_nps(scores):
    s = scores.dropna()
    promoters = (s >= 9).mean()
    detractors = (s <= 6).mean()
    return (promoters - detractors) * 100

nps_all = calc_nps(sv["recommend_score"])
print(f"\n全体NPS: {nps_all:.1f}")
print("会員種別別NPS:")
print(sv.groupby("membership")["recommend_score"].apply(calc_nps).round(1))

# 会員種別 × 年代の満足度クロス集計
cross = sv.pivot_table(index="membership", columns="age_group", values="satisfaction", aggfunc="mean")
print("\n会員種別 × 年代 の平均満足度:")
print(cross.round(2).to_string())

fig, ax = plt.subplots(figsize=(8, 3.5))
sns.heatmap(cross, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax)
ax.set_title("平均満足度（会員種別 × 年代）")
plt.tight_layout()
plt.show()
plt.close("all")

# %% [markdown]
# ## 🖊 EXERCISE 3
#
# **問3-1（満足度ドライバー）**：総合満足度 `satisfaction` と最も相関が強い項目評価（`q_quality / q_price / q_support`）は
# どれでしょうか。ヒント：`sv[[...]].corr()` の `satisfaction` 行を見る（欠損は corr が自動で対応）。
#
# **問3-2（欠損の扱い）**：`q_support` の欠損を「①除外したとき」と「②全体平均で補完したとき」で、
# `q_support` の平均がどう変わるか比較してください。ヒント：`dropna()` と `fillna(平均)`。

# %%
# ここにコードを書く（問3-1：満足度ドライバー＝相関）
# corr = sv[["satisfaction", "q_quality", "q_price", "q_support"]].corr()
# print(corr["satisfaction"].sort_values(ascending=False))

# ここにコードを書く（問3-2：欠損の扱いで平均がどう変わるか）
# print("除外:", ...); print("平均補完:", ...)
pass

# %% [markdown]
# ---
# # 4. 👥 employees — 従業員データ（混合型・回帰/群比較パターン）
#
# ## 📖 このデータの形と「まず何を見るか」
# 1行 = 1人の従業員。**数値（給与・勤続・残業…）＋カテゴリ（部署・学歴…）＋フラグ（離職）** が混ざった混合型。
# 給与は **職級・勤続・学歴** で説明でき（→ 回帰）、離職は **残業が多い／エンゲージメントが低い** ほど起きやすい（→ 群比較）。
# まず見るのは **群ごとの平均の違い** と **数値どうしの関係（回帰）**。

# %%
# ▶️ 例：給与を「職級・勤続・学歴」で重回帰（np.linalg.lstsq）し、係数を解釈
emp = pd.read_csv(os.path.join(DATA, "hr", "employees.csv"))
print("従業員数:", len(emp), " 離職率:", f"{emp['attrition'].mean()*100:.1f}%")

# 学歴はカテゴリ → ダミー変数化（drop_first で基準カテゴリを1つ落とす）
edu_dummies = pd.get_dummies(emp["education"], prefix="edu", drop_first=True).astype(float)
X = pd.concat([emp[["job_level", "tenure_years"]].astype(float), edu_dummies], axis=1)
X.insert(0, "切片", 1.0)  # 切片項
y = emp["monthly_salary"].astype(float).values

A = X.values
coef, _, _, _ = np.linalg.lstsq(A, y, rcond=None)

# R²（決定係数）を手計算
y_hat = A @ coef
ss_res = np.sum((y - y_hat) ** 2)
ss_tot = np.sum((y - y.mean()) ** 2)
r2 = 1 - ss_res / ss_tot

print("\n重回帰の係数（給与 ≈ 切片 + 各係数×変数）:")
for name, c in zip(X.columns, coef):
    print(f"  {name:12s}: {c:>12,.0f} 円")
print(f"\nR²（決定係数）: {r2:.3f}  → 給与のばらつきの {r2*100:.1f}% を説明")
print("解釈：職級が1上がると月給が約 {:,.0f}円、勤続1年で約 {:,.0f}円 増える傾向。".format(coef[1], coef[2]))

# %% [markdown]
# ## 🖊 EXERCISE 4
#
# **問4-1（離職の群比較）**：離職した人（`attrition==1`）としていない人で、
# `overtime_hours`（残業）と `engagement_score`（エンゲージメント）の平均を比較してください。
# ヒント：`emp.groupby("attrition")[["overtime_hours", "engagement_score"]].mean()`。
#
# **問4-2（t検定）**：残業時間の差が偶然と言えるか、**2標本のt検定**で確かめてください（`scipy.stats.ttest_ind`）。
# ヒント：p値が 0.05 未満なら「差は統計的に有意」。離職群の残業が多いはず。

# %%
# ここにコードを書く（問4-1：離職有無で群比較）
# print(emp.groupby("attrition")[["overtime_hours", "engagement_score"]].mean())

# ここにコードを書く（問4-2：残業時間の t検定）
# a = emp.loc[emp["attrition"] == 1, "overtime_hours"]
# b = emp.loc[emp["attrition"] == 0, "overtime_hours"]
# t, p = stats.ttest_ind(a, b, equal_var=False)
# print(f"t={t:.2f}, p={p:.4f}")
pass

# %% [markdown]
# ---
# # 5. 🏭 sensor_readings — 製造ラインのセンサー（高頻度時系列・異常検知パターン）
#
# ## 📖 このデータの形と「まず何を見るか」
# 1行 = ある時刻・ある機械（M-01〜M-04）の計測値（`temperature / vibration / pressure / rpm`）と不良フラグ `defect`。
# **高頻度の時系列**で、**緩やかなドリフト（劣化）／突発スパイク（外れ値）／センサー欠損** が混ざります。
# まず見るのは **欠損の補間** と **外れ値検出（±3σ や IQR）**、そして **不良時と正常時の差**。

# %%
# ▶️ 例：機械別の温度時系列 ＋ 欠損の線形補間 ＋ ±3σ で外れ値検出
sen = pd.read_csv(os.path.join(DATA, "iot", "sensor_readings.csv"), parse_dates=["timestamp"])
print("行数:", len(sen), " 機械:", list(sen["machine_id"].unique()))
print("欠損数:\n", sen[["temperature", "vibration", "pressure", "rpm"]].isna().sum())

sen = sen.sort_values(["machine_id", "timestamp"])
# 機械ごとに温度を線形補間（時系列なので前後をつないで埋める）
sen["temp_filled"] = sen.groupby("machine_id")["temperature"].transform(lambda s: s.interpolate(method="linear"))

# ±3σ で外れ値検出（機械ごとに基準を作る）
def flag_outliers(s):
    m, sd = s.mean(), s.std()
    return (s > m + 3 * sd) | (s < m - 3 * sd)

sen["is_outlier"] = sen.groupby("machine_id")["temp_filled"].transform(flag_outliers)
print("\n温度の外れ値（±3σ）件数:", int(sen["is_outlier"].sum()))

fig, ax = plt.subplots(figsize=(11, 4))
for mid, sub in sen.groupby("machine_id"):
    ax.plot(sub["timestamp"], sub["temp_filled"], label=mid, alpha=0.8)
out = sen[sen["is_outlier"]]
ax.scatter(out["timestamp"], out["temp_filled"], color="red", s=25, zorder=5, label="外れ値(±3σ)")
ax.set_title("機械別 温度の時系列（補間後）と外れ値")
ax.set_ylabel("温度(℃)")
ax.legend(ncol=5, fontsize=8)
plt.tight_layout()
plt.show()
plt.close("all")

# %% [markdown]
# ## 🖊 EXERCISE 5
#
# **問5-1（不良時 vs 正常時）**：不良が出たとき（`defect==1`）と出ないときで、
# `temperature` と `vibration` の平均に差があるか比較してください。
# ヒント：`sen.groupby("defect")[["temp_filled", "vibration"]].mean()`。不良時は高温・高振動のはず。
#
# **問5-2（しきい値ルール）**：不良を見つける簡単なルールを1つ作り、その**的中度**を確認してください。
# 例：「温度 > しきい値 かつ 振動 > しきい値」を不良候補とし、そのうち実際に不良だった割合（適合率）を出す。
# ヒント：不良群の温度・振動の中央値あたりをしきい値の目安にする。

# %%
# ここにコードを書く（問5-1：不良時 vs 正常時の差）
# print(sen.groupby("defect")[["temp_filled", "vibration"]].mean())

# ここにコードを書く（問5-2：しきい値ルールの的中度）
# rule = (sen["temp_filled"] > T) & (sen["vibration"] > V)
# print("ルール該当数:", rule.sum(), " うち実際に不良:", sen.loc[rule, "defect"].mean())
pass

# %% [markdown]
# ---
# # 6. 💹 stock_prices — 株価（複数時系列・相関パターン）
#
# ## 📖 このデータの形と「まず何を見るか」
# 1行 = 1銘柄・1日の終値（**ロング形式**）。まず `pivot` で **ワイド形式（日付×銘柄）** に直すと分析しやすくなります。
# 株価そのものより **日次リターン（前日比）** に注目し、**ボラティリティ（リスク）** と **銘柄間の相関** を見ます。

# %%
# ▶️ 例：pivot でワイド化 → 日次リターン → 相関ヒートマップ
stk = pd.read_csv(os.path.join(DATA, "finance", "stock_prices.csv"), parse_dates=["date"])
print("銘柄:", list(stk["ticker"].unique()), " 営業日数:", stk["date"].nunique())

wide = stk.pivot(index="date", columns="ticker", values="close").sort_index()
returns = wide.pct_change().dropna()  # 日次リターン
print("\n各銘柄の日次リターン（平均・標準偏差=リスク）:")
stats_tbl = pd.DataFrame({
    "平均リターン(%)": returns.mean() * 100,
    "リスク(標準偏差%)": returns.std() * 100,
}).round(3)
print(stats_tbl.to_string())

corr = returns.corr()
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax[0])
ax[0].set_title("銘柄間リターン相関")
(1 + returns).cumprod().plot(ax=ax[1])  # 累積リターン（1から始めた指数）
ax[1].set_title("累積リターン（初日=1）")
ax[1].set_ylabel("指数")
plt.tight_layout()
plt.show()
plt.close("all")

# %% [markdown]
# ## 🖊 EXERCISE 6
#
# **問6-1（ボラ比較）**：最もリスク（リターンの標準偏差）が高い銘柄と低い銘柄はどれでしょうか。
# ヒント：`returns.std().sort_values()` の両端。
#
# **問6-2（累積リターン）**：500営業日を通して**最も成長した銘柄**はどれでしょうか。
# ヒント：`(1 + returns).cumprod().iloc[-1]` が最大の銘柄。

# %%
# ここにコードを書く（問6-1：ボラ比較）
# vol = returns.std().sort_values()
# print("最低リスク:", vol.index[0], " 最高リスク:", vol.index[-1])

# ここにコードを書く（問6-2：累積リターンが最大の銘柄）
# final = (1 + returns).cumprod().iloc[-1]
# print(final.sort_values(ascending=False))
pass

# %% [markdown]
# ---
# # ✅ 解答例
#
# 各演習の解答です。すべて上のセットアップ＋各セクションの読み込みを実行した状態で動きます。

# %%
# --- 解答(web_traffic-1) ---
dow_labels = ["月", "火", "水", "木", "金", "土", "日"]
dow_mean = web.groupby(web.index.dayofweek)["sessions"].mean()
dow_mean.index = dow_labels
print("曜日別 平均セッション:")
print(dow_mean.round(0))
print("→ 週末(土日)は平日より低く、'週末はアクセスが落ちる' 効果が確認できる。")

# %%
# --- 解答(web_traffic-2) ---
m, s = web["sessions"].mean(), web["sessions"].std()
upper = m + 3 * s
anomalies = web[web["sessions"] > upper]
print(f"平均={m:.0f}, 標準偏差={s:.0f}, +3σしきい値={upper:.0f}")
print(f"異常に高い日: {len(anomalies)}件（キャンペーンのスパイクと推定）")
print(anomalies[["sessions"]].round(0).to_string())

# %%
# --- 解答(ad_campaigns-1) ---
funnel = g[["clicks"]].copy()
funnel["CVR(%)"] = (g["conversions"] / g["clicks"] * 100).round(2)
funnel = funnel.sort_values("clicks", ascending=False)
print("クリック数 と CVR:")
print(funnel.to_string())
low_cvr = funnel["CVR(%)"].idxmin()
print(f"\n→ '{low_cvr}' はクリックの割にCVRが低く、ファネル後半（CV）で落ちている。")

# %%
# --- 解答(ad_campaigns-2) ---
best = summary.index[0]
worst_roas = summary["ROAS(倍)"].idxmin()
print(f"予算移管案：ROAS最低の『{worst_roas}』(ROAS={summary.loc[worst_roas, 'ROAS(倍)']:.2f}) から、"
      f"ROAS最高の『{best}』(ROAS={summary.loc[best, 'ROAS(倍)']:.2f}) へ。")
print(f"  根拠：CPA も『{summary['CPA(円)'].idxmax()}』が最も高く獲得効率が悪い。")

# %%
# --- 解答(survey-1) ---
corr_sat = sv[["satisfaction", "q_quality", "q_price", "q_support"]].corr()["satisfaction"].drop("satisfaction")
print("総合満足度との相関:")
print(corr_sat.sort_values(ascending=False).round(3))
print(f"→ 満足度の最大ドライバーは『{corr_sat.idxmax()}』(相関 {corr_sat.max():.3f})。")

# %%
# --- 解答(survey-2) ---
drop_mean = sv["q_support"].dropna().mean()
fill_mean = sv["q_support"].fillna(sv["q_support"].mean()).mean()
print(f"①欠損を除外したときの q_support 平均: {drop_mean:.3f}")
print(f"②全体平均で補完したときの平均      : {fill_mean:.3f}")
print("→ 平均値補完では平均は変わらない（同じ値で埋めるため）。補完は分散を縮める副作用に注意。")

# %%
# --- 解答(employees-1) ---
grp = emp.groupby("attrition")[["overtime_hours", "engagement_score"]].mean()
grp.index = ["在籍(0)", "離職(1)"]
print(grp.round(2).to_string())
print("→ 離職者は残業が多く、エンゲージメントが低い傾向。")

# %%
# --- 解答(employees-2) ---
a = emp.loc[emp["attrition"] == 1, "overtime_hours"]
b = emp.loc[emp["attrition"] == 0, "overtime_hours"]
t, p = stats.ttest_ind(a, b, equal_var=False)
print(f"離職群の平均残業={a.mean():.1f}h, 在籍群={b.mean():.1f}h")
print(f"t={t:.2f}, p={p:.2e} → " + ("差は統計的に有意（p<0.05）。" if p < 0.05 else "有意な差とは言えない。"))

# %%
# --- 解答(sensor-1) ---
diff = sen.groupby("defect")[["temp_filled", "vibration"]].mean()
diff.index = ["正常(0)", "不良(1)"]
print(diff.round(2).to_string())
print(f"→ 不良時の平均温度は {diff.loc['不良(1)', 'temp_filled']:.1f}℃ で、正常時より高温・高振動。")

# %%
# --- 解答(sensor-2) ---
# しきい値は不良群の中央値を目安にする
T = sen.loc[sen["defect"] == 1, "temp_filled"].median()
V = sen.loc[sen["defect"] == 1, "vibration"].median()
rule = (sen["temp_filled"] > T) & (sen["vibration"] > V)
hit = sen.loc[rule, "defect"]
print(f"ルール：温度>{T:.1f}℃ かつ 振動>{V:.2f}")
print(f"  該当 {int(rule.sum())} 件、うち実際に不良 {int(hit.sum())} 件 → 適合率(精度) {hit.mean()*100:.1f}%")
print(f"  全不良 {int(sen['defect'].sum())} 件中 {int(hit.sum())} 件を捕捉（再現率 {hit.sum()/sen['defect'].sum()*100:.1f}%）")

# %%
# --- 解答(stock-1) ---
vol = returns.std().sort_values()
print("リスク（日次リターン標準偏差）昇順:")
print((vol * 100).round(3).to_string())
print(f"→ 最低リスク: {vol.index[0]} / 最高リスク: {vol.index[-1]}")

# %%
# --- 解答(stock-2) ---
final = (1 + returns).cumprod().iloc[-1].sort_values(ascending=False)
print("累積リターン（初日=1, 最終日の指数）:")
print(final.round(3).to_string())
print(f"→ 最も成長した銘柄: {final.index[0]}（{final.iloc[0]:.2f}倍）")

# %% [markdown]
# ---
# ## 🎓 講座全体のまとめ
#
# 6つのまったく違う形のデータを触ってきましたが、やったことの **型は共通** でした。
#
# > **① 分布と欠損を見る → ② 比較軸を決める → ③ 可視化 → ④ 解釈**
#
# - 時系列なら「集計・移動平均でならす／曜日・季節性／異常日」を見る（web_traffic, sensor, stock）。
# - 比率データなら「合計してから割る」で効率指標を作り**比較**する（ad_campaigns）。
# - アンケートなら「欠損の扱い」を決め、**NPS やクロス集計**でセグメント差を見る（survey）。
# - 混合型なら「群比較＋検定」と「回帰」で**要因**を探る（employees）。
# - 複数時系列なら `pivot` で整え、**リターン・リスク・相関**で読む（stock）。
#
# データが変われば見るべき指標や手法は変わりますが、**「まず分布と欠損、次に比較軸」** という入り口は同じです。
#
# 👉 メイン教材に戻って総合演習 **09（capstone）** をやり切ると、この型が一気通貫でつながります。
# 各手法の詳細は **README** と 各モジュール（05 記述統計・06 可視化・07 検定・08 回帰）を参照してください。
# お疲れさまでした！
