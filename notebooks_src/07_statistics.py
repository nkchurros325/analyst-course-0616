# %% [markdown]
# # 07. 統計的推論と A/B テスト
#
# 🎯 **このモジュールのゴール**：手元の標本（サンプル）から母集団について何が言えるかを、
# **信頼区間**と**仮説検定**で語れるようになる。そして A/B テストを「正しく」読み解く。
#
# **前提**：モジュール01（アナリストの思考法）〜06（可視化）まで。pandas / numpy / matplotlib の基本。
#
# **題材**：`data/ab_test.csv`（`user_id, group(A/B), converted(0/1), session_seconds`）。
# group **A はコントロール（現行）**、group **B はテスト施策**、`converted` は購入の有無（1=購入）。
#
# **使う道具**：可視化（matplotlib/seaborn）＋ `scipy.stats`。
# > 検定は **scipy.stats** を使います（statsmodels / sklearn は使いません）。

# %%
# === セットアップ（最初に必ず実行）===
import os
import sys
import numpy as np
import pandas as pd

# Windowsのcp932コンソールでも日本語/記号のprintで落ちないようにUTF-8で出力
# （Jupyter では通常不要だが、害はない）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- 可視化（Jupyter では matplotlib.use("Agg") の行は不要）---
import matplotlib
matplotlib.use("Agg")  # スクリプト実行時に plt.show() でブロックしないため
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
for _c in ["Meiryo", "Yu Gothic", "MS Gothic", "Hiragino Sans", "IPAexGothic", "Noto Sans CJK JP"]:
    if _c in {f.name for f in font_manager.fontManager.ttflist}:
        rcParams["font.family"] = _c
        break
rcParams["axes.unicode_minus"] = False
import seaborn as sns
sns.set_theme(style="whitegrid", font=rcParams["font.family"])

# --- 検定ライブラリ ---
from scipy import stats


def find_data_dir():
    for base in [".", "..", "../..", os.path.join("..", "data-analyst-course")]:
        cand = os.path.join(base, "data")
        if os.path.exists(os.path.join(cand, "customers.csv")):
            return cand
    raise FileNotFoundError("data フォルダが見つかりません。python scripts/generate_data.py を実行してください。")


DATA = find_data_dir()
print("データ:", os.path.abspath(DATA))

# A/B テストデータを読み込む
ab = pd.read_csv(os.path.join(DATA, "ab_test.csv"))
print(ab.shape)
ab.head()

# %% [markdown]
# ## 📖 7-1. なぜ「推論」が必要なのか
#
# 私たちが見ているのは **たまたま集まった一部の利用者（標本）**。
# でも本当に知りたいのは **全利用者・将来の利用者まで含めた真の値（母集団）** です。
# 標本は引くたびに少し違う数字になるので、こう問います：
#
# > **「B の CVR が A より高いこの差は、偶然のブレで説明できる範囲か？ 本当に施策が効いたのか？」**
#
# まずは群ごとの規模と購入数をざっと眺めます。

# %%
# 群ごとの人数・購入数・コンバージョン率(CVR)を一気に見る
summary = ab.groupby("group")["converted"].agg(n="size", buyers="sum", cvr="mean")
summary["cvr_%"] = (summary["cvr"] * 100).round(2)
print(summary)

# %% [markdown]
# ## 📖 7-2. 中心極限定理（CLT）を体感する
#
# **中心極限定理**：元のデータがどんな分布でも、**標本平均**を何度も計算して並べると、
# サンプルサイズが大きいほどその分布は **正規分布（釣鐘型）** に近づく。
# これが信頼区間や検定の土台です。
#
# 下では「0〜1の一様分布（まったく釣鐘型でない）」から `n` 個取って平均する、を何千回も繰り返し、
# **元の分布**と**標本平均の分布**を見比べます。

# %%
rng = np.random.default_rng(7)  # 再現性のため乱数の種を固定

# 元の分布：一様分布から1万個（平らな分布）
raw = rng.uniform(0, 1, size=10000)

# 標本平均の分布：一様分布から n=30 個取って平均、を 5000 回
n = 30
sample_means = np.array([rng.uniform(0, 1, size=n).mean() for _ in range(5000)])

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].hist(raw, bins=30, color="#9aa0a6")
axes[0].set_title("元の分布（一様分布）= 平ら")
axes[1].hist(sample_means, bins=30, color="#4c8bf5")
axes[1].set_title(f"標本平均(n={n})の分布 = 釣鐘型に近づく")
fig.suptitle("中心極限定理のシミュレーション")
fig.tight_layout()
plt.show()  # Jupyterではこのセルの下に図が表示される
plt.close(fig)

print("元データの平均  :", round(raw.mean(), 3), " 標準偏差:", round(raw.std(), 3))
print("標本平均の平均  :", round(sample_means.mean(), 3))
print("標本平均の標準偏差(=標準誤差の実測):", round(sample_means.std(), 3))
print("理論上の標準誤差 σ/√n            :", round((1/np.sqrt(12))/np.sqrt(n), 3))
print("→ グラフ _clt_demo.png を保存しました（右が釣鐘型になっていれば成功）")

# %% [markdown]
# ## 🖊 EXERCISE 1（やさしい）：群ごとのコンバージョン率
#
# `ab` から **A群・B群それぞれの CVR（converted の平均）** を計算してください。
#
# > 期待される答えのヒント：A ≈ 4.4%、B ≈ 6.0% 程度。`groupby("group")["converted"].mean()` が近道。

# %%
# ここにコードを書く
# cvr = ...
# print(cvr)
pass

# %% [markdown]
# ## 🖊 EXERCISE 2（やさしい）：差とリフト（相対改善率）
#
# A群とB群の CVR の **絶対差（ポイント差）** と **リフト（相対改善率 = (B−A)/A）** を計算してください。
#
# > 期待される答えのヒント：絶対差 ≈ +1.6 ポイント、リフト ≈ +35%。

# %%
# ここにコードを書く
# cvr_a = ...
# cvr_b = ...
# abs_diff = ...
# lift = ...
pass

# %% [markdown]
# ## 📖 7-3. 標準誤差と信頼区間
#
# - **標準誤差 SE**：標本平均（や割合）のばらつき。
#   - 平均： `SE = s / √n`（s は標準偏差）
#   - 割合： `SE = √( p(1−p) / n )`
# - **95% 信頼区間** ＝ 推定値 ± **1.96** × SE （1.96 は正規分布で中央95%に対応）
#
# 信頼区間の正しい読み方：「同じやり方で取り直して区間を作るのを100回やれば、約95回は真の値を含む」。
# 実務では「真の値はだいたいこの範囲」という**幅**として使います。**区間が狭いほど精度が高い**。

# %%
# 平均（session_seconds）の 95% 信頼区間を計算するヘルパー
def mean_ci(x, z=1.96):
    x = np.asarray(x, dtype=float)
    m = x.mean()
    se = x.std(ddof=1) / np.sqrt(len(x))  # ddof=1 で不偏標準偏差
    return m, (m - z*se, m + z*se)

for g in ["A", "B"]:
    m, (lo, hi) = mean_ci(ab.loc[ab["group"] == g, "session_seconds"])
    print(f"{g}群 滞在時間: 平均 {m:6.2f} 秒  95%CI [{lo:6.2f}, {hi:6.2f}]")

# %% [markdown]
# ## 🖊 EXERCISE 3（ふつう）：コンバージョン率の95%信頼区間
#
# **割合の信頼区間**を使って、A群・B群それぞれの CVR の 95% 信頼区間を計算してください。
# 割合の標準誤差は `SE = √( p(1−p)/n )`、区間は `p ± 1.96×SE` です。
#
# > 期待される答えのヒント：A は概ね [3.9%, 4.9%]、B は [5.4%, 6.6%]。
# > **2つの区間が重なっていない** ことに注目（後の検定で「有意差あり」と整合）。

# %%
# ここにコードを書く
# def prop_ci(buyers, n, z=1.96):
#     p = buyers / n
#     se = ...
#     return p, (p - z*se, p + z*se)
# for g in ["A", "B"]:
#     ...
pass

# %% [markdown]
# ## 📖 7-4. 仮説検定の枠組み
#
# 手順は5ステップ：
#
# 1. **仮説**：H₀「差はない」 ／ H₁「差がある」
# 2. **有意水準 α** を決める（慣習で 0.05）
# 3. **検定統計量**（t値・カイ二乗値など）を計算
# 4. **p値**を出す
# 5. **判断**：`p < α` なら H₀ を棄却（＝有意差あり）、`p ≥ α` なら棄却できない
#
# **p値の正しい意味** ＝「H₀（差がない）が本当だとしたら、観測した差かそれ以上に極端な差が偶然で出る確率」。
# - ❌「H₀ が正しい確率」ではない／❌「p小さい＝効果大」ではない（効果の大きさは別途）。
#
# 誤りは2種類：**第一種(α)** = 差がないのに「ある」と言う、**第二種(β)** = 差があるのに見逃す。

# %% [markdown]
# ## 📖 7-5(a). 連続値の比較 ── session_seconds の t 検定
#
# 「A と B で平均滞在時間に差があるか」。独立した2群の平均比較なので **独立2標本 t 検定**。
# `scipy.stats.ttest_ind(..., equal_var=False)`（＝Welchのt検定、分散が等しいと仮定しない）を使います。

# %%
a_sec = ab.loc[ab["group"] == "A", "session_seconds"]
b_sec = ab.loc[ab["group"] == "B", "session_seconds"]

t_stat, p_t = stats.ttest_ind(a_sec, b_sec, equal_var=False)

print(f"A群 平均 {a_sec.mean():.2f} 秒 / B群 平均 {b_sec.mean():.2f} 秒")
print(f"t = {t_stat:.3f},  p = {p_t:.3e}")
print("--- 4点セット ---")
print("帰無仮説 H0 : A と B の母平均（滞在時間）は等しい")
print(f"p値        : {p_t:.3e}")
print("結論       : p < 0.05 なので H0 を棄却 → 滞在時間に統計的に有意な差あり（B が長い）")
print("ビジネス的意味: 施策 B は滞在時間を伸ばしている → 関与（エンゲージメント）が高い可能性")

# %% [markdown]
# ## 📖 7-5(b). 割合の比較 ── converted のカイ二乗検定
#
# CVR（割合）の差は、クロス集計表（group × converted）に対する **カイ二乗検定**
# `scipy.stats.chi2_contingency` で見ます。帰無仮説は「group と converted は独立（CVR は群によらない）」。

# %%
ct = pd.crosstab(ab["group"], ab["converted"])
print("クロス集計（行=group, 列=converted）")
print(ct)

chi2, p_chi, dof, expected = stats.chi2_contingency(ct)
print(f"\nカイ二乗 = {chi2:.3f},  自由度 = {dof},  p = {p_chi:.3e}")
print("--- 4点セット ---")
print("帰無仮説 H0 : group と converted は独立（A と B で CVR は等しい）")
print(f"p値        : {p_chi:.3e}")
print("結論       : p < 0.05 なので H0 を棄却 → CVR に統計的に有意な差あり（B が高い）")
print("ビジネス的意味: 施策 B は購入率を引き上げている")

# %% [markdown]
# ## 📖 もう一つの考え方：2標本の割合の z 検定
#
# 割合の差は z 検定でも検定できます（2×2 のカイ二乗とほぼ等価で χ² = z²）。
# scipy だけで素朴に書くと次の通り。結論はカイ二乗と一致します。

# %%
n_a = (ab["group"] == "A").sum()
n_b = (ab["group"] == "B").sum()
x_a = ab.loc[ab["group"] == "A", "converted"].sum()
x_b = ab.loc[ab["group"] == "B", "converted"].sum()

p_a, p_b = x_a / n_a, x_b / n_b
p_pool = (x_a + x_b) / (n_a + n_b)                       # H0 下の共通割合
se_pool = np.sqrt(p_pool * (1 - p_pool) * (1/n_a + 1/n_b))
z = (p_b - p_a) / se_pool
p_z = 2 * (1 - stats.norm.cdf(abs(z)))                   # 両側

print(f"z = {z:.3f},  p = {p_z:.3e}")
print(f"参考: z^2 = {z**2:.3f}  ≈ カイ二乗 {chi2:.3f}（ほぼ一致）")

# %% [markdown]
# ## 🖊 EXERCISE 4（ふつう）：session_seconds の t 検定を自分で
#
# A群・B群の `session_seconds` に対して `scipy.stats.ttest_ind`（Welch, `equal_var=False`）で t 検定し、
# **「帰無仮説 / p値 / 結論（5%で棄却するか）/ ビジネス的な意味」の4点セット**を文章で書いてください。
#
# > 期待される答えのヒント：p は極めて小さい（≈ 7e-15）→ H0 を棄却、B の滞在時間が有意に長い。

# %%
# ここにコードを書く
# a_sec = ...
# b_sec = ...
# t_stat, p_value = ...
# print(...)  # 4点セットを書く
pass

# %% [markdown]
# ## 🖊 EXERCISE 5（ふつう）：converted のクロス集計 → カイ二乗検定
#
# `pd.crosstab` で group×converted のクロス集計を作り、`stats.chi2_contingency` で検定してください。
# 結論を**日本語で**（4点セットで）書きましょう。
#
# > 期待される答えのヒント：p ≈ 0.0001 → H0 棄却、CVR に有意差あり（B が高い）。

# %%
# ここにコードを書く
# ct = pd.crosstab(...)
# chi2, p_value, dof, expected = ...
# print(...)
pass

# %% [markdown]
# ## 📖 7-6. 効果量と実務的有意性
#
# 検定が教えるのは「差が偶然か否か」だけ。**差の大きさ（ビジネスインパクト）** は別問題です。
# サンプルが巨大なら、ごく小さな差でも p は小さくなります。
#
# > **統計的に有意 ≠ ビジネス的に重要。**
#
# CVR の差を実務語に翻訳：**絶対差（ポイント）・リフト（相対%）・売上/件数換算**。

# %%
cvr_a = ab.loc[ab["group"] == "A", "converted"].mean()
cvr_b = ab.loc[ab["group"] == "B", "converted"].mean()
abs_diff = cvr_b - cvr_a
lift = abs_diff / cvr_a

monthly_visits = 100_000  # 仮に月10万訪問とする
extra_buyers = monthly_visits * abs_diff

print(f"CVR  A={cvr_a*100:.2f}%  B={cvr_b*100:.2f}%")
print(f"絶対差: {abs_diff*100:+.2f} ポイント")
print(f"リフト(相対改善率): {lift*100:+.1f}%")
print(f"月10万訪問なら購入が約 {extra_buyers:,.0f} 件/月 の増加に相当")

# %% [markdown]
# ## 🖊 EXERCISE 6（ふつう〜難）：効果量を意思決定者向けに
#
# EXERCISE 2 のリフトに加え、**事業の数字への換算**を1つ計算してください。
# 例：月の訪問数を仮置きして「購入が何件増えるか」、あるいは平均客単価を仮定して「売上が何円増えるか」。
#
# > 期待される答えのヒント：自分で置いた仮定（訪問数・客単価）を明記し、件数 or 金額で語ること。
# > 「有意（p値）」と「大きさ（リフト・件数）」は必ずセットで。

# %%
# ここにコードを書く
# monthly_visits = ...
# aov = ...  # 平均客単価（円）。仮置きでよい
# extra_buyers = ...
# extra_revenue = ...
pass

# %% [markdown]
# ## 📖 7-7. よくある落とし穴（A/Bテスト）
#
# - **覗き見(peeking)**：途中で何度も見て有意になった瞬間に止める → 第一種の誤りが激増。事前に期間・サンプル数を決める。
# - **p値ハッキング**：有意になった指標/セグメントだけ報告する → NG。
# - **多重比較**：たくさん検定すればどれかは偶然 p<0.05（20回で平均1回）→ 補正 or 指標を絞る。
# - **サンプル不足**：n が小さいと差を検出できない（検出力不足＝第二種の誤り）。
# - **「有意でない＝差がない」ではない**：p≥0.05 は「差があるとは言えなかった」だけ。
#
# > 💡 テスト開始**前**に「仮説・主要指標・期間・必要サンプル数・判断基準」を書き出す。後出し解釈を封じる。

# %% [markdown]
# ## 🖊 EXERCISE 7（難）：意思決定者への報告文を書く
#
# ここまでの結果（CVR の差・リフト・カイ二乗の p値・滞在時間の t 検定）をもとに、
# **結論ファースト**で意思決定者向けの報告文を書いてください（コメント or print の文字列で）。
#
# 型：**【結論】→【根拠】→【示唆】→【提案】**。
# 「p=0.0001」ではなく **「偶然ではほぼ起きない差」**、効果は **件数/金額** で語ること。
#
# > 期待される答えのヒント：結論=「B は CVR を相対+35%改善、偶然では説明しにくい」。
# > 提案=「B を全面展開し、新奇性効果でないか展開後もモニタリング」。

# %%
# ここに報告文を書く（複数行文字列でOK）
# report = """
# 【結論】 ...
# 【根拠】 ...
# 【示唆】 ...
# 【提案】 ...
# """
# print(report)
pass

# %% [markdown]
# ## 🖊 EXERCISE 8（難・発展）：覗き見(peeking)の危険をシミュレーションで実感
#
# **A と B にまったく差がない**状況（H0 が真）を乱数で作り、
# 「データが増えるたびに検定して、一度でも p<0.05 になったら有意と宣言する」方式が、
# どれくらいの割合で**誤って有意**（第一種の誤り）になるか調べてください。
#
# ヒント：
# - 同じ真の割合（例 5%）で A・B を生成（＝本当は差なし）。
# - 100人ずつ増やしながら何度も検定し、途中で一度でも p<0.05 になった試行を数える。
# - これを多数回繰り返し、その割合を出す。本来 5% のはずが、覗き見だと大きく上回る。
#
# > 期待される答えのヒント：覗き見ありの「偽陽性率」は 5% を大きく超える（15〜25%程度になりうる）。

# %%
# ここにコードを書く
# rng = np.random.default_rng(0)
# true_p = 0.05
# ... 覗き見ありの偽陽性率を推定 ...
pass

# %% [markdown]
# ## ✅ 解答例
#
# 以下は実データ（`data/ab_test.csv`）で実際に動く解答例です。

# %%
# --- 解答1：群ごとのコンバージョン率 ---
cvr = ab.groupby("group")["converted"].mean()
print((cvr * 100).round(2))  # A ≈ 4.42%, B ≈ 5.98%

# %%
# --- 解答2：差とリフト ---
cvr_a = ab.loc[ab["group"] == "A", "converted"].mean()
cvr_b = ab.loc[ab["group"] == "B", "converted"].mean()
abs_diff = cvr_b - cvr_a
lift = abs_diff / cvr_a
print(f"絶対差: {abs_diff*100:+.2f} ポイント")
print(f"リフト(相対改善率): {lift*100:+.1f}%")

# %%
# --- 解答3：CVR の 95% 信頼区間（割合の信頼区間）---
def prop_ci(buyers, n, z=1.96):
    p = buyers / n
    se = np.sqrt(p * (1 - p) / n)
    return p, (p - z*se, p + z*se)

for g in ["A", "B"]:
    sub = ab[ab["group"] == g]
    p, (lo, hi) = prop_ci(sub["converted"].sum(), len(sub))
    print(f"{g}群 CVR {p*100:5.2f}%  95%CI [{lo*100:5.2f}%, {hi*100:5.2f}%]")
# 2つの区間が重ならない → 有意差ありと整合

# %%
# --- 解答4：session_seconds の t 検定（Welch）---
a_sec = ab.loc[ab["group"] == "A", "session_seconds"]
b_sec = ab.loc[ab["group"] == "B", "session_seconds"]
t_stat, p_value = stats.ttest_ind(a_sec, b_sec, equal_var=False)
print(f"A平均 {a_sec.mean():.2f}s / B平均 {b_sec.mean():.2f}s,  t={t_stat:.3f}, p={p_value:.3e}")
print("H0: A=B の母平均 / p<0.05 で棄却 → 滞在時間に有意差あり（B が長い）")
print("ビジネス的意味: B は関与度を高めている可能性")

# %%
# --- 解答5：converted のカイ二乗検定 ---
ct = pd.crosstab(ab["group"], ab["converted"])
chi2, p_value, dof, expected = stats.chi2_contingency(ct)
print(ct)
print(f"chi2={chi2:.3f}, dof={dof}, p={p_value:.3e}")
print("H0: group と converted は独立（CVR は群によらず同じ）")
print("結論: p<0.05 で棄却 → CVR に有意差あり（B が高い）")
print("ビジネス的意味: 施策 B は購入率を引き上げている")

# %%
# --- 解答6：効果量の事業換算 ---
monthly_visits = 100_000   # 仮定：月10万訪問
aov = 4_000                # 仮定：平均客単価 4,000 円
extra_buyers = monthly_visits * abs_diff
extra_revenue = extra_buyers * aov
print(f"リフト: {lift*100:+.1f}%")
print(f"仮定: 月{monthly_visits:,}訪問・客単価{aov:,}円")
print(f"→ 購入 約 {extra_buyers:,.0f} 件/月 増、売上 約 {extra_revenue:,.0f} 円/月 増の見込み")
print("※ 有意性(p値)と効果量(件数・金額)はセットで報告する")

# %%
# --- 解答7：意思決定者への報告文（結論ファースト）---
report = f"""
【結論】 新施策 B は CVR を {cvr_a*100:.1f}% → {cvr_b*100:.1f}%（相対 {lift*100:+.0f}%）に改善。
        偶然ではほぼ説明できない差です（カイ二乗検定で有意, p≈{p_value:.4f}）。
【根拠】 A 6,200人 / B 6,150人 の A/B テスト。滞在時間も B が有意に長い（t検定）。
        CVR の95%信頼区間も A と B で重ならない。
【示唆】 B は購入・滞在の両面で効いている。月10万訪問なら購入が約{100_000*abs_diff:,.0f}件/月の増加に相当。
【提案】 B を全面展開。展開後2週間で同等のリフトが続くか（新奇性効果でないか）を継続モニタリング。
"""
print(report)

# %%
# --- 解答8：覗き見(peeking)の偽陽性率シミュレーション ---
rng = np.random.default_rng(0)
true_p = 0.05          # A も B も本当は同じ CVR（＝差なし。H0 が真）
n_trials = 300         # 試行回数（速度優先でやや少なめ）
steps = range(200, 4001, 200)   # 200人ずつ増やしてのぞき見

false_pos_peeking = 0  # 途中で一度でも p<0.05 になった試行
false_pos_final = 0    # 最後の1回だけで判定した場合
for _ in range(n_trials):
    a_all = rng.random(4000) < true_p
    b_all = rng.random(4000) < true_p
    flagged = False
    last_p = 1.0
    for nstep in steps:
        a, b = a_all[:nstep], b_all[:nstep]
        ct = np.array([[(~a).sum(), a.sum()], [(~b).sum(), b.sum()]])
        # 度数が0だと検定できないのでスキップ
        if (ct.sum(axis=0) == 0).any() or (ct.sum(axis=1) == 0).any():
            continue
        _, p, _, _ = stats.chi2_contingency(ct)
        last_p = p
        if p < 0.05:
            flagged = True
    if flagged:
        false_pos_peeking += 1
    if last_p < 0.05:
        false_pos_final += 1

print(f"本当は差がない（H0真）のに……")
print(f"覗き見あり（途中で一度でも有意なら宣言）の偽陽性率: {false_pos_peeking/n_trials*100:.1f}%")
print(f"最後の1回だけで判定した偽陽性率              : {false_pos_final/n_trials*100:.1f}%（≈5%が正常）")
print("→ 覗き見は第一種の誤りを大きく膨らませる。事前に期間・サンプル数を決めて最後に1回だけ判定する。")
