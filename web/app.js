/* データアナリスト養成講座 — ブラウザ実行版（Pyodide） */
"use strict";

const PYODIDE_VERSION = "v0.26.4";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/${PYODIDE_VERSION}/full/`;
const CORE_PACKAGES = ["numpy", "pandas", "matplotlib", "scipy"];

let pyodide = null;
let lessons = [];
let activeLessonId = null;

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
};

/* ---- 図を出力エリアに差し込むためのフック（Python から呼ばれる） ---- */
window._daImgTarget = null;
globalThis._daEmitImage = function (b64) {
  if (!window._daImgTarget) return;
  const img = new Image();
  img.src = "data:image/png;base64," + b64;
  window._daImgTarget.appendChild(img);
};

/* ====================================================================== */
/* 初期化                                                                  */
/* ====================================================================== */
async function init() {
  const loaderMsg = $("#loaderMsg");
  const setMsg = (m) => (loaderMsg.textContent = m);

  try {
    setMsg("Python実行環境を読み込み中…（初回は30秒ほど）");
    pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
    window.pyodide = pyodide; // デバッグ・上級者用に公開

    setMsg("ライブラリを読み込み中…（pandas / matplotlib / scipy）");
    await pyodide.loadPackage(CORE_PACKAGES);

    // sqlite3（SQLモジュール用。Pyodideでは別パッケージ）
    try {
      await pyodide.loadPackage("sqlite3");
    } catch (e) {
      console.warn("sqlite3 の読み込みに失敗:", e);
    }

    // seaborn（無ければ micropip で取得）
    try {
      await pyodide.loadPackage("seaborn");
    } catch (_e) {
      await pyodide.loadPackage("micropip");
      const micropip = pyodide.pyimport("micropip");
      await micropip.install("seaborn");
    }

    // ランタイム（セル実行ヘルパー）を読み込む
    setMsg("実行ヘルパーを初期化中…");
    const runtimeSrc = await (await fetch("runtime.py")).text();
    pyodide.runPython(runtimeSrc);

    // 日本語フォント（同梱TTFを matplotlib に登録）
    setMsg("日本語フォントを準備中…");
    await loadJapaneseFont();

    // データをPyodideのファイルシステムにロード
    setMsg("サンプルデータを読み込み中…");
    await loadData();

    // レッスンを読み込む
    setMsg("教材を読み込み中…");
    lessons = await (await fetch("lessons.json")).json();
    buildSidebar();

    // 最初のレッスンを表示
    const startId = location.hash.replace("#", "") || lessons[0].id;
    openLesson(lessons.some((l) => l.id === startId) ? startId : lessons[0].id);

    $("#loader").classList.add("hidden");
  } catch (err) {
    setMsg("読み込みに失敗しました 😢");
    $("#loaderSub").textContent = String(err);
    console.error(err);
  }
}

/* 日本語フォントを matplotlib に登録し、既定フォントにする */
async function loadJapaneseFont() {
  try {
    const buf = await (await fetch("fonts/jp.ttf")).arrayBuffer();
    pyodide.FS.mkdirTree("/home/pyodide/fonts");
    pyodide.FS.writeFile("/home/pyodide/fonts/jp.ttf", new Uint8Array(buf));
    pyodide.runPython(`
import matplotlib.font_manager as _fm
from matplotlib import rcParams as _rc
_fm.fontManager.addfont("/home/pyodide/fonts/jp.ttf")
_JP_FONT = _fm.FontProperties(fname="/home/pyodide/fonts/jp.ttf").get_name()
_rc["font.family"] = _JP_FONT
_rc["font.sans-serif"] = [_JP_FONT] + list(_rc["font.sans-serif"])
_rc["axes.unicode_minus"] = False
# ノートブックの setup が候補フォントを探す処理でも確実にヒットするよう、
# 代表的な日本語フォント名のエイリアスとして同じ実体ファイルを登録しておく。
import matplotlib
for _alias in ["Meiryo", "Yu Gothic", "IPAexGothic", "Noto Sans CJK JP", "MS Gothic"]:
    try:
        _e = _fm.FontEntry(fname="/home/pyodide/fonts/jp.ttf", name=_alias)
        _fm.fontManager.ttflist.append(_e)
    except Exception:
        pass
print("日本語フォント:", _JP_FONT)
`);
  } catch (e) {
    console.warn("日本語フォントの読み込みに失敗（グラフの日本語が□になる可能性）:", e);
  }
}

/* データファイルを /home/pyodide/data/ に書き込む */
async function loadData() {
  const manifest = await (await fetch("data_manifest.json")).json();
  const FS = pyodide.FS;
  for (const item of manifest) {
    const parts = item.path.split("/");
    const dir = "/home/pyodide/data" + (parts.length > 1 ? "/" + parts.slice(0, -1).join("/") : "");
    try { FS.mkdirTree(dir); } catch (_e) {}
    const dest = "/home/pyodide/data/" + item.path;
    const res = await fetch("data/" + item.path);
    if (item.binary) {
      const buf = await res.arrayBuffer();
      FS.writeFile(dest, new Uint8Array(buf));
    } else {
      const txt = await res.text();
      FS.writeFile(dest, txt);
    }
  }
}

/* ====================================================================== */
/* サイドバー                                                              */
/* ====================================================================== */
function buildSidebar() {
  const nav = $("#sidebar");
  nav.innerHTML = "";

  const readLabel = el("div", "group-label");
  readLabel.textContent = "はじめに（読み物）";
  nav.appendChild(readLabel);

  let exAdded = false;
  for (const lesson of lessons) {
    if (!lesson.reading && !exAdded) {
      const exLabel = el("div", "group-label");
      exLabel.textContent = "演習（コードを実行）";
      nav.appendChild(exLabel);
      exAdded = true;
    }
    const btn = el("button", "lesson");
    btn.dataset.id = lesson.id;
    btn.innerHTML =
      escapeHtml(lesson.title) +
      (lesson.reading ? '<span class="tag">📖</span>' : '<span class="tag">▶</span>');
    btn.addEventListener("click", () => {
      openLesson(lesson.id);
      closeSidebarMobile();
    });
    nav.appendChild(btn);
  }
}

function highlightSidebar() {
  document.querySelectorAll("nav.sidebar button.lesson").forEach((b) => {
    b.classList.toggle("active", b.dataset.id === activeLessonId);
  });
}

/* ====================================================================== */
/* レッスン表示                                                            */
/* ====================================================================== */
function openLesson(id) {
  const lesson = lessons.find((l) => l.id === id);
  if (!lesson) return;
  activeLessonId = id;
  location.hash = id;
  highlightSidebar();

  // 名前空間をリセット（前のレッスンの変数を引き継がない）
  if (pyodide) {
    try { pyodide.runPython("da_reset_namespace()"); } catch (_e) {}
  }

  const main = $("#content");
  main.innerHTML = "";
  main.scrollTop = 0;
  window.scrollTo(0, 0);

  // 演習レッスンには「全部実行」バー
  if (!lesson.reading) {
    const bar = el("div", "lesson-bar");
    const runAllBtn = el("button");
    runAllBtn.textContent = "▶ このレッスンを上から全部実行";
    runAllBtn.addEventListener("click", () => runAll(main, runAllBtn));
    const hint = el("span", "hint");
    hint.textContent = "※ コードセルは上から順に実行してください（変数を引き継ぎます）。セルは自由に書き換えてOK。";
    bar.appendChild(runAllBtn);
    bar.appendChild(hint);
    main.appendChild(bar);
  }

  for (const cell of lesson.cells) {
    if (cell.type === "markdown") {
      const div = el("div", "md");
      div.innerHTML = marked.parse(cell.source);
      main.appendChild(div);
    } else {
      main.appendChild(buildCodeCell(cell.source));
    }
  }
}

function buildCodeCell(source) {
  const wrap = el("div", "cell");

  const toolbar = el("div", "cell-toolbar");
  const label = el("span", "label");
  label.textContent = "Python";
  const spacer = el("span", "spacer");
  const resetBtn = el("button", "reset");
  resetBtn.textContent = "リセット";
  const runBtn = el("button", "run");
  runBtn.textContent = "▶ 実行";
  toolbar.append(label, spacer, resetBtn, runBtn);

  const ta = el("textarea", "code");
  ta.value = source;
  ta.spellcheck = false;
  ta.rows = Math.min(Math.max(source.split("\n").length, 2), 26);
  autoSize(ta);
  ta.addEventListener("input", () => autoSize(ta));
  ta.addEventListener("keydown", (e) => handleTab(e, ta));

  const output = el("div", "output");

  resetBtn.addEventListener("click", () => {
    ta.value = source;
    autoSize(ta);
    output.innerHTML = "";
  });
  runBtn.addEventListener("click", () => runCell(ta, output, runBtn));

  wrap.append(toolbar, ta, output);
  return wrap;
}

/* ====================================================================== */
/* セル実行                                                                */
/* ====================================================================== */
async function runCell(ta, output, btn) {
  if (!pyodide) return;
  btn.disabled = true;
  const prev = btn.textContent;
  btn.textContent = "実行中…";
  output.innerHTML = "";
  window._daImgTarget = output;
  try {
    pyodide.globals.set("_cell_src", ta.value);
    const jsonStr = await pyodide.runPythonAsync("da_run_cell_json(_cell_src)");
    const res = JSON.parse(jsonStr);

    if (res.stdout) {
      const pre = el("pre");
      pre.textContent = res.stdout;
      output.appendChild(pre);
    }
    if (res.html) {
      const div = el("div");
      div.innerHTML = res.html;
      output.appendChild(div);
    }
    if (res.text) {
      const pre = el("pre");
      pre.textContent = res.text;
      output.appendChild(pre);
    }
    if (res.error) {
      const pre = el("pre", "err");
      pre.textContent = res.error;
      output.appendChild(pre);
    }
  } catch (err) {
    const pre = el("pre", "err");
    pre.textContent = String(err);
    output.appendChild(pre);
  } finally {
    window._daImgTarget = null;
    btn.disabled = false;
    btn.textContent = prev;
  }
}

async function runAll(main, btn) {
  btn.disabled = true;
  const prev = btn.textContent;
  const cells = [...main.querySelectorAll(".cell")];
  for (let i = 0; i < cells.length; i++) {
    btn.textContent = `実行中… (${i + 1}/${cells.length})`;
    const ta = cells[i].querySelector("textarea.code");
    const out = cells[i].querySelector(".output");
    const runBtn = cells[i].querySelector("button.run");
    await runCell(ta, out, runBtn);
  }
  btn.textContent = prev;
  btn.disabled = false;
}

/* ====================================================================== */
/* ユーティリティ                                                          */
/* ====================================================================== */
function autoSize(ta) {
  ta.style.height = "auto";
  ta.style.height = Math.min(ta.scrollHeight + 4, 640) + "px";
}

function handleTab(e, ta) {
  if (e.key === "Tab") {
    e.preventDefault();
    const s = ta.selectionStart, en = ta.selectionEnd;
    ta.value = ta.value.slice(0, s) + "    " + ta.value.slice(en);
    ta.selectionStart = ta.selectionEnd = s + 4;
  }
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* モバイルのサイドバー開閉 */
function toggleSidebar() {
  $("#sidebar").classList.toggle("open");
  $("#backdrop").classList.toggle("show");
}
function closeSidebarMobile() {
  $("#sidebar").classList.remove("open");
  $("#backdrop").classList.remove("show");
}

window.addEventListener("DOMContentLoaded", () => {
  marked.setOptions({ gfm: true, breaks: false });
  $("#menuBtn").addEventListener("click", toggleSidebar);
  $("#backdrop").addEventListener("click", closeSidebarMobile);
  init();
});
