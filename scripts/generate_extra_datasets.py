"""
データアナリスト養成講座 — 発展用サンプルデータ生成スクリプト

メイン教材の架空EC「Sora Mart」だけだと「結合・集計」中心に偏るため、
データの“形”や分野が異なる6つのデータセットを追加で生成します。
それぞれ別の分析パターンを練習するための素材です。

  1. timeseries/web_traffic_daily.csv … 日次Webアクセス（時系列：トレンド/季節性/欠測/急増）
  2. marketing/ad_campaigns.csv       … 広告チャネル別実績（比率・ファネル：CTR/CVR/CPA/ROAS）
  3. survey/customer_survey.csv       … 顧客アンケート（カテゴリ・リッカート・NPS・自由記述）
  4. hr/employees.csv                 … 従業員データ（混合型：群比較・回帰・離職）
  5. iot/sensor_readings.csv          … 製造ラインのセンサー（高頻度・異常検知・欠損・外れ値）
  6. finance/stock_prices.csv         … 株価（複数時系列：リターン・ボラ・相関）

すべて乱数シード固定。実在の人物・企業・銘柄とは一切関係ありません。

使い方:
    python scripts/generate_extra_datasets.py
"""

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 2024
rng = np.random.default_rng(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data"))


def _dir(name):
    p = os.path.join(DATA_DIR, name)
    os.makedirs(p, exist_ok=True)
    return p


def _save(df, subdir, filename):
    path = os.path.join(_dir(subdir), filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path, len(df)


# ----------------------------------------------------------------------
# 1. 日次Webアクセス（時系列パターン）
# ----------------------------------------------------------------------
def make_web_traffic():
    """
    2年分の日次アクセス。
    - ゆるやかな上昇トレンド
    - 週次季節性（週末はやや低い）
    - 月初の軽い盛り上がり
    - 年末商戦やキャンペーンによる数回の急増（スパイク）
    - 数日の欠測（計測トラブル想定でNaN行）
    """
    start = datetime(2023, 1, 1)
    days = 731  # 2023-01-01 .. 2024-12-31
    dates = [start + timedelta(days=i) for i in range(days)]

    t = np.arange(days)
    trend = 3000 + 6.0 * t                      # 右肩上がり
    weekly = 1 + 0.18 * np.sin(2 * np.pi * (t % 7) / 7 - 1.2)  # 曜日の波
    weekend = np.array([0.82 if d.weekday() >= 5 else 1.0 for d in dates])  # 週末減
    noise = rng.normal(1.0, 0.06, days)

    sessions = trend * weekly * weekend * noise

    # キャンペーン/イベントによるスパイク
    spike_idx = [60, 175, 330, 360, 510, 690]   # それっぽい日に急増
    for s in spike_idx:
        width = rng.integers(2, 5)
        for k in range(width):
            if s + k < days:
                sessions[s + k] *= rng.uniform(1.5, 2.4)

    sessions = sessions.round().astype(float)

    users = (sessions * rng.uniform(0.7, 0.8, days)).round()
    pageviews = (sessions * rng.uniform(2.5, 4.0, days)).round()
    bounce_rate = np.clip(rng.normal(0.45, 0.05, days), 0.2, 0.8).round(3)
    cvr = np.clip(rng.normal(0.025, 0.006, days), 0.005, None)
    conversions = (sessions * cvr).round()
    revenue = (conversions * rng.normal(6200, 800, days)).round()

    df = pd.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "sessions": sessions,
        "users": users,
        "pageviews": pageviews,
        "bounce_rate": bounce_rate,
        "conversions": conversions,
        "revenue": revenue,
    })

    # 欠測（計測トラブル）を数日分入れる：その日の指標をNaNに
    miss_days = rng.choice(days, size=8, replace=False)
    metric_cols = ["sessions", "users", "pageviews", "bounce_rate", "conversions", "revenue"]
    df.loc[miss_days, metric_cols] = np.nan

    return df


# ----------------------------------------------------------------------
# 2. 広告チャネル別実績（比率・ファネルパターン）
# ----------------------------------------------------------------------
def make_ad_campaigns():
    """
    チャネル×日次の広告実績。
    impressions → clicks → conversions のファネル。
    チャネルごとに CTR / CVR / 単価が異なる（比較演習向け）。
    """
    start = datetime(2024, 1, 1)
    days = 182  # 半年分
    dates = [start + timedelta(days=i) for i in range(days)]

    channels = {
        # name:        (日次imp平均, CTR,   CVR,   1クリック単価CPC, 1CVあたり売上)
        "検索広告":     (12000, 0.045, 0.060, 95,  7800),
        "ディスプレイ": (40000, 0.008, 0.012, 38,  6500),
        "SNS広告":      (28000, 0.018, 0.030, 60,  6900),
        "動画広告":     (35000, 0.012, 0.018, 45,  6600),
        "アフィリエイト":(6000, 0.030, 0.050, 70,  7200),
    }

    rows = []
    for ch, (imp_base, ctr, cvr, cpc, rev_per_cv) in channels.items():
        for i, d in enumerate(dates):
            # 週末は配信やや増、ノイズあり
            wk = 1.1 if d.weekday() >= 5 else 1.0
            imp = max(0, rng.normal(imp_base * wk, imp_base * 0.12))
            clicks = rng.binomial(int(imp), np.clip(rng.normal(ctr, ctr * 0.15), 0.001, 0.5))
            conv = rng.binomial(int(clicks), np.clip(rng.normal(cvr, cvr * 0.2), 0.001, 0.9))
            cost = clicks * rng.normal(cpc, cpc * 0.1)
            revenue = conv * rng.normal(rev_per_cv, rev_per_cv * 0.15)
            rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "channel": ch,
                "impressions": int(imp),
                "clicks": int(clicks),
                "cost": round(float(cost)),
                "conversions": int(conv),
                "revenue": round(float(revenue)),
            })
    df = pd.DataFrame(rows)
    return df


# ----------------------------------------------------------------------
# 3. 顧客アンケート（カテゴリ・リッカート・NPSパターン）
# ----------------------------------------------------------------------
def make_survey():
    """
    1人1行のアンケート結果。
    - 属性（年代・性別・地域・会員種別）
    - 満足度・各項目評価（1〜5のリッカート尺度）
    - 推奨度（0〜10：NPS算出用）
    - 知ったきっかけ（カテゴリ）
    - 自由記述（短い定型コメントからランダム）
    一部に未回答（欠損）を含む。
    """
    n = 1200
    age_groups = rng.choice(["10代", "20代", "30代", "40代", "50代", "60代以上"],
                            n, p=[0.05, 0.22, 0.27, 0.22, 0.15, 0.09])
    gender = rng.choice(["女性", "男性", "回答しない"], n, p=[0.54, 0.41, 0.05])
    region = rng.choice(["北海道・東北", "関東", "中部", "近畿", "中国・四国", "九州・沖縄"],
                        n, p=[0.10, 0.35, 0.16, 0.20, 0.09, 0.10])
    membership = rng.choice(["無料会員", "有料会員"], n, p=[0.7, 0.3])

    # 有料会員ほど満足度が高い、という構造を入れる
    base = np.where(membership == "有料会員", 4.1, 3.4)
    quality = np.clip(rng.normal(base, 0.8, n).round(), 1, 5).astype(int)
    price = np.clip(rng.normal(base - 0.4, 0.9, n).round(), 1, 5).astype(int)
    support = np.clip(rng.normal(base - 0.2, 1.0, n).round(), 1, 5).astype(int)
    # 総合満足度は各項目に連動＋ノイズ
    satisfaction = np.clip(
        np.round((quality + price + support) / 3 + rng.normal(0, 0.5, n)), 1, 5
    ).astype(int)
    # 推奨度（0-10）は満足度に連動
    recommend = np.clip((satisfaction * 2 + rng.normal(0, 1.5, n)).round(), 0, 10).astype(int)

    heard = rng.choice(["検索", "SNS", "友人・知人", "広告", "メディア記事", "その他"],
                       n, p=[0.30, 0.25, 0.18, 0.15, 0.08, 0.04])

    comments_pos = ["使いやすい", "サポートが丁寧", "コスパが良い", "デザインが好き", "品揃えが豊富"]
    comments_neg = ["値段が高い", "動作が重い", "問い合わせ対応が遅い", "在庫切れが多い", "解約しづらい"]
    comments_neu = ["特になし", "普通", "改善に期待"]
    comment = []
    for s in satisfaction:
        if s >= 4:
            comment.append(rng.choice(comments_pos))
        elif s <= 2:
            comment.append(rng.choice(comments_neg))
        else:
            comment.append(rng.choice(comments_neu))

    df = pd.DataFrame({
        "respondent_id": np.arange(1, n + 1),
        "age_group": age_groups,
        "gender": gender,
        "region": region,
        "membership": membership,
        "satisfaction": satisfaction,
        "q_quality": quality,
        "q_price": price,
        "q_support": support,
        "recommend_score": recommend,
        "heard_from": heard,
        "free_comment": comment,
    })

    # 一部未回答（リッカート項目・自由記述）
    for col, k in [("q_support", 70), ("q_price", 40), ("free_comment", 120), ("recommend_score", 30)]:
        idx = rng.choice(df.index, size=k, replace=False)
        df.loc[idx, col] = np.nan
    return df


# ----------------------------------------------------------------------
# 4. 従業員データ（混合型・回帰・群比較・離職パターン）
# ----------------------------------------------------------------------
def make_employees():
    """
    1人1行の人事データ。
    給与は 職級・勤続・学歴 で説明できる構造（回帰演習向け）。
    離職(attrition)は 残業・エンゲージメント・給与 に依存（要因分析向け）。
    """
    n = 1500
    departments = rng.choice(
        ["営業", "開発", "マーケティング", "カスタマーサポート", "管理部門", "人事"],
        n, p=[0.28, 0.30, 0.12, 0.15, 0.10, 0.05],
    )
    job_level = rng.choice([1, 2, 3, 4, 5], n, p=[0.30, 0.30, 0.22, 0.13, 0.05])
    age = np.clip(rng.normal(38, 9, n).round(), 22, 64).astype(int)
    tenure = np.clip(rng.normal((age - 22) * 0.35, 3, n).round(), 0, 35).astype(int)
    education = rng.choice(["高卒", "専門・短大", "大卒", "院卒"], n, p=[0.15, 0.20, 0.50, 0.15])
    gender = rng.choice(["女性", "男性"], n, p=[0.45, 0.55])
    region = rng.choice(["東京", "大阪", "名古屋", "福岡", "札幌", "リモート"],
                        n, p=[0.40, 0.18, 0.12, 0.10, 0.05, 0.15])

    edu_bonus = pd.Series(education).map(
        {"高卒": 0, "専門・短大": 1.5, "大卒": 4, "院卒": 7}).to_numpy()
    # 月給（万円）：職級が主因、勤続・学歴・年齢が加算、ノイズ
    salary = (
        22
        + job_level * 7.5
        + tenure * 0.6
        + edu_bonus
        + (age - 22) * 0.15
        + rng.normal(0, 3.0, n)
    )
    salary = np.clip(salary, 18, None).round(1)
    monthly_salary = (salary * 10000).round().astype(int)  # 円

    overtime = np.clip(rng.normal(20, 12, n), 0, 80).round().astype(int)
    # エンゲージメント（1-5）：残業多いほど下がる傾向＋ノイズ
    engagement = np.clip(
        np.round(4.2 - overtime * 0.02 + rng.normal(0, 0.7, n), 1), 1.0, 5.0)

    # 離職確率：残業↑・エンゲージ↓・給与↓ で上昇
    logit = (
        -2.4
        + overtime * 0.035
        - (engagement - 3) * 0.9
        - (salary - salary.mean()) * 0.03
    )
    prob = 1 / (1 + np.exp(-logit))
    attrition = rng.binomial(1, np.clip(prob, 0.01, 0.95))

    df = pd.DataFrame({
        "employee_id": np.arange(1, n + 1),
        "department": departments,
        "job_level": job_level,
        "age": age,
        "tenure_years": tenure,
        "education": education,
        "gender": gender,
        "work_location": region,
        "monthly_salary": monthly_salary,
        "overtime_hours": overtime,
        "engagement_score": engagement,
        "attrition": attrition,  # 1=退職, 0=在籍
    })
    return df


# ----------------------------------------------------------------------
# 5. 製造ラインのセンサー（高頻度・異常検知・欠損・外れ値パターン）
# ----------------------------------------------------------------------
def make_sensors():
    """
    複数マシンの毎時センサー値（約2週間分）。
    - 温度・振動・圧力・回転数
    - 緩やかなドリフト（時間とともに温度が上がる劣化）
    - センサー欠損（NaN）
    - 突発的な外れ値（スパイク）
    - 不良(defect)は 高温×高振動 で発生しやすい
    """
    start = datetime(2024, 6, 1)
    hours = 24 * 14
    machines = ["M-01", "M-02", "M-03", "M-04"]

    rows = []
    for m in machines:
        base_temp = rng.uniform(60, 70)
        drift = rng.uniform(0.01, 0.05)  # 機体ごとの劣化速度
        for h in range(hours):
            ts = start + timedelta(hours=h)
            day_cycle = np.sin(2 * np.pi * (h % 24) / 24)  # 日内変動
            temp = base_temp + drift * h + 3 * day_cycle + rng.normal(0, 1.2)
            vibration = 2.0 + 0.02 * (temp - base_temp) + rng.normal(0, 0.3)
            pressure = rng.normal(101.3, 1.5)
            rpm = rng.normal(1500, 40)

            # 外れ値スパイク（まれに）
            if rng.random() < 0.01:
                temp += rng.uniform(15, 30)
                vibration += rng.uniform(2, 5)

            # 不良発生：高温×高振動で確率上昇
            logit = -6 + 0.07 * (temp - 65) + 1.2 * (vibration - 2.5)
            defect = rng.binomial(1, 1 / (1 + np.exp(-logit)))

            rows.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
                "machine_id": m,
                "temperature": round(float(temp), 2),
                "vibration": round(float(vibration), 3),
                "pressure": round(float(pressure), 2),
                "rpm": int(rpm),
                "defect": int(defect),
            })

    df = pd.DataFrame(rows)
    # センサー欠損を散らす
    for col, k in [("temperature", 60), ("vibration", 45), ("pressure", 40), ("rpm", 30)]:
        idx = rng.choice(df.index, size=k, replace=False)
        df.loc[idx, col] = np.nan
    return df


# ----------------------------------------------------------------------
# 6. 株価（複数時系列・リターン・相関パターン）
# ----------------------------------------------------------------------
def make_stocks():
    """
    架空5銘柄の日次終値（営業日, 約2年）。
    幾何ブラウン運動でランダムウォーク。
    一部銘柄は共通の市場ファクターで相関させる（相関演習向け）。
    """
    start = datetime(2023, 1, 2)
    # 平日のみ（簡易的に土日を除く）
    dates = []
    d = start
    while len(dates) < 500:
        if d.weekday() < 5:
            dates.append(d)
        d += timedelta(days=1)
    n = len(dates)

    tickers = {
        # name:    (初期株価, 年率ドリフト, 年率ボラ, 市場ファクター感応度beta)
        "アオゾラ電機": (1500, 0.10, 0.25, 1.1),
        "ソラリス製薬": (3200, 0.06, 0.20, 0.6),
        "ミドリ商事":   (800,  0.03, 0.30, 1.3),
        "ヒカリ銀行":   (2100, 0.04, 0.18, 0.9),
        "コスモ食品":   (1200, 0.05, 0.15, 0.4),
    }

    dt = 1 / 252
    # 共通市場リターン（ボラを高めにして銘柄間の相関構造をはっきりさせる）
    market = rng.normal(0.04 * dt, 0.22 * np.sqrt(dt), n)

    rows = []
    for name, (p0, mu, vol, beta) in tickers.items():
        idio = rng.normal(0, vol * np.sqrt(dt), n)         # 個別要因
        ret = (mu * dt) + beta * market + idio
        price = p0 * np.exp(np.cumsum(ret))
        for i, dd in enumerate(dates):
            rows.append({
                "date": dd.strftime("%Y-%m-%d"),
                "ticker": name,
                "close": round(float(price[i]), 1),
            })
    df = pd.DataFrame(rows)
    return df


# ----------------------------------------------------------------------
# メイン
# ----------------------------------------------------------------------
def main():
    print("発展用サンプルデータを生成します ...\n")
    results = []

    df = make_web_traffic()
    results.append(("時系列",         *_save(df, "timeseries", "web_traffic_daily.csv")))

    df = make_ad_campaigns()
    results.append(("広告ファネル",   *_save(df, "marketing", "ad_campaigns.csv")))

    df = make_survey()
    results.append(("アンケート/NPS", *_save(df, "survey", "customer_survey.csv")))

    df = make_employees()
    results.append(("人事/離職",      *_save(df, "hr", "employees.csv")))

    df = make_sensors()
    results.append(("IoTセンサー",    *_save(df, "iot", "sensor_readings.csv")))

    df = make_stocks()
    results.append(("株価/金融",      *_save(df, "finance", "stock_prices.csv")))

    print("=== 生成結果 ===")
    for label, path, nrows in results:
        rel = os.path.relpath(path, DATA_DIR)
        print(f"  [{label:>12s}]  data/{rel:<38s} {nrows:>6,} 行")
    print(f"\n出力先: {DATA_DIR}")
    print("完了しました。データの説明は docs/data_catalog.md を参照してください。")


if __name__ == "__main__":
    main()
