# 教材オーサリング共通仕様（執筆者向け・内部資料）

この講座のモジュールを書くときの共通ルール。各モジュール担当はこれに従うこと。

## 対象・トーン
- 対象：初級〜中級の学習者。日本語。丁寧で実践的、ただし冗長にしない。
- 「やり方」だけでなく「なぜそうするか」「結果をどう解釈するか」を必ず添える。
- コース全体の世界観：架空EC「Sora Mart（ソラマート）」の分析。

## データ（`./data/` に生成済み）
- `customers.csv` … customer_id, name, gender(女性/男性/回答なし), age, prefecture(都道府県), registration_date(YYYY-MM-DD), acquisition_channel(検索広告/SNS広告/オーガニック検索/メルマガ/友人紹介)。2,000行。
- `products.csv` … product_id, product_name, category(キッチン/インテリア/文具/アパレル/食品/美容), price(円), cost(円)。80行。
- `orders.csv` … order_id, customer_id, order_date(YYYY-MM-DD), status(completed/cancelled/returned), payment_method(クレジットカード/代金引換/コンビニ払い/電子マネー)。約5,900行。
- `order_items.csv` … order_item_id, order_id, product_id, quantity, unit_price(円)。約14,800行。
- `sora_mart.db` … 上記4テーブルを収録した SQLite（SQL演習用）。
- `customers_raw.csv` … 汚した顧客データ（モジュール04専用）。
- `ab_test.csv` … user_id, group(A/B), converted(0/1), session_seconds（モジュール07専用）。

## 厳守する分析規約
- **売上 = `order_items.quantity × order_items.unit_price` を合計**。注文に紐付け、**`status='completed'` のみ**を売上とする（cancelled/returned は売上ではない）。
- 期間は 2023-01-01〜2024-12-31。
- **使えるライブラリ**：pandas, numpy, matplotlib, seaborn, scipy, sqlite3。
- **使えない（import 禁止）**：sklearn, statsmodels。回帰は scipy.stats.linregress や numpy の最小二乗（np.linalg.lstsq）で実装する。

## 成果物（モジュールごとに2ファイル）
1. `docs/NN_xxx.md` … 解説（読み物）。概念＋なぜ＋小さなコード/SQL例＋表＋💡Tip。見出しを使い、最後に次モジュールへのリンクを置く。
2. `notebooks_src/NN_xxx.py` … percent形式のノートブック元ファイル（下記）。`scripts/build_notebooks.py` で `.ipynb` に変換される。

## percent形式のルール（notebooks_src/*.py）
- マークダウンセル：行 `# %% [markdown]` で開始。以降の各行は `# 本文`（先頭の `# ` が除去されて本文になる）。空行は `#` だけの行。
  - 見出しは `# # タイトル`（→ H1）、`# ## 見出し`（→ H2）のように書く。
- コードセル：行 `# %%` で開始。以降は素のPythonコード。
- 例：
  ```
  # %% [markdown]
  # # タイトル
  #
  # 説明文。

  # %%
  df = pd.read_csv("...")
  df.head()
  ```

## ノートブックの構成（必須）
1. 先頭マークダウン：タイトル＋🎯このモジュールのゴール＋前提（前のモジュール）。
2. セットアップのコードセル（下記テンプレを使う）。
3. 以降は **📖解説(md) → ▶️例(code・コメント付きで必ず print などで結果を出す) → 🖊EXERCISE(md・課題説明) → 演習用スケルトンセル(code)** を繰り返す。
   - スケルトンセルは **コメントとヒントだけ**にし `# ここにコードを書く` を置く（＝ファイルを通し実行してもエラーにならない）。必要なら `pass`。
4. EXERCISE は **5〜8問**、易→難。各問に「期待される答えのヒント」を一言。
5. 末尾に マークダウン `## ✅ 解答例` を置き、続けて各問の解答コードセル（`# --- 解答1 ---` のようにラベル）。**解答セルは実データで実際に正しく動くこと。**

### セットアップ・テンプレ（コピーして調整）
```python
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
```

### SQLモジュールはセットアップに追加
```python
import sqlite3
conn = sqlite3.connect(os.path.join(DATA, "sora_mart.db"))
def q(sql):
    """SQLを実行して DataFrame で返すヘルパー。"""
    return pd.read_sql(sql, conn)
```

### 可視化を使うモジュール（05,06,07,08,09）はセットアップ先頭に追加
```python
import matplotlib
matplotlib.use("Agg")  # スクリプト実行時に plt.show() でブロックしないため（Jupyterでは無視してOK）
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
for _c in ["Meiryo", "Yu Gothic", "MS Gothic", "Hiragino Sans", "IPAexGothic", "Noto Sans CJK JP"]:
    if _c in {f.name for f in font_manager.fontManager.ttflist}:
        rcParams["font.family"] = _c
        break
rcParams["axes.unicode_minus"] = False
import seaborn as sns
sns.set_theme(style="whitegrid", font=rcParams["font.family"])
```
> 注：`matplotlib.use("Agg")` は import pyplot より前に置く。Jupyterユーザー向けにコメントで「Jupyterではこの行は不要」と書いておくと親切。

## 検証（提出前に必須）
1. コース直下で `python scripts/build_notebooks.py NN_xxx.py` を実行し、変換できること。
2. `python notebooks_src/NN_xxx.py` を実行し、**例外なく終了コード0**になること（matplotlibのAgg警告は無視可）。エラーは直す。
3. 例セルも解答セルも実データで通ること。スケルトンセルは通し実行で落ちないこと。

完了時に「2ファイルのパス」と「python 実行が成功したこと」を報告する。
