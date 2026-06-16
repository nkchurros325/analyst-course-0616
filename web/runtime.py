# ブラウザ内Python（Pyodide）で各コードセルを「Jupyterっぽく」実行するためのヘルパー。
# app.js から fetch して pyodide.runPython() で一度だけ読み込む。

import ast
import base64
import io
import sys
import traceback

import matplotlib
matplotlib.use("AGG")  # 図は自前でPNG化して表示する
import matplotlib.pyplot as plt  # noqa: E402

# レッスンごとの実行名前空間（セル間で変数を共有する）
_NS = {"__name__": "__main__"}


def da_reset_namespace():
    """レッスンを切り替えたときに名前空間をまっさらにする。"""
    global _NS
    _NS = {"__name__": "__main__"}
    plt.close("all")


def _emit_open_figures():
    """現在開いている matplotlib の図をPNG化して JS 側に渡す。"""
    import js  # Pyodide: JSのグローバルにアクセス
    for num in plt.get_fignums():
        fig = plt.figure(num)
        buf = io.BytesIO()
        try:
            fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        except Exception:
            continue
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("ascii")
        js._daEmitImage(b64)
    plt.close("all")


# plt.show() を「図を取り込む」動作に差し替える（ノートブックは plt.show() を呼ぶ）
def _patched_show(*args, **kwargs):
    _emit_open_figures()


plt.show = _patched_show


def _display_value(val):
    """セル最後の式の値を、Jupyterのように見やすいHTML/テキストにする。"""
    if val is None:
        return None
    # pandas の DataFrame / Series はHTMLテーブルに
    try:
        import pandas as pd
        if isinstance(val, (pd.DataFrame, pd.Series)):
            if isinstance(val, pd.Series):
                val = val.to_frame()
            html = val.to_html(max_rows=30, max_cols=30, border=0)
            return {"kind": "html", "value": html}
    except Exception:
        pass
    # matplotlib の Figure / Axes は図として取り込み（表示はrun側で）→ テキストにはしない
    try:
        from matplotlib.figure import Figure
        from matplotlib.axes import Axes
        if isinstance(val, (Figure, Axes)):
            return None
    except Exception:
        pass
    return {"kind": "text", "value": repr(val)}


def da_run_cell(src):
    """1セル分のコードを実行し、{stdout, html, text, error} を返す。"""
    out = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = out
    sys.stderr = out
    result = {"stdout": "", "html": None, "text": None, "error": None}
    try:
        tree = ast.parse(src)
        last_expr = None
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last_expr = tree.body.pop()
        if tree.body:
            exec(compile(tree, "<cell>", "exec"), _NS)
        if last_expr is not None:
            val = eval(compile(ast.Expression(last_expr.value), "<cell>", "eval"), _NS)
            disp = _display_value(val)
            if disp and disp["kind"] == "html":
                result["html"] = disp["value"]
            elif disp and disp["kind"] == "text":
                result["text"] = disp["value"]
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        # show() を呼ばずに作った図も最後に取り込む
        try:
            _emit_open_figures()
        except Exception:
            pass
    result["stdout"] = out.getvalue()
    return result


def da_run_cell_json(src):
    """da_run_cell の結果を JSON 文字列で返す（JS側で扱いやすくするため）。"""
    import json
    return json.dumps(da_run_cell(src))
