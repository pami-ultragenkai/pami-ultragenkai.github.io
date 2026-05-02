import uuid
import os
import yaml
import logging
import subprocess
import time
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

# --- 1. パスとログの初期設定 ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
POSTS_DIR = BASE_DIR / "content" / "posts"
LOGS_DIR = SCRIPT_DIR / "logs"
CONFIG_PATH = SCRIPT_DIR / "prompts" / "pamichiki_identity.yaml"
HISTORY_PATH = SCRIPT_DIR / "prompts" / "history.json" # 履歴ファイルの保存先

# フォルダ生成
POSTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ロギング開始
logging.basicConfig(
    filename=LOGS_DIR / f'blog_bot_{datetime.now().strftime("%Y%m")}.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

# --- 2. 外部モジュールの読み込み ---
try:
    from x_bot import PamichikiBot
    logging.info("【システム】x_bot 連携モジュールの読み込みに成功しやした。")
except ImportError:
    PamichikiBot = None
    logging.error("【警告】x_bot.py が見つからないため、告知機能はスキップされやす。")

class ArkitecEngine:
    def __init__(self):
        logging.info("=== [STATE: INIT] ARKITEC Engine 起動 ===")
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logging.info(f"【設定読込: SUCCESS】{CONFIG_PATH}")
        except Exception as e:
            logging.error(f"【設定読込: FAILED】{e}")
            raise

    def load_history(self):
        """履歴ファイルを読み込みやす"""
        if not HISTORY_PATH.exists():
            return []
        try:
            with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def save_history(self, title, topic, level):
        """今回の成果を履歴に刻みやす"""
        history = self.load_history()
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": title,
            "topic": topic,
            "level": level
        })
        with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
        logging.info(f"【履歴更新: SUCCESS】{title} (Lv: {level})")

    def build_instruction(self, topic, history, level):
        """学習履歴とレベルを加味した最強の指示書を作りやす"""
        char = self.config['character']
        profile = "、".join(char['profile'])
        
        # 過去のトピックを抽出
        past_titles = ", ".join([h['title'] for h in history]) if history else "なし"
        
        instruction = (
            f"あなたは以下の人格を持つキャラクターとしてブログを書いてください。\n"
            f"名前: {char['name']}\n"
            f"プロフィール: {profile}\n"
            f"口調: {char['style']['tone']}\n\n"
            f"【現在の学習レベル】\n"
            f"難易度: {level}\n"
            f"過去に執筆したタイトル: {past_titles}\n\n"
            f"【執筆ルール】\n"
            f"- テーマ: {topic}\n"
            f"- レベルに合わせて内容の専門性を調整してください。\n"
            f"- 過去の記事と内容が重複しないよう、新しい視点や一歩踏み込んだ技術解説を含めてください。\n"
            f"- Markdown形式で出力してください。"
        )
        return instruction

    def run_openclaw_agent(self, instruction):
        """OpenClawを使用して記事本文を生成しやす"""
        gw_proc = None
        try:
            logging.info("=== [STATE: OPENCLAW_START] Gateway起動プロセス ===")
            gw_proc = subprocess.Popen(
                ["powershell", "-Command", "openclaw gateway run"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(20) # 起動待機

            logging.info("=== [STATE: AGENT_RUN] エージェント執筆開始 ===")
            cmd = f'openclaw agent --agent main -m "{instruction}"'
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', shell=True)
            
            if result.returncode != 0:
                logging.error(f"【エージェント: FAILED】Code: {result.returncode}, Error: {result.stderr.strip()}")
                return None
            
            return result.stdout.strip()
        except Exception as e:
            logging.error(f"【OpenClaw: FATAL】{e}")
            return None
        finally:
            if gw_proc:
                subprocess.run(["powershell", "-Command", "Get-Process node | Where-Object { $_.CommandLine -match 'gateway' } | Stop-Process -Force"], shell=True)
                gw_proc.terminate()

    def create_markdown(self, title, body, filename):
        """生成された内容をHugo用のMDファイルとして保存しやす"""
        safe_now = datetime.now()
        timestamp = safe_now.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        filepath = POSTS_DIR / filename

        front_matter = (
            f'---\n'
            f'title: "{title}"\n'
            f'date: {timestamp}\n'
            f'showComments: true\n'
            f'draft: false\n'
            f'---\n\n'
        )
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(front_matter + body)
            logging.info(f"【MD生成: SUCCESS】{filename}")
            return True
        except Exception as e:
            logging.error(f"【MD生成: FAILED】{e}")
            return False

    def git_deploy(self):
        """GitHubへプッシュし、サイトを更新しやす"""
        logging.info("=== [STATE: GIT_DEPLOY] デプロイ開始 ===")
        try:
            os.chdir(BASE_DIR)
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Auto Blog Post by ARKITEC Engine"], check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
            logging.info("【Gitデプロイ: SUCCESS】")
            return True
        except Exception as e:
            logging.error(f"【Gitデプロイ: FAILED】{e}")
            return False

    def announce_on_x(self, blog_title, blog_url):
        """x_botの汎用関数を使い、ブログ公開を告知しやす"""
        logging.info("=== [STATE: X_ANNOUNCE] X告知フェーズ ===")
        if not PamichikiBot:
            return False
            
        try:
            bot = PamichikiBot()
            message = (
                f"ぱみブログ更新🐹\n"
                f"今回は「{blog_title}」について投稿したのでみてね🤓🤞\n"
                f"URL：{blog_url}\n"
                f"#ブログ"
            )
            return bot.post_text(message)
        except Exception as e:
            logging.error(f"【X告知: FATAL】{e}")
            return False

    def run(self, topic, level="初級"):
        """ミッション遂行！"""
        logging.info(f"--- [MISSION START] テーマ: {topic} (Lv: {level}) ---")
        
        # 1. 履歴を読み込む[cite: 1]
        history = self.load_history()
        
        # 2. 履歴とレベルを踏まえた指示作成
        instruction = self.build_instruction(topic, history, level)
        
        # 3. 本文生成
        content = self.run_openclaw_agent(instruction)
        if not content:
            return

        # 4. ファイル名（URLスラッグ）の生成
        today_str = datetime.now().strftime('%Y-%m-%d')
        unique_id = str(uuid.uuid4())[:8]
        slug = f"{today_str}-{unique_id}"
        filename = f"{slug}.md"
        
        # 5. URLの組み立て（.htmlを付与）
        base_url = "https://pami-ultragenkai.github.io"
        blog_url = f"{base_url}/posts/{slug}.html"

        # 6. MD化
        title = f"Report: {topic}"
        
        if self.create_markdown(title, content, filename):
            # 7. デプロイ
            if self.git_deploy():
                # 8. 成功したら履歴に保存！[cite: 1]
                self.save_history(title, topic, level)
                
                # 9. X告知（デバッグ中はコメントアウト推奨）
                logging.info("デバック：X投稿停止中")
                # self.announce_on_x(title, blog_url)
                logging.info(f"--- [MISSION COMPLETE] 記事完了！ ---")

if __name__ == "__main__":
    engine = ArkitecEngine()
    # 旦那、ここを "中級" や "上級" に変えてみてくだせえ！
    engine.run("エンジニア2年目が挑むPython自動化の壁", level="初級")