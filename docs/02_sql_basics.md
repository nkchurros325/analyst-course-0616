# 02. SQL 基礎

> このモジュールのゴール：**SQL でデータベースから必要なデータを「正しく」取り出せるようになる。**
> SELECT の基本から、絞り込み・並べ替え・集計・結合、そして中級のウィンドウ関数まで、Sora Mart の実データで段階的に手を動かします。

前提：[01. アナリストの思考法](01_analyst_mindset.md)。分析の5ステップのうち、本章は **③取得・加工** を担います。

---

## 2-0. SQL は「集合に対する操作」

プログラミングのループ（1件ずつ処理する）と違い、**SQL は表（行の集合）まるごとに対して「こういう条件で、こう集めて、こう並べて」と宣言する**言語です。

> 「どう処理するか（手続き）」ではなく「何が欲しいか（結果の形）」を書く。

この発想の切り替えが SQL 上達の第一歩です。「1行ずつ」ではなく「この条件を満たす行の集合」「このキーでまとめた集合」と考えましょう。

本章で使うデータベースは `data/sora_mart.db`（SQLite）。テーブルは4つです。

| テーブル | 主なカラム | 1行の意味 |
|---|---|---|
| `customers` | customer_id, age, prefecture, acquisition_channel | 顧客1人 |
| `products` | product_id, product_name, category, price, cost | 商品1つ |
| `orders` | order_id, customer_id, order_date, status | 注文1件 |
| `order_items` | order_item_id, order_id, product_id, quantity, unit_price | 注文の明細1行 |

> 🧭 **分析規約（本講座で厳守）**：売上は `order_items.quantity × unit_price` の合計。注文（`orders`）に紐付けて **`status='completed'` のみ**を売上とする（cancelled / returned は売上に含めない）。この規約は本章のほぼ全ての売上クエリに登場します。

---

## 2-1. SELECT / FROM / LIMIT / DISTINCT ── まず中身を見る

データ分析は「まず眺める」から始まります。

```sql
-- 全カラムを5行だけ見る（* は「全部の列」）
SELECT * FROM customers LIMIT 5;

-- 必要な列だけ選ぶ
SELECT customer_id, age, prefecture FROM customers LIMIT 5;

-- 重複を除いて値の種類を見る（どんな都道府県があるか）
SELECT DISTINCT prefecture FROM customers;
```

- `SELECT` … 取り出す**列**を指定（`*` は全列）。
- `FROM` … どの**テーブル**から取るか。
- `LIMIT n` … 先頭 `n` 行だけ。**大きなテーブルをいきなり全件見ない**ための安全装置。
- `DISTINCT` … 重複を除く。「この列にはどんな値があるのか」を把握するのに便利。

> 💡 新しいテーブルに出会ったら、まず `SELECT * ... LIMIT 5` と `SELECT DISTINCT 列` で**カラムの意味と値の種類**を確認する癖を。

---

## 2-2. WHERE ── 行を絞り込む

`WHERE` は**条件に合う行だけ**を残します。

```sql
-- 比較演算子
SELECT * FROM customers WHERE age >= 30;

-- AND / OR（複数条件。OR と AND が混ざるときは括弧で意図を明確に）
SELECT * FROM customers WHERE age >= 30 AND gender = '女性';
SELECT * FROM customers WHERE prefecture = '東京都' OR prefecture = '大阪府';

-- IN（候補のどれか）
SELECT * FROM customers WHERE prefecture IN ('東京都', '大阪府', '愛知県');

-- BETWEEN（範囲、両端を含む）
SELECT * FROM customers WHERE age BETWEEN 20 AND 29;

-- LIKE（部分一致。% は任意の文字列、_ は任意の1文字）
SELECT * FROM products WHERE product_name LIKE 'キッチン%';
```

| 書き方 | 意味 |
|---|---|
| `=`, `<>`, `<`, `>`, `<=`, `>=` | 比較（不等号は `<>`） |
| `AND` / `OR` | かつ / または |
| `IN (...)` | リストのどれかに一致 |
| `BETWEEN a AND b` | a 以上 b 以下（両端含む） |
| `LIKE 'A%'` | 「A」で始まる（`%`=任意長、`_`=1文字） |
| `IS NULL` / `IS NOT NULL` | 値が空かどうか（`= NULL` は使えない） |

> 💡 NULL（値なし）は特別。`age = NULL` ではなく **`age IS NULL`** と書きます。比較演算子では NULL は拾えません。

---

## 2-3. ORDER BY ── 並べ替える

```sql
-- 年齢の高い順（降順 DESC）。昇順は ASC（省略時は昇順）
SELECT customer_id, age FROM customers ORDER BY age DESC LIMIT 10;

-- 複数キー：まず都道府県名順、同じ県内では年齢の高い順
SELECT prefecture, age FROM customers ORDER BY prefecture ASC, age DESC;
```

- `ORDER BY 列 DESC` で降順、`ASC`（既定）で昇順。
- `LIMIT` と組み合わせると「TOP N」が作れます（例：高額顧客 TOP10）。

---

## 2-4. 集計関数 ── COUNT / SUM / AVG / MIN / MAX

1行ずつではなく、**集合全体を1つの数字に要約**します。

```sql
SELECT
  COUNT(*)        AS 行数,        -- 行の数
  COUNT(DISTINCT prefecture) AS 県数, -- 重複を除いた数
  AVG(age)        AS 平均年齢,
  MIN(age)        AS 最年少,
  MAX(age)        AS 最年長
FROM customers;
```

- `COUNT(*)` は行数、`COUNT(列)` は **NULL を除いた**その列の件数、`COUNT(DISTINCT 列)` は種類数。
- `SUM` 合計 / `AVG` 平均 / `MIN` 最小 / `MAX` 最大。
- 集計関数は**整数同士の割り算に注意**。SQLite では `5/2 = 2`（切り捨て）。平均比などを出すときは `* 1.0` を掛けて小数にします（例：`SUM(...) * 1.0 / COUNT(...)`）。

---

## 2-5. GROUP BY / HAVING ── カテゴリ別に集計する

`GROUP BY` は「**同じ値の行をまとめて**、グループごとに集計関数を計算する」もの。分析で最も使う構文です。

```sql
-- カテゴリ別の商品数
SELECT category, COUNT(*) AS 商品数
FROM products
GROUP BY category
ORDER BY 商品数 DESC;

-- HAVING：集計した「後」の結果を絞り込む（商品数が10以上のカテゴリだけ）
SELECT category, COUNT(*) AS 商品数
FROM products
GROUP BY category
HAVING COUNT(*) >= 10;
```

- `GROUP BY 列` … その列の値ごとにグループ化。`SELECT` に書ける非集計列は、原則 `GROUP BY` した列だけ。
- **`WHERE` と `HAVING` の違い**：
  - `WHERE` … グループ化する**前**の、**個々の行**に対する絞り込み。
  - `HAVING` … グループ化した**後**の、**集計結果**に対する絞り込み（`COUNT(*) >= 10` など集計関数が使える）。

> 💡 「completed の注文だけ集計したい」は `WHERE status='completed'`（行の絞り込み）。「合計売上が100万円以上のカテゴリだけ」は `HAVING SUM(...) >= 1000000`（集計後の絞り込み）。場所を間違えるとエラーになるか結果が変わります。

---

## 2-6. SQL の実行順序 ── 書く順と動く順は違う

SQL は書いた順（SELECT が先頭）ではなく、**内部では次の順で評価**されます。これを知ると HAVING や別名の挙動が腑に落ちます。

```
FROM   → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
（取る）  （行で絞る） （まとめる）  （集計で絞る） （列を選ぶ） （並べる）  （件数制限）
```

- だから `WHERE` では「まだ計算されていない」集計関数や `SELECT` の別名は使えない。
- 逆に `ORDER BY` は `SELECT` の**後**なので、`SELECT` で付けた別名で並べ替えできる（多くのDBで可）。

> 🧭 つまずいたら「いま SQL はどの段階にいる？」と実行順序を思い出すと、エラーの大半は説明がつきます。

---

## 2-7. JOIN ── テーブルをつなぐ

分析の本番。`orders`・`order_items`・`products`・`customers` を結合して「誰が・何を・いくら買ったか」を1つの表にします。

```sql
-- 売上 = order_items.quantity × unit_price を、completed の注文で集計
-- カテゴリ別売上ランキング
SELECT p.category, SUM(oi.quantity * oi.unit_price) AS 売上
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products    p  ON oi.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY p.category
ORDER BY 売上 DESC;
```

- `JOIN ... ON 条件` で、**キーが一致する行同士**を横につなぐ。`o` `oi` `p` は**テーブル別名**（長い名前を省略し、どの表の列か明示するため）。
- **INNER JOIN（既定の `JOIN`）**：両方のテーブルに**一致がある行だけ**残る。
- **LEFT JOIN**：左テーブルの行は**全部残し**、右に一致が無ければ右側の列は NULL になる。

```sql
-- LEFT JOIN：一度も売れていない商品も「売上0」で出したいとき
SELECT p.product_name, COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS 売上
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id;
```

> 💡 **INNER と LEFT の使い分け**：「売れた商品だけ」見たいなら INNER。「売れていない商品も漏らさず一覧にしたい」なら LEFT。LEFT で右が NULL の行は「一致が無かった」サイン。`COALESCE(x, 0)` で NULL を0に置き換えられます。

---

## 2-8. CASE 式 ── 条件で値を作り分ける

`CASE` は「もし〜なら〜」を SQL の中で書く仕組み。年齢を年代に変換するなど、**集計の前にカテゴリを作る**のに使います。

```sql
-- 年代別の顧客数
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
ORDER BY 年代;
```

- `WHEN 条件 THEN 値` を上から順に評価し、最初に当てはまったものを返す。どれにも合わなければ `ELSE`。
- GROUP BY と組み合わせると、**連続値（年齢）をビン（年代）にまとめた集計**ができます。

---

## 2-9. 日付関数 strftime ── 月次で集計する

SQLite では日付は文字列（`'2024-12-31'`）。`strftime(書式, 日付)` で年や月を取り出せます。

```sql
-- 月次売上の推移（completed のみ）
SELECT
  strftime('%Y-%m', o.order_date) AS 月,
  SUM(oi.quantity * oi.unit_price) AS 売上
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY 月
ORDER BY 月;
```

- `strftime('%Y-%m', 日付)` → `'2024-12'` のような「年-月」。これで GROUP BY すれば月次集計。
- 主な書式：`%Y`=西暦4桁、`%m`=月、`%d`=日、`%Y-%m`=年月。

> 💡 「月ごとの推移」は **`strftime('%Y-%m', ...)` で月の文字列を作って GROUP BY** が定石。年で見たいなら `%Y` に変えるだけ。

---

## 2-10. サブクエリ ── クエリの中にクエリ

クエリの結果を、別のクエリの**条件**や**仮想テーブル**として使えます。

```sql
-- WHERE 内サブクエリ：全体平均より高額な商品
SELECT product_name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);

-- FROM 内サブクエリ：いったん顧客別売上を作り、その平均を出す
SELECT AVG(顧客売上) AS 顧客あたり平均売上
FROM (
  SELECT c.customer_id, SUM(oi.quantity * oi.unit_price) AS 顧客売上
  FROM customers c
  JOIN orders o      ON c.customer_id = o.customer_id
  JOIN order_items oi ON o.order_id = oi.order_id
  WHERE o.status = 'completed'
  GROUP BY c.customer_id
);
```

- **WHERE 内**：単一の値（平均など）を返すサブクエリを比較条件に使う。
- **FROM 内**：サブクエリの結果を「テーブルのように」扱い、その上でさらに集計する（**集計の二段重ね**）。

---

## 2-11. ウィンドウ関数（中級）── 行を残したまま集計

`GROUP BY` は行をまとめてしまいますが、**ウィンドウ関数は個々の行を残したまま、その行に「グループ内の順位」や「累計」を添える**ことができます。

```sql
-- カテゴリ内の売上ランキング：各カテゴリで売上TOPの商品はどれ？
SELECT
  category, product_name, 売上,
  ROW_NUMBER() OVER (PARTITION BY category ORDER BY 売上 DESC) AS カテゴリ内順位
FROM (
  SELECT p.category, p.product_name, SUM(oi.quantity * oi.unit_price) AS 売上
  FROM orders o
  JOIN order_items oi ON o.order_id = oi.order_id
  JOIN products    p  ON oi.product_id = p.product_id
  WHERE o.status = 'completed'
  GROUP BY p.product_id
);

-- SUM() OVER：月次売上の累計（running total）
SELECT
  月, 売上,
  SUM(売上) OVER (ORDER BY 月) AS 累計売上
FROM (
  SELECT strftime('%Y-%m', o.order_date) AS 月, SUM(oi.quantity * oi.unit_price) AS 売上
  FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
  WHERE o.status = 'completed'
  GROUP BY 月
);
```

- `関数() OVER (PARTITION BY ... ORDER BY ...)` … `PARTITION BY` でグループを区切り（省略時は全体）、`ORDER BY` でその中の順序を決める。
- `ROW_NUMBER()` … グループ内の連番（1,2,3…）。「カテゴリ別TOP3」などに。
- `SUM() OVER (ORDER BY ...)` … 先頭からの**累計**。
- `GROUP BY` との違い：GROUP BY は行が**潰れる**、ウィンドウ関数は行が**残る**（明細＋集計を同時に見たいとき）。

> 💡 ウィンドウ関数は SQLite 3.25 以降で使えます（本講座の環境は対応済み）。「明細を見せつつ、その横に順位や累計を出したい」ときの強力な道具です。

---

## 2-12. まとめ

- SQL は**集合への宣言的な操作**。「何が欲しいか」を書く。
- 実行順序 **FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT** を意識するとエラーが読める。
- 売上は必ず **`quantity × unit_price` の SUM、`status='completed'` のみ**（本講座の規約）。
- 絞り込みは `WHERE`（行）と `HAVING`（集計後）を使い分ける。
- 結合は INNER（一致のみ）と LEFT（左を全部残す）を目的で選ぶ。
- 中級では CASE・strftime・サブクエリ・ウィンドウ関数で表現力が一気に広がる。

次は、同じ集計を **Python の pandas** で行います。SQL の GROUP BY が pandas の `groupby` にどう対応するか、対比しながら学ぶと両方が深まります。

👉 [03. pandas 基礎](03_pandas_basics.md) へ

> 演習では「コードが動いた」で終わらせず、**結果から何が言えるか**（例：売上が一番大きいカテゴリはどこで、なぜか）を一言メモする癖をつけましょう。
