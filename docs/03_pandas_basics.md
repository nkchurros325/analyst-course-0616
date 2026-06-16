# 03. Python / pandas 基礎

> このモジュールのゴール：**pandas でデータを「読む・選ぶ・絞る・並べる・集計する・結合する・整える」一連の操作ができるようになる。**
> 前提：[02. SQL 基礎](02_sql_basics.md) を終えていること。SQL で解いた問い（月次売上・カテゴリ別売上・顧客別購入額など）を、ここでは pandas で解き直します。

---

## 3-1. なぜ pandas なのか

SQL は「データベースから必要な行・列を取り出す」のが得意でした。pandas は、取り出した**手元のデータを自由に加工・分析・可視化**するためのツールです。

- 列を足したり、欠損を埋めたり、複雑な計算をしたり（SQLより柔軟）
- そのまま matplotlib / seaborn でグラフ化できる（モジュール05以降）
- scikit-learn など他のライブラリへ橋渡しできる

実務では「**SQLで粗く絞って取り出し → pandasで仕上げる**」という分業がよくあります。両方の対応を意識すると上達が早いです。

---

## 3-2. DataFrame と Series ── 2つの基本の型

pandas のデータは、ほぼこの2つで表せます。

| 型 | イメージ | 例 |
|----|---------|----|
| **Series** | 1列分のデータ（ラベル付きの1次元配列） | `df['price']` |
| **DataFrame** | 表全体（複数のSeriesが列として並んだ2次元） | `df` |

```python
df = pd.read_csv("data/products.csv")  # DataFrame（表）
s  = df["price"]                        # Series（1列）
```

- DataFrame には **行ラベル（index）** と **列ラベル（columns）** があります。
- 「1列だけ選ぶと Series、2列以上だと DataFrame」と覚えておくと混乱しません。

> 💡 表計算ソフトで言えば、DataFrame が「シート全体」、Series が「1列分の縦の並び」。
> index は「行番号（または行の名前）」にあたります。

---

## 3-3. SQL と pandas の対応表

SQL を知っていれば、pandas は「同じことを別の書き方でやるだけ」です。

| やりたいこと | SQL | pandas |
|-------------|-----|--------|
| 全件・先頭を見る | `SELECT * ... LIMIT 5` | `df.head()` |
| 列を選ぶ | `SELECT a, b` | `df[["a", "b"]]` |
| 行を絞る | `WHERE age >= 30` | `df[df["age"] >= 30]` |
| 並べ替え | `ORDER BY price DESC` | `df.sort_values("price", ascending=False)` |
| 上位N件 | `ORDER BY x DESC LIMIT 10` | `df.nlargest(10, "x")` |
| 集計 | `GROUP BY category` | `df.groupby("category")` |
| 集計関数 | `SUM(x), AVG(x), COUNT(*)` | `.agg(["sum", "mean", "count"])` |
| 件数の数え上げ | `GROUP BY g` + `COUNT` | `df["g"].value_counts()` |
| 結合 | `JOIN ... ON` | `df.merge(other, on="key")` |
| 重複なし一覧 | `SELECT DISTINCT g` | `df["g"].unique()` |
| クロス集計 | （複雑な GROUP BY） | `df.pivot_table(...)` |

> 🧭 大きな違い：SQL は「サーバに命令を送って結果を受け取る」、pandas は「メモリ上の表を直接いじる」。
> だから pandas では途中結果を変数に取って `print` で確かめながら進められます。

---

## 3-4. まず全体を把握する（読み込み〜要約）

データを受け取ったら、**いきなり集計せず、まず全体像を掴む**のが鉄則です。

```python
df = pd.read_csv("data/customers.csv")

df.head()       # 先頭5行。中身のイメージを掴む
df.tail()       # 末尾5行
df.shape        # (行数, 列数)
df.info()       # 列名・型・非欠損数。欠損やdtypeの確認に必須
df.describe()   # 数値列の要約統計（件数・平均・std・min・四分位・max）
df.dtypes       # 各列のデータ型
```

- `info()` で **欠損（non-null の数が行数より少ない列）** をまず疑う。
- `describe()` で **min/max がおかしくないか**（年齢が0や999など）を確認する。
- `dtypes` で **日付が object（文字列）のまま**になっていないかを見る（後で `to_datetime` する）。

> 💡 この「最初の5分の健康診断」を省くと、後の集計で必ず痛い目を見ます（モジュール04クレンジングで詳述）。

---

## 3-5. 列と行の選択

### 列の選択

```python
df["age"]            # 1列 → Series
df[["name", "age"]]  # 複数列 → DataFrame（[[ ]] と二重括弧）
```

### 行の選択 ── `loc` と `iloc`

| | 指定方法 | 例 |
|--|---------|----|
| `loc` | **ラベル**（列名・index名）で指定 | `df.loc[0, "age"]`、`df.loc[:, ["name", "age"]]` |
| `iloc` | **位置（整数）** で指定 | `df.iloc[0, 2]`、`df.iloc[:5, :3]` |

```python
df.loc[df["age"] >= 30, ["name", "prefecture"]]  # 条件で行、ラベルで列（実務で一番使う形）
df.iloc[0]        # 0行目（Series）
df.iloc[:5]       # 先頭5行
```

> 💡 迷ったら **`loc`（名前で指定）を基本**にする。位置で取りたいときだけ `iloc`。
> 「`df["col"]` は列、`df.loc[行, 列]` は行と列の両方」を区別すると混乱しません。

---

## 3-6. 条件で絞り込む（ブールインデックス）

`df[条件]` の「条件」は、各行が True/False の **Series（ブール）** です。

```python
df[df["age"] >= 30]                               # 30歳以上
df[(df["age"] >= 30) & (df["prefecture"] == "東京都")]  # 複数条件は & | で、各条件は ( ) で囲む
df[df["prefecture"].isin(["東京都", "大阪府"])]    # いずれかに一致（SQLのIN）
df[df["age"].between(30, 39)]                      # 30〜39（両端含む）
df.query("age >= 30 and prefecture == '東京都'")  # 文字列で書ける query
```

- **複数条件は `and/or` ではなく `&`（かつ）`|`（または）**。さらに各条件を**必ず `( )` で囲む**（演算子の優先順位の都合）。これは初心者がよく踏むワナです。
- `query()` は SQL の `WHERE` に近い書き味で、条件が長いときに読みやすい。

> 💡 `&` `|` を `and` `or` と書くと `ValueError` になります。エラーが出たらまずここを疑う。

---

## 3-7. 並べ替えと上位N件

```python
df.sort_values("price", ascending=False)          # 価格の高い順
df.sort_values(["category", "price"], ascending=[True, False])  # 複数キー
df.nlargest(10, "price")                           # 上位10件（sort + head の近道）
df.sort_values("price", ascending=False).head(10) # 同じ結果
```

`nlargest` / `nsmallest` は「上位・下位N件だけ欲しい」ときの定番。SQL の `ORDER BY ... LIMIT` に対応します。

---

## 3-8. 新しい列を作る

```python
# 直接代入
df["profit"] = df["price"] - df["cost"]
df["margin"] = (df["price"] - df["cost"]) / df["price"]

# assign（元を壊さず新しいDataFrameを返す。メソッドチェーンで便利）
df2 = df.assign(profit=df["price"] - df["cost"])

# apply（行や値ごとに関数を適用。柔軟だが遅いので「ベクトル演算でできないとき」だけ）
df["price_band"] = df["price"].apply(lambda p: "高" if p >= 5000 else "中" if p >= 2000 else "低")
```

> 💡 まず四則演算（**ベクトル演算**）で書けないか考える。`df["a"] * df["b"]` のような列同士の計算は速く、`apply` は最後の手段。

---

## 3-9. 数え上げと基本集計

```python
df["gender"].value_counts()                 # カテゴリごとの件数（多い順）
df["gender"].value_counts(normalize=True)   # 構成比（割合）
df["age"].mean(), df["age"].median()        # 平均・中央値
df["price"].sum()                           # 合計
```

`value_counts()` は「性別構成」「都道府県の分布」など**カテゴリ列の概観**に最適。`normalize=True` で割合になります。

---

## 3-10. groupby + agg ── 集計の本丸

「**グループごとに集計する**」のが `groupby`。SQL の `GROUP BY` そのものです。

```python
# カテゴリ別の平均価格
prod.groupby("category")["price"].mean()

# カテゴリ別に「平均価格」と「商品数」を同時に（agg）
prod.groupby("category").agg(
    avg_price=("price", "mean"),
    n_products=("product_id", "count"),
)

# 複数キーでグループ化
df.groupby(["prefecture", "gender"])["age"].mean()
```

- `agg(新しい列名=("対象列", "集計方法"))` の形（**named aggregation**）が読みやすくおすすめ。
- 集計方法は `"sum" / "mean" / "count" / "min" / "max" / "median" / "nunique"` などが使えます。

> 💡 `groupby` の結果は index がグループキーになります。表として扱いたいときは `.reset_index()` を付けると列に戻ります。

---

## 3-11. merge ── テーブルの結合

複数の表を「キー」でつなぐのが `merge`。SQL の `JOIN` です。Sora Mart の売上は4テーブルにまたがるので、ここが分析の要になります。

```python
# order_items に orders を結合して、status と order_date を持ってくる
sales = order_items.merge(orders, on="order_id")
# さらに商品・顧客情報も
sales = sales.merge(products, on="product_id").merge(customers, on="customer_id")
```

### `how`（結合方法）の違い

| how | 意味 | 残る行 |
|-----|------|--------|
| `inner`（既定） | 両方にキーがある行だけ | 共通部分のみ |
| `left` | 左を全部残す | 左の全行（右が無ければ NaN） |
| `right` | 右を全部残す | 右の全行 |
| `outer` | どちらかにあれば残す | 全部（無い側は NaN） |

```python
order_items.merge(orders, on="order_id", how="left")  # 注文明細を全部残したい場合
```

> 💡 結合後は **行数が想定通りか必ず確認**（`df.shape`）。キーが重複していると行が増殖します（多対多）。
> 「明細(order_items) に注文(orders) を `left` で付ける」と、明細の件数が保たれて安心です。

---

## 3-12. 売上の作り方（このコースの厳守ルール）

> **売上 = `order_items.quantity × order_items.unit_price` を合計。`status == 'completed'` の注文のみ**（cancelled / returned は売上に含めない）。

```python
sales = order_items.merge(orders[["order_id", "status", "order_date"]], on="order_id")
sales = sales[sales["status"] == "completed"].copy()
sales["amount"] = sales["quantity"] * sales["unit_price"]
sales["amount"].sum()   # → 総売上
```

この `sales`（completed のみ・amount 列付き）を、以降の集計の出発点にします。

---

## 3-13. 日付を扱う

CSV から読むと日付は**ただの文字列（object）**です。`pd.to_datetime` で日付型に変換すると、年・月などを取り出せます。

```python
sales["order_date"] = pd.to_datetime(sales["order_date"])
sales["year"]  = sales["order_date"].dt.year     # 年
sales["month"] = sales["order_date"].dt.month    # 月
sales["ym"]    = sales["order_date"].dt.to_period("M")  # 2024-03 のような月単位

# 月次売上
monthly = sales.groupby("ym")["amount"].sum()
```

- `.dt` アクセサ経由で `year / month / day / weekday / to_period` などが使えます。
- `to_period("M")` は「年月」をひとまとめにでき、月次集計のキーに便利です。

---

## 3-14. pivot_table ── クロス集計

行と列の2軸で集計するのが `pivot_table`。Excel のピボットテーブルと同じ発想です。

```python
# 獲得経路（行）× 性別（列）の人数クロス集計
customers.pivot_table(
    index="acquisition_channel",
    columns="gender",
    values="customer_id",
    aggfunc="count",
    fill_value=0,
)
```

- `index`＝行に置く軸、`columns`＝列に置く軸、`values`＝集計する値、`aggfunc`＝集計方法。
- `fill_value=0` で「該当なし」のセルを 0 にできます。
- `margins=True` を付けると行・列の合計（総計）も出ます。

> 💡 `groupby(["a","b"]).size()` でも同じ集計はできますが、`pivot_table` は**2軸を縦横に並べた表**にしてくれるので人が読みやすい。

---

## 3-15. よく使うメソッド早見表

| 目的 | メソッド |
|------|---------|
| 読み込み | `pd.read_csv(path)` |
| 全体把握 | `head` / `tail` / `shape` / `info` / `describe` / `dtypes` |
| 列選択 | `df["c"]` / `df[["a","b"]]` |
| 行選択 | `df.loc[行, 列]` / `df.iloc[i, j]` |
| 条件抽出 | `df[条件]` / `isin` / `between` / `query` |
| 並べ替え | `sort_values` / `nlargest` / `nsmallest` |
| 列追加 | 代入 / `assign` / `apply` |
| 数え上げ | `value_counts` / `nunique` / `unique` |
| 集計 | `groupby` + `agg` / `sum` / `mean` / `count` |
| 結合 | `merge`（`how=inner/left/right/outer`） |
| 日付 | `pd.to_datetime` / `.dt.year` / `.dt.to_period` |
| クロス集計 | `pivot_table` |
| index操作 | `reset_index` / `set_index` |

---

## 3-16. このあとの流れ

pandas でデータを操れるようになりました。でも現実のデータは**欠損・重複・表記ゆれ・型崩れ**だらけです。
次は、そんな「汚いデータ」を分析できる状態に整える技術を学びます。

👉 [04. データクレンジング](04_data_cleaning.md) へ

> 演習では SQL モジュールと同じ問い（月次売上・カテゴリ別売上・顧客別購入額）も解きます。
> 「同じ答えが SQL でも pandas でも出せる」ことを確認し、**道具に依らず問いに答える**感覚を養いましょう。
