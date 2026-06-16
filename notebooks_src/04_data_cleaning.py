# %% [markdown]
# # 04. データクレンジング / 前処理
#
# 🎯 **このモジュールのゴール**：わざと汚した顧客データ `customers_raw.csv` を読み込み、
# 汚れを「発見 → 判断して処理 → 検証」の流れで直し、分析に使える
# **「きれいな顧客マスタ」**を完成させる。
#
# **前提**：モジュール02〜03（pandas / SQL でのデータ取得）を一通り触っていること。
# 解説は `docs/04_data_cleaning.md` を参照。
#
# **題材データ `customers_raw.csv` には、次の汚れが意図的に入っています**：
#
# - `age` に欠損(NaN)と異常値（-1, 0, 200, 999 など）
# - `gender` の表記ゆれ（女性 / 男性 / 回答なし のほか F / M / 空 が混在）
# - `prefecture` に前後の余分な空白
# - `registration_date` のフォーマットゆれ（YYYY-MM-DD と YYYY/MM/DD）
# - 完全な重複行（同一顧客が複数回）
# - `name` に末尾の全角スペース
# - 列名が `channel`（取得チャネル）

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

RAW_PATH = os.path.join(DATA, "customers_raw.csv")
raw = pd.read_csv(RAW_PATH)
print("読み込み:", raw.shape, "（行数, 列数）")
raw.head()

# %% [markdown]
# ## 📖 4-1. まず「汚れを発見」する
#
# 加工の前に**観察**します。次の道具で全体像をつかみます。
#
# - `info()`：行数・列・dtype・非欠損数
# - `isna().sum()`：列ごとの欠損数
# - `duplicated().sum()`：完全重複の行数
# - `value_counts(dropna=False)`：カテゴリ列の表記ゆれ・欠損
# - `describe()`：数値列の min/max/平均（異常値の当たりがつく）
#
# **発見せずにいきなり `dropna()` してはいけません。**何件・何を捨てたか分からなくなります。

# %%
# ▶️ 例：5つの道具で汚れを発見する
print("=== info ===")
raw.info()

print("\n=== 欠損数 isna().sum() ===")
print(raw.isna().sum())

print("\n=== 完全重複の行数 duplicated().sum() ===")
print(raw.duplicated().sum())

print("\n=== gender の表記ゆれ value_counts ===")
print(raw["gender"].value_counts(dropna=False))

print("\n=== age の describe（min が -1、max が 999 → 異常値の気配）===")
print(raw["age"].describe())

# %% [markdown]
# ## 📖 4-2. 欠損値の扱い ── 削除 vs 補完
#
# - **削除 `dropna()`**：欠損がごく少数 / その行は使えない場合。**捨てる前に件数を確認**。
# - **補完 `fillna()`**：行は活かしたい場合。数値は**平均より中央値（median）が無難**
#   （平均は外れ値に弱い）。
#
# 補完した値は「推定」であって事実ではない、と意識しておきます。

# %%
# ▶️ 例：dropna と fillna を比べる（age を題材に）
before = len(raw)
dropped = raw.dropna(subset=["age"])
print(f"dropna: {before} → {len(dropped)} 行（{before - len(dropped)} 件が欠損で脱落）")

med = raw["age"].median()
print("age の中央値:", med)
filled = raw["age"].fillna(med)
print("fillna 後の欠損数:", filled.isna().sum(), "（補完で 0 になる）")

# %% [markdown]
# ## 🖊 EXERCISE 1（易）：汚れの棚卸し
#
# `raw` について、次の3つを表示してください。
#
# 1. 列ごとの欠損数（`isna().sum()`）
# 2. 完全重複の行数（`duplicated().sum()`）
# 3. 各列のユニーク値の数（`nunique()`）
#
# 💡 ヒント：`raw.nunique()` で全列のユニーク数が一度に出ます。

# %%
# ここにコードを書く
# 1. 欠損数:
# 2. 重複数:
# 3. ユニーク値数:
pass

# %% [markdown]
# ## 📖 4-3. 重複の除去
#
# 完全に同じ行は `drop_duplicates()` で1件に畳めます。
# 「customer_id だけ重複」を消すなら `subset=["customer_id"]` を指定します。

# %%
# ▶️ 例：完全重複を除去して行数の変化を見る
n0 = len(raw)
no_dup = raw.drop_duplicates()
print(f"完全重複の除去: {n0} → {len(no_dup)} 行（{n0 - len(no_dup)} 件の重複を削除）")

# %% [markdown]
# ## 🖊 EXERCISE 2（易）：重複を除去する
#
# `raw` から完全重複行を除いた DataFrame `df2` を作り、行数の変化を表示してください。
#
# 💡 ヒント：`raw.drop_duplicates()`。除去前後で `len()` を比べる。

# %%
# ここにコードを書く
# df2 = ...
pass

# %% [markdown]
# ## 📖 4-4. 文字列の正規化と表記ゆれの統一
#
# - **前後の空白**：`str.strip()` で除去。
# - **全角空白（`　`, U+3000）**：明示的に置換（`str.replace("　", "")`）。
# - **表記ゆれ**：マッピング辞書で統一。`map()` は辞書に無い値を NaN にするので、
#   最後に `fillna(...)` で受け皿を作っておくと安全。

# %%
# ▶️ 例：prefecture の空白除去と、gender の3カテゴリ統一
tmp = raw.copy()

# 都道府県：前後の半角・全角空白を除去
tmp["prefecture"] = tmp["prefecture"].str.strip().str.replace("　", "", regex=False)

# gender：女性/男性/回答なし の3カテゴリに統一
gender_map = {"女性": "女性", "F": "女性", "男性": "男性", "M": "男性",
              "回答なし": "回答なし", "": "回答なし"}
tmp["gender"] = tmp["gender"].str.strip().map(gender_map).fillna("回答なし")

print("gender 統一後:")
print(tmp["gender"].value_counts())
print("\nprefecture 例（空白が消えている）:", tmp["prefecture"].head(3).tolist())

# %% [markdown]
# ## 🖊 EXERCISE 3（中）：gender を3カテゴリに統一する
#
# `raw["gender"]` を **女性 / 男性 / 回答なし** の3つだけに統一した Series を作り、
# `value_counts()` で「3カテゴリだけ」になったことを確認してください。
#
# 💡 ヒント：マッピング辞書 + `.map(...)` + `.fillna("回答なし")`。F→女性, M→男性。

# %%
# ここにコードを書く
# gender_map = {...}
# gender_clean = ...
pass

# %% [markdown]
# ## 🖊 EXERCISE 4（中）：prefecture と name の空白を除去する
#
# `raw` の `prefecture` と `name` から、**前後の半角空白と全角空白**を除いた列を作ってください。
# 除去前に「空白を含む行が何件あったか」を数えると、効果が確認できます。
#
# 💡 ヒント：`str.strip()` の後に `str.replace("　", "", regex=False)`。
# 元の値と `strip` 後の値が違う行数 = 汚れていた行数。

# %%
# ここにコードを書く
# pref_clean = ...
# name_clean = ...
pass

# %% [markdown]
# ## 📖 4-5. 異常値の検出と処理（age）
#
# `age` には -1, 0, 200, 999 のような**ありえない値**が混ざっています。
# ここでは **0〜120 の範囲外を欠損(NaN)に置き換え → 中央値で補完**します。
# 「消す」のではなく「いったん欠損化して補完に回す」と、欠損処理に流れを一本化できます。
#
# 📎 IQR法（軽い紹介）：`IQR = Q3 - Q1` から `Q1-1.5IQR 未満 / Q3+1.5IQR 超`を外れ値とみなす方法。
# ただし機械的なので、消す前に「本当に異常か」をドメインで確認します。

# %%
# ▶️ 例：範囲外を欠損化 → 中央値補完
tmp = raw.copy()
print("処理前の age describe:")
print(tmp["age"].describe()[["min", "max"]])

mask = (tmp["age"] < 0) | (tmp["age"] > 120)
print("\n範囲外（<0 or >120）の件数:", int(mask.sum()))
tmp.loc[mask, "age"] = np.nan                       # ありえない値を欠損化
tmp["age"] = tmp["age"].fillna(tmp["age"].median()) # 中央値で補完

print("\n処理後の age describe（min/max が常識範囲に）:")
print(tmp["age"].describe()[["min", "max", "mean"]])
print("欠損数:", tmp["age"].isna().sum())

# IQR法の参考（外れ値の境界を計算するだけ）
q1, q3 = raw["age"].quantile([0.25, 0.75])
iqr = q3 - q1
print(f"\n[参考] IQR法の境界: 下限={q1 - 1.5 * iqr:.1f}, 上限={q3 + 1.5 * iqr:.1f}")

# %% [markdown]
# ## 🖊 EXERCISE 5（中）：age の異常値を欠損化して中央値で補完する
#
# `raw["age"]` について、**0未満 または 120超** の値を NaN にしてから、
# **中央値**で補完した Series `age_clean` を作ってください。補完後に欠損が0件か確認します。
#
# 💡 ヒント：`s = raw["age"].copy()` → `s[(s<0)|(s>120)] = np.nan` → `s.fillna(s.median())`。

# %%
# ここにコードを書く
# age_clean = ...
pass

# %% [markdown]
# ## 📖 4-6. 型変換 ── 日付フォーマットの混在
#
# `registration_date` は `2023-12-24`（ハイフン）と `2024/06/04`（スラッシュ）が混在。
# datetime 型に統一します。pandas 2系の `format="mixed"` でパースでき、
# `errors="coerce"`（失敗を NaT にする）を併用すると堅牢です。
# 変換後は NaT の件数を必ず確認します。

# %%
# ▶️ 例：日付を datetime に統一する
dt = pd.to_datetime(raw["registration_date"], format="mixed", errors="coerce")
print("dtype:", dt.dtype)
print("変換失敗（NaT）の件数:", dt.isna().sum())
print("最小日:", dt.min(), " 最大日:", dt.max())
print("例:", dt.head(4).tolist())

# %% [markdown]
# ## 🖊 EXERCISE 6（中）：registration_date を datetime に統一する
#
# `raw["registration_date"]` を datetime 型に変換した Series `date_clean` を作り、
# 変換できなかった（NaT になった）件数を表示してください。
#
# 💡 ヒント：`pd.to_datetime(..., format="mixed", errors="coerce")`。`.isna().sum()` で NaT を数える。

# %%
# ここにコードを書く
# date_clean = ...
pass

# %% [markdown]
# ## 🖊 EXERCISE 7（難）：きれいな顧客マスタを作る（総合）
#
# ここまでの処理を全部つなげて、**きれいな顧客マスタ `customers_clean`** を作ってください。
# 手順（順番も大事）：
#
# 1. `raw` をコピー
# 2. 完全重複を除去
# 3. `name` / `prefecture` の前後空白（半角・全角）を除去
# 4. `gender` を3カテゴリに統一
# 5. `age` の範囲外（<0 / >120）を NaN 化 → 中央値で補完
# 6. `registration_date` を datetime に統一
#
# 最後に **行数の変化（raw → clean）** と、検証（`isna().sum()`, `duplicated().sum()`,
# `gender` の `value_counts`, `age` の `describe`）を表示してください。
#
# 💡 ヒント：各ステップは上の例セルのコードを組み合わせるだけ。`before = len(raw)` を控えておく。

# %%
# ここにコードを書く
# customers_clean = raw.copy()
# ... 2〜6 を順に適用 ...
# 検証を print する
pass

# %% [markdown]
# ## ✅ 解答例
#
# 以下は実データで動作する解答例です。

# %%
# --- 解答1：汚れの棚卸し ---
print("1. 欠損数:")
print(raw.isna().sum())
print("\n2. 重複数:", raw.duplicated().sum())
print("\n3. 各列のユニーク値数:")
print(raw.nunique())

# %%
# --- 解答2：重複を除去する ---
df2 = raw.drop_duplicates()
print(f"重複除去: {len(raw)} → {len(df2)} 行（{len(raw) - len(df2)} 件削除）")

# %%
# --- 解答3：gender を3カテゴリに統一する ---
gender_map = {"女性": "女性", "F": "女性", "男性": "男性", "M": "男性",
              "回答なし": "回答なし", "": "回答なし"}
gender_clean = raw["gender"].str.strip().map(gender_map).fillna("回答なし")
print(gender_clean.value_counts())
assert set(gender_clean.unique()) <= {"女性", "男性", "回答なし"}
print("→ 3カテゴリに統一できた")

# %%
# --- 解答4：prefecture と name の空白を除去する ---
def strip_all(s):
    return s.str.strip().str.replace("　", "", regex=False)

dirty_pref = (raw["prefecture"] != strip_all(raw["prefecture"])).sum()
dirty_name = (raw["name"] != strip_all(raw["name"])).sum()
pref_clean = strip_all(raw["prefecture"])
name_clean = strip_all(raw["name"])
print(f"prefecture: 空白を含んでいた行 = {dirty_pref} 件 → 除去済み")
print(f"name      : 空白を含んでいた行 = {dirty_name} 件 → 除去済み")

# %%
# --- 解答5：age の異常値を欠損化して中央値で補完する ---
age_clean = raw["age"].copy()
n_outlier = ((age_clean < 0) | (age_clean > 120)).sum()
age_clean[(age_clean < 0) | (age_clean > 120)] = np.nan
age_clean = age_clean.fillna(age_clean.median())
print(f"範囲外の異常値: {int(n_outlier)} 件を欠損化 → 中央値で補完")
print("補完後の欠損数:", age_clean.isna().sum())
print(age_clean.describe()[["min", "max", "mean"]])

# %%
# --- 解答6：registration_date を datetime に統一する ---
date_clean = pd.to_datetime(raw["registration_date"], format="mixed", errors="coerce")
print("dtype:", date_clean.dtype)
print("変換失敗（NaT）:", date_clean.isna().sum(), "件")
print("期間:", date_clean.min().date(), "〜", date_clean.max().date())

# %%
# --- 解答7：きれいな顧客マスタを作る（総合）---
before = len(raw)
customers_clean = raw.copy()

# 2. 完全重複を除去
customers_clean = customers_clean.drop_duplicates()

# 3. name / prefecture の空白除去（半角・全角）
for col in ["name", "prefecture"]:
    customers_clean[col] = (customers_clean[col].str.strip()
                            .str.replace("　", "", regex=False))

# 4. gender を3カテゴリに統一
customers_clean["gender"] = (customers_clean["gender"].str.strip()
                             .map(gender_map).fillna("回答なし"))

# 5. age の範囲外を NaN 化 → 中央値補完
m = (customers_clean["age"] < 0) | (customers_clean["age"] > 120)
customers_clean.loc[m, "age"] = np.nan
customers_clean["age"] = customers_clean["age"].fillna(customers_clean["age"].median())

# 6. registration_date を datetime に統一
customers_clean["registration_date"] = pd.to_datetime(
    customers_clean["registration_date"], format="mixed", errors="coerce")

# 仕上げ：正規化で「空白違い」が揃った結果、新たに完全一致になった行があるので
#         もう一度だけ重複を除去する（正規化 → 再dedup は実務でよくある順序）
n_after_norm = len(customers_clean)
customers_clean = customers_clean.drop_duplicates()
print(f"正規化後に再度判明した重複: {n_after_norm - len(customers_clean)} 件を追加で除去")

# --- 検証 ---
print(f"行数の変化: {before} → {len(customers_clean)} 行 "
      f"（{before - len(customers_clean)} 件減：重複と正規化で揃った重複）")
print("\n欠損数（すべて 0 が理想）:")
print(customers_clean.isna().sum())
print("\n重複数:", customers_clean.duplicated().sum())
print("\ngender（3カテゴリ）:")
print(customers_clean["gender"].value_counts())
print("\nage の describe（min/max が常識範囲）:")
print(customers_clean["age"].describe()[["min", "max", "mean"]])
print("\nregistration_date dtype:", customers_clean["registration_date"].dtype)
customers_clean.head()
