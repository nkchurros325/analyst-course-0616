"""
軽量HTML学習サイト（web/）をローカルで配信する簡易サーバー。

キャッシュ無効化ヘッダを付けるので、ファイルを編集したらブラウザの
リロードだけで最新版が反映されます（開発・動作確認向け）。

使い方:
    python scripts/serve.py            # http://127.0.0.1:8766 で配信
    python scripts/serve.py 9000       # ポート指定
"""

import http.server
import os
import socketserver
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.normpath(os.path.join(HERE, "..", "web"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8766


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # 静かに


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"配信中: http://127.0.0.1:{PORT}/  (Ctrl+C で停止)")
        print(f"ディレクトリ: {WEB_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n停止しました。")


if __name__ == "__main__":
    main()
