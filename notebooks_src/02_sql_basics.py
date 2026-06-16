# %% [markdown]
# # 02. SQL 基礎
#
# 🎯 **このモジュールのゴール**：SQL でデータベースから必要なデータを「正しく」取り出せるようになる。
# SELECT の基本から、絞り込み・並べ替え・集計・結合、そして中級のウィンドウ関数まで、
# Sora Mart の実データ（`sora_mart.db`）で段階的に手を動かします。
#
# **前提**：[01. アナリストの思考法]。分析の5ステップのうち、本章は「③取得・加工」を担います。
#
# **分析規約（厳守）**：売上は `order_items.quantity × unit_price` の合計。
# 注文（orders）に紐付けて `status='completed'` のみを売上とする（cancelled / returned は売上に含めない）。

# %%
# === セットアップ（最初に必ず実行）===
import os
import numpy as np
import pandas as pd
import sqlite3

def find_data_dir():
    for base in [".", "..", "../..", os.path.join("..", "data-analyst-course")]:
        cand = os.path.join(base, "data")
        if os.path.exists(os.path.join(cand, "customers.csv")):
            return cand
    raise FileNotFoundError("data フォルダが見つかりません。python scripts/generate_data.py を実行してください。")

DATA = find_data_dir()
print("データ:", os.path.abspath(DATA))

conn = sqlite3.connect(os.path.join(DATA, "sora_mart.db"))

def q(sql):
    """SQLを実行して DataFrame で返すヘルパー。"""
    return pd.read_sql(sql, conn)

print("SQLite バージョン:", sqlite3.sqlite_version)

# %% [markdown]
# ## 📖 SQL は「集合に対する操作」
#
# プログラミングのループ（1件ずつ処理）と違い、SQL は **表（行の集合）まるごと** に対して
# 「こういう条件で、こう集めて、こう並べて」と宣言する言語です。
# 「どう処理するか」ではなく「何が欲しいか（結果の形）」を書く、と覚えましょう。
#
# 使うテーブルは4つ：
#
# | テーブル | 1行の意味 | 主なカラム |
# |---|---|---|
# | `customers` | 顧客1人 | customer_id, age, prefecture, acquisition_channel |
# | `products` | 商品1つ | product_id, product_name, category, price, cost |
# | `orders` | 注文1件 | order_id, customer_id, order_date, status |
# | `order_items` | 注文明細1行 | order_id, product_id, quantity, unit_price |

# %%
# テーブル一覧を確認
print(q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))

# %% [markdown]
# ## 📖 2-1. SELECT / FROM / LIMIT / DISTINCT ── まず中身を見る
#
# - `SELECT` … 取り出す列（`*` は全列）／ `FROM` … どのテーブルから
# - `LIMIT n` … 先頭 n 行だけ（いきなり全件見ない安全装置）
# - `DISTINCT` … 重複を除く（値の種類を把握する）

# %%
# ▶️ 例：先頭5行 / 必要な列だけ / 値の種類
print("--- customers 先頭5行 ---")
print(q("SELECT * FROM customers LIMIT 5"))

print("\n--- 必要な列だけ ---")
print(q("SELECT customer_id, age, prefecture FROM customers LIMIT 5"))

print("\n--- 商品カテゴリの種類 ---")
print(q("SELECT DISTINCT category FROM products"))

# %% [markdown]
# ## 📖 2-2. WHERE ── 行を絞り込む
#
# | 書き方 | 意味 |
# |---|---|
# | `=` `<>` `<` `>` `<=` `>=` | 比較（不等号は `<>`） |
# | `AND` / `OR` | かつ / または（混在時は括弧で明確に） |
# | `IN (...)` | リストのどれか |
# | `BETWEEN a AND b` | a 以上 b 以下（両端含む） |
# | `LIKE 'A%'` | 「A」で始まる（`%`=任意長, `_`=1文字） |
#
# 💡 NULL は `= NULL` ではなく `IS NULL` で判定する。

# %%
# ▶️ 例：いろいろな絞り込み
print("30歳以上の女性 件数:", q(
    "SELECT COUNT(*) AS n FROM customers WHERE age >= 30 AND gender = '女性'"
).iloc[0, 0])

print("\n--- 東京都・大阪府・愛知県の顧客（IN）先頭5件 ---")
print(q("SELECT customer_id, prefecture, age FROM customers "
        "WHERE prefecture IN ('東京都','大阪府','愛知県') LIMIT 5"))

print("\n--- 20代（BETWEEN）の人数 ---")
print(q("SELECT COUNT(*) AS n FROM customers WHERE age BETWEEN 20 AND 29").iloc[0, 0])

print("\n--- 商品名が「キッチン」で始まる（LIKE）---")
print(q("SELECT product_name FROM products WHERE product_name LIKE 'キッチン%' LIMIT 5"))

# %% [markdown]
# ## 🖊 EXERCISE
#
# 易しい問題から順に取り組みます。`q("SQL文")` で実行できます。
# 各問は下のスケルトンセルに SQL を書いて確かめましょう（末尾に解答例あり）。
#
# - **問1**：`products` から「`category` ごとの商品数」を、商品数の多い順に並べて表示する。
#   ヒント：`GROUP BY category` と `COUNT(*)`、`ORDER BY ... DESC`。
# - **問2**：`customers` から「都道府県別の顧客数 TOP5」を表示する。
#   ヒント：`GROUP BY prefecture` → `ORDER BY 件数 DESC` → `LIMIT 5`。
# - **問3**：月次売上の推移（completed のみ）を、月の昇順で表示する。
#   ヒント：`strftime('%Y-%m', o.order_date)` で月を作り `GROUP BY`。売上は `SUM(oi.quantity*oi.unit_price)`。
# - **問4**：カテゴリ別売上ランキング（completed のみ）。売上の多い順。
#   ヒント：orders × order_items × products を JOIN、`WHERE o.status='completed'`。
# - **問5**：顧客別の購入金額 TOP10（completed のみ）。customer_id と合計金額。
#   ヒント：customers × orders × order_items を JOIN、`GROUP BY c.customer_id` → `LIMIT 10`。
# - **問6**：獲得経路（acquisition_channel）ごとの平均客単価（= 売上 ÷ 注文数, completed のみ）。
#   ヒント：`SUM(oi.quantity*oi.unit_price) * 1.0 / COUNT(DISTINCT o.order_id)`。整数割り算を避けるため `*1.0`。
# - **問7**：CASE で年代別（20代/30代…）の顧客数を出す。
#   ヒント：`CASE WHEN age<20 THEN '10代以下' WHEN age<30 THEN '20代' ... END` を GROUP BY。
# - **問8**（中級）：ウィンドウ関数でカテゴリ内の商品売上ランキングを作り、各カテゴリのTOP1を抽出する。
#   ヒント：FROM内サブクエリで商品別売上を作り、`ROW_NUMBER() OVER (PARTITION BY category ORDER BY 売上 DESC)`。

# %%
# 問1：カテゴリ別の商品数
# ヒント：SELECT category, COUNT(*) ... GROUP BY category ORDER BY ... DESC
# ここにコードを書く
pass

# %%
# 問2：都道府県別の顧客数 TOP5
# ヒント：GROUP BY prefecture → ORDER BY 件数 DESC → LIMIT 5
# ここにコードを書く
pass

# %%
# 問3：月次売上の推移（completed のみ）
# ヒント：strftime('%Y-%m', o.order_date) を GROUP BY、SUM(oi.quantity*oi.unit_price)
# ここにコードを書く
pass

# %%
# 問4：カテゴリ別売上ランキング（completed のみ）
# ヒント：orders × order_items × products を JOIN、WHERE o.status='completed'
# ここにコードを書く
pass

# %%
# 問5：顧客別の購入金額 TOP10（completed のみ）
# ヒント：customers × orders × order_items を JOIN、GROUP BY c.customer_id → LIMIT 10
# ここにコードを書く
pass

# %%
# 問6：獲得経路ごとの平均客単価（completed のみ）
# ヒント：SUM(oi.quantity*oi.unit_price)*1.0 / COUNT(DISTINCT o.order_id)
# ここにコードを書く
pass

# %%
# 問7：CASE で年代別の顧客数
# ヒント：CASE WHEN age<20 ... END AS 年代 を GROUP BY
# ここにコードを書く
pass

# %%
# 問8（中級）：ウィンドウ関数でカテゴリ内売上ランキング → 各カテゴリTOP1
# ヒント：FROM内サブクエリ + ROW_NUMBER() OVER (PARTITION BY category ORDER BY 売上 DESC)
# ここにコードを書く
pass

# %% [markdown]
# ## 📖 中級トピックの復習（解答前のおさらい）
#
# - **JOIN**：`JOIN ... ON キー一致`。INNER（既定）は一致がある行だけ、LEFT は左を全部残す。
# - **CASE**：`CASE WHEN 条件 THEN 値 ... ELSE ... END`。連続値（年齢）をビン（年代）に。
# - **strftime**：`strftime('%Y-%m', 日付)` で「年-月」。月次集計の定石。
# - **サブクエリ**：WHERE 内（単一値の比較）／ FROM 内（集計の二段重ね）。
# - **ウィンドウ関数**：`関数() OVER (PARTITION BY ... ORDER BY ...)`。行を残したまま順位・累計を添える。
#
# 実行順序を忘れずに：**FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT**。

# %% [markdown]
# ## ✅ 解答例
#
# 以下は実データで動く解答例です。結果から「何が言えるか」も一言ずつ考えてみましょう。

# %%
# --- 解答1：カテゴリ別の商品数 ---
print(q("""
SELECT category, COUNT(*) AS 商品数
FROM products
GROUP BY category
ORDER BY 商品数 DESC
"""))

# %%
# --- 解答2：都道府県別の顧客数 TOP5 ---
print(q("""
SELECT prefecture, COUNT(*) AS 顧客数
FROM customers
GROUP BY prefecture
ORDER BY 顧客数 DESC
LIMIT 5
"""))

# %%
# --- 解答3：月次売上の推移（completed のみ）---
ans3 = q("""
SELECT strftime('%Y-%m', o.order_date) AS 月,
       SUM(oi.quantity * oi.unit_price) AS 売上
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY 月
ORDER BY 月
""")
print(ans3.head(12))
print("... 月数:", len(ans3))

# %%
# --- 解答4：カテゴリ別売上ランキング（completed のみ）---
print(q("""
SELECT p.category, SUM(oi.quantity * oi.unit_price) AS 売上
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products    p  ON oi.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY p.category
ORDER BY 売上 DESC
"""))

# %%
# --- 解答5：顧客別の購入金額 TOP10（completed のみ）---
print(q("""
SELECT c.customer_id, c.prefecture,
       SUM(oi.quantity * oi.unit_price) AS 購入金額
FROM customers c
JOIN orders o       ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY c.customer_id
ORDER BY 購入金額 DESC
LIMIT 10
"""))

# %%
# --- 解答6：獲得経路ごとの平均客単価（completed のみ）---
# 客単価 = 売上 ÷ 注文数。整数割り算を避けるため *1.0 で小数化。
print(q("""
SELECT c.acquisition_channel AS 獲得経路,
       COUNT(DISTINCT o.order_id) AS 注文数,
       ROUND(SUM(oi.quantity * oi.unit_price) * 1.0
             / COUNT(DISTINCT o.order_id), 0) AS 平均客単価
FROM customers c
JOIN orders o       ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY c.acquisition_channel
ORDER BY 平均客単価 DESC
"""))

# %%
# --- 解答7：CASE で年代別の顧客数 ---
print(q("""
SELECT
  CASE
    WHEN age < 20 THEN '10代以下'
    WHEN age < 30 THEN '20代'
    WHEN age < 40 THEN '30代'
    WHEN age < 50 THEN '40代'
    WHEN age < 60 THEN '50代'
    ELSE '60代以上'
  END AS 年代,
  COUNT(*) AS 人数
FROM customers
GROUP BY 年代
ORDER BY 年代
"""))

# %%
# --- 解答8（中級）：ウィンドウ関数でカテゴリ内売上ランキング → 各カテゴリTOP1 ---
# FROM内サブクエリで商品別売上を作り、PARTITION BY category で順位付け。
print(q("""
SELECT category, product_name, 売上, カテゴリ内順位
FROM (
  SELECT p.category, p.product_name,
         SUM(oi.quantity * oi.unit_price) AS 売上,
         ROW_NUMBER() OVER (
           PARTITION BY p.category
           ORDER BY SUM(oi.quantity * oi.unit_price) DESC
         ) AS カテゴリ内順位
  FROM orders o
  JOIN order_items oi ON o.order_id = oi.order_id
  JOIN products    p  ON oi.product_id = p.product_id
  WHERE o.status = 'completed'
  GROUP BY p.product_id
)
WHERE カテゴリ内順位 = 1
ORDER BY 売上 DESC
"""))

# %%
# --- おまけ：SUM() OVER による月次売上の累計（running total）---
print(q("""
SELECT 月, 売上,
       SUM(売上) OVER (ORDER BY 月) AS 累計売上
FROM (
  SELECT strftime('%Y-%m', o.order_date) AS 月,
         SUM(oi.quantity * oi.unit_price) AS 売上
  FROM orders o
  JOIN order_items oi ON o.order_id = oi.order_id
  WHERE o.status = 'completed'
  GROUP BY 月
)
ORDER BY 月
LIMIT 6
"""))

# %% [markdown]
# ## まとめと次へ
#
# - SQL は集合への宣言的操作。実行順序 **FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY** を意識する。
# - 売上は必ず `quantity × unit_price` の SUM、`status='completed'` のみ（本講座の規約）。
# - 絞り込みは `WHERE`（行）と `HAVING`（集計後）を使い分ける。JOIN は INNER と LEFT を目的で選ぶ。
#
# 次は同じ集計を **pandas** で。SQL の GROUP BY が pandas の `groupby` にどう対応するかを対比すると理解が深まります。
#
# 👉 03. pandas 基礎 へ
