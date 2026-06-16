"""
データアナリスト養成講座 — サンプルデータ生成スクリプト

架空のオンライン雑貨EC「Sora Mart（ソラマート）」の取引データを生成します。
- customers.csv     顧客マスタ
- products.csv      商品マスタ
- orders.csv        注文ヘッダ
- order_items.csv   注文明細
- customers_raw.csv 「汚い」顧客データ（前処理演習用）
- ab_test.csv       A/Bテスト結果（統計演習用）
- sora_mart.db      上記をまとめたSQLite DB（SQL演習用）

すべて乱数シードを固定しているため、何度実行しても同じデータになります。
実在の人物・企業とは一切関係ありません。

使い方:
    python scripts/generate_data.py
"""

import os
import sqlite3
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# 設定
# ----------------------------------------------------------------------
SEED = 42
rng = np.random.default_rng(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

N_CUSTOMERS = 2000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)
N_DAYS = (END_DATE - START_DATE).days + 1

PREFECTURES = [
    "北海道", "宮城県", "東京都", "神奈川県", "埼玉県", "千葉県",
    "愛知県", "大阪府", "京都府", "兵庫県", "広島県", "福岡県",
]
# 都市部ほど顧客が多い、という重み
PREF_WEIGHTS = np.array([5, 3, 25, 12, 8, 7, 9, 14, 4, 6, 3, 8], dtype=float)
PREF_WEIGHTS /= PREF_WEIGHTS.sum()

CHANNELS = ["検索広告", "SNS広告", "オーガニック検索", "メルマガ", "友人紹介"]
CHANNEL_WEIGHTS = [0.30, 0.25, 0.25, 0.12, 0.08]

GENDERS = ["女性", "男性", "回答なし"]
GENDER_WEIGHTS = [0.55, 0.40, 0.05]

# 商品カテゴリと価格帯（円）
CATEGORIES = {
    "キッチン":   (800, 6000),
    "インテリア": (1500, 20000),
    "文具":       (200, 3000),
    "アパレル":   (1500, 12000),
    "食品":       (500, 4000),
    "美容":       (900, 8000),
}

PAYMENT_METHODS = ["クレジットカード", "代金引換", "コンビニ払い", "電子マネー"]
PAYMENT_WEIGHTS = [0.58, 0.12, 0.18, 0.12]

LAST_NAMES = [
    "佐藤", "鈴木", "高橋", "田中", "伊藤", "渡辺", "山本", "中村",
    "小林", "加藤", "吉田", "山田", "佐々木", "山口", "松本", "井上",
]
FIRST_NAMES = [
    "陽菜", "蓮", "結衣", "大翔", "葵", "悠真", "凛", "湊",
    "莉子", "樹", "美咲", "颯太", "さくら", "陽斗", "芽依", "悠人",
]


# ----------------------------------------------------------------------
# 1. 顧客マスタ
# ----------------------------------------------------------------------
def make_customers():
    customer_ids = np.arange(1, N_CUSTOMERS + 1)

    # 登録日：期間内にゆるやかに増加（後半ほど登録が多い）
    reg_offsets = (rng.beta(2.0, 1.5, N_CUSTOMERS) * (N_DAYS - 1)).astype(int)
    reg_dates = [START_DATE + timedelta(days=int(o)) for o in reg_offsets]

    ages = np.clip(rng.normal(38, 12, N_CUSTOMERS).round(), 18, 80).astype(int)
    genders = rng.choice(GENDERS, N_CUSTOMERS, p=GENDER_WEIGHTS)
    prefs = rng.choice(PREFECTURES, N_CUSTOMERS, p=PREF_WEIGHTS)
    channels = rng.choice(CHANNELS, N_CUSTOMERS, p=CHANNEL_WEIGHTS)

    last = rng.choice(LAST_NAMES, N_CUSTOMERS)
    first = rng.choice(FIRST_NAMES, N_CUSTOMERS)
    names = [f"{l} {f}" for l, f in zip(last, first)]

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "name": names,
        "gender": genders,
        "age": ages,
        "prefecture": prefs,
        "registration_date": [d.strftime("%Y-%m-%d") for d in reg_dates],
        "acquisition_channel": channels,
    })
    return df, reg_dates


# ----------------------------------------------------------------------
# 2. 商品マスタ
# ----------------------------------------------------------------------
def make_products():
    rows = []
    pid = 1
    for cat, (low, high) in CATEGORIES.items():
        n = rng.integers(10, 18)  # カテゴリごとの商品数
        for _ in range(n):
            price = int(rng.uniform(low, high) // 100 * 100)  # 100円単位
            cost_ratio = rng.uniform(0.45, 0.7)
            cost = int(price * cost_ratio // 10 * 10)
            rows.append({
                "product_id": pid,
                "product_name": f"{cat}商品{pid:03d}",
                "category": cat,
                "price": price,
                "cost": cost,
            })
            pid += 1
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 3. 注文ヘッダ + 明細
# ----------------------------------------------------------------------
def make_orders(customers, reg_dates, products):
    # 顧客ごとの「購入しやすさ」をガンマ分布で設定（ヘビーユーザーが少数いる）
    propensity = rng.gamma(shape=1.6, scale=1.0, size=N_CUSTOMERS)

    order_rows = []
    item_rows = []
    order_id = 1
    order_item_id = 1

    product_ids = products["product_id"].to_numpy()
    product_prices = products.set_index("product_id")["price"].to_dict()

    for i in range(N_CUSTOMERS):
        cust_id = int(customers.loc[i, "customer_id"])
        reg = reg_dates[i]
        # 登録から期末までの日数
        active_days = (END_DATE - reg).days
        if active_days <= 0:
            continue

        # 期待注文数：在籍日数と購入傾向に比例
        expected = propensity[i] * active_days / 180.0
        n_orders = rng.poisson(expected)

        for _ in range(n_orders):
            # 注文日：登録日以降のランダムな日
            day_offset = int(rng.integers(0, active_days + 1))
            odate = reg + timedelta(days=day_offset)

            # 季節性：11-12月（ギフト需要）を少し増やすため再サンプリング
            if odate.month in (11, 12) and rng.random() < 0.0:
                pass  # （季節性は注文数側で擬似的に表現済み）

            status = rng.choice(
                ["completed", "completed", "completed", "cancelled", "returned"],
                p=[0.80, 0.08, 0.04, 0.05, 0.03],
            )
            payment = rng.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)

            order_rows.append({
                "order_id": order_id,
                "customer_id": cust_id,
                "order_date": odate.strftime("%Y-%m-%d"),
                "status": status,
                "payment_method": payment,
            })

            # 明細：1注文あたり1〜4商品
            n_items = int(rng.integers(1, 5))
            chosen = rng.choice(product_ids, size=n_items, replace=False)
            for prod in chosen:
                qty = int(rng.integers(1, 4))
                unit_price = product_prices[int(prod)]
                item_rows.append({
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "product_id": int(prod),
                    "quantity": qty,
                    "unit_price": unit_price,
                })
                order_item_id += 1
            order_id += 1

    orders = pd.DataFrame(order_rows)
    items = pd.DataFrame(item_rows)
    return orders, items


# ----------------------------------------------------------------------
# 4. 「汚い」顧客データ（前処理演習用）
# ----------------------------------------------------------------------
def make_dirty_customers(customers):
    """customers をコピーして、現実によくある汚れを混ぜる。"""
    df = customers.copy()
    df = df.head(300).copy()  # 演習用に小さめ

    # 列名を実務でありがちな英語混在に
    df = df.rename(columns={
        "acquisition_channel": "channel",
    })

    # age に欠損と異常値を混ぜる
    df["age"] = df["age"].astype(float)
    miss_idx = rng.choice(df.index, size=20, replace=False)
    df.loc[miss_idx, "age"] = np.nan
    bad_idx = rng.choice(df.index, size=5, replace=False)
    df.loc[bad_idx, "age"] = rng.choice([-1, 0, 999, 200], size=5)

    # gender の表記ゆれ
    gender_map_idx = rng.choice(df.index, size=60, replace=False)
    swap = {"女性": "F", "男性": "M", "回答なし": ""}
    df.loc[gender_map_idx, "gender"] = df.loc[gender_map_idx, "gender"].map(swap)

    # prefecture に余分な空白・全角半角ゆれ
    sp_idx = rng.choice(df.index, size=40, replace=False)
    df.loc[sp_idx, "prefecture"] = " " + df.loc[sp_idx, "prefecture"] + " "

    # registration_date のフォーマットゆれ
    fmt_idx = rng.choice(df.index, size=50, replace=False)
    df.loc[fmt_idx, "registration_date"] = (
        pd.to_datetime(df.loc[fmt_idx, "registration_date"]).dt.strftime("%Y/%m/%d")
    )

    # 重複行を追加（同じ顧客が2回登録されている想定）
    dup = df.sample(15, random_state=SEED)
    df = pd.concat([df, dup], ignore_index=True)

    # name に前後空白
    nm_idx = rng.choice(df.index, size=30, replace=False)
    df.loc[nm_idx, "name"] = df.loc[nm_idx, "name"] + "　"

    return df


# ----------------------------------------------------------------------
# 5. A/Bテストデータ（統計演習用）
# ----------------------------------------------------------------------
def make_ab_test():
    """
    ECサイトの商品ページボタン色を変える A/Bテスト。
    - group A（コントロール）: コンバージョン率 約4.8%
    - group B（テスト）      : コンバージョン率 約5.6%（わずかに改善）
    1ユーザー1行。converted は購入したか(1/0)。
    """
    n_a, n_b = 6200, 6150
    p_a, p_b = 0.048, 0.056

    a = pd.DataFrame({
        "user_id": np.arange(1, n_a + 1),
        "group": "A",
        "converted": rng.binomial(1, p_a, n_a),
        # 滞在時間（秒）: 群でわずかに差
        "session_seconds": np.clip(rng.normal(95, 40, n_a), 5, None).round(1),
    })
    b = pd.DataFrame({
        "user_id": np.arange(n_a + 1, n_a + n_b + 1),
        "group": "B",
        "converted": rng.binomial(1, p_b, n_b),
        "session_seconds": np.clip(rng.normal(101, 42, n_b), 5, None).round(1),
    })
    df = pd.concat([a, b], ignore_index=True)
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    return df


# ----------------------------------------------------------------------
# メイン
# ----------------------------------------------------------------------
def main():
    print("サンプルデータを生成します ...")

    customers, reg_dates = make_customers()
    products = make_products()
    orders, items = make_orders(customers, reg_dates, products)
    dirty = make_dirty_customers(customers)
    ab = make_ab_test()

    # CSV出力
    customers.to_csv(os.path.join(DATA_DIR, "customers.csv"), index=False, encoding="utf-8-sig")
    products.to_csv(os.path.join(DATA_DIR, "products.csv"), index=False, encoding="utf-8-sig")
    orders.to_csv(os.path.join(DATA_DIR, "orders.csv"), index=False, encoding="utf-8-sig")
    items.to_csv(os.path.join(DATA_DIR, "order_items.csv"), index=False, encoding="utf-8-sig")
    dirty.to_csv(os.path.join(DATA_DIR, "customers_raw.csv"), index=False, encoding="utf-8-sig")
    ab.to_csv(os.path.join(DATA_DIR, "ab_test.csv"), index=False, encoding="utf-8-sig")

    # SQLite DB
    db_path = os.path.join(DATA_DIR, "sora_mart.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    customers.to_sql("customers", conn, index=False)
    products.to_sql("products", conn, index=False)
    orders.to_sql("orders", conn, index=False)
    items.to_sql("order_items", conn, index=False)
    conn.commit()
    conn.close()

    # サマリ表示
    print("\n=== 生成結果 ===")
    print(f"customers     : {len(customers):>7,} 行")
    print(f"products      : {len(products):>7,} 行")
    print(f"orders        : {len(orders):>7,} 行")
    print(f"order_items   : {len(items):>7,} 行")
    print(f"customers_raw : {len(dirty):>7,} 行（前処理演習用）")
    print(f"ab_test       : {len(ab):>7,} 行（統計演習用）")
    print(f"\n出力先: {DATA_DIR}")
    print("SQLite DB: sora_mart.db (テーブル: customers, products, orders, order_items)")
    print("完了しました。")


if __name__ == "__main__":
    main()
