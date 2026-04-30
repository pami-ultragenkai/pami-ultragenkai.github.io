import uuid
import os
import yaml
import logging
import subprocess
import time
import re
from datetime import datetime, timedelta
from pathlib import Path

# --- 1. パスとログの初期設定 ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
POSTS_DIR = BASE_DIR / "content" / "posts"
LOGS_DIR = SCRIPT_DIR / "logs"
CONFIG_PATH = SCRIPT_DIR / "prompts" / "pamichiki_identity.yaml"

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

    def build_instruction(self, topic):
        """人格設定に基づいた執筆指示（プロンプト）を構成しやす"""
        char = self.config['character']
        profile = "、".join(char['profile'])
        instruction = (
            f"あなたは以下の人格を持つキャラクターとしてブログを書いてください。\n"
            f"名前: {char['name']}\n"
            f"プロフィール: {profile}\n"
            f"口調: {char['style']['tone']}\n\n"
            f"【執筆ルール】\n"
            f"- テーマ: {topic}\n"
            f"- Markdown形式で出力してください。\n"
            f"- エンジニアとしての技術的視点と、{char['name']}らしい一生懸命さを出してください。"
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
        
        # 外で決めた filename を使用してパスを作成
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
            logging.error("【告知中断】PamichikiBot クラスが利用不可でやんす。")
            return False
            
        try:
            bot = PamichikiBot()
            # 旦那指定の固定文言スタイル
            message = (
                f"ぱみブログ更新🐹\n"
                f"今回は「{blog_title}」について投稿したのでみてね🤓🤞\n"
                f"URL：{blog_url}\n"
                f"#ブログ"
            )
            
            if bot.post_text(message):
                logging.info("【X告知: SUCCESS】告知ポストが完了しやした。")
                return True
            else:
                logging.error("【X告知: FAILED】ポストに失敗しやした。")
                return False
        except Exception as e:
            logging.error(f"【X告知: FATAL】内部エラー: {e}")
            return False

    def run(self, topic):
        """全プロセスの司令塔でやんす"""
        logging.info(f"--- [MISSION START] テーマ: {topic} ---")
        
        # 1. 執筆指示作成
        instruction = self.build_instruction(topic)
        
        # 2. 本文生成
        content = self.run_openclaw_agent(instruction)
        if not content:
            logging.error("【ミッション失敗】本文生成フェーズで脱落しやした。")
            return

        # 3. ファイル名（URLスラッグ）の生成[cite: 1]
        # 日本語URLを避け、日付と一意のIDで構成しやす
        today_str = datetime.now().strftime('%Y-%m-%d')
        unique_id = str(uuid.uuid4())[:8]
        slug = f"{today_str}-{unique_id}"
        filename = f"{slug}.md"
        
        # 4. URLの組み立て[cite: 1]
        base_url = "https://pami-ultragenkai.github.io"
        blog_url = f"{base_url}/posts/{slug}"

        # 5. MD化（生成したfilenameを渡す）[cite: 1]
        title = f"Report: {topic}"
        if self.create_markdown(title, content, filename):
            # 6. デプロイと告知
            if self.git_deploy():
                self.announce_on_x(title, blog_url)
                logging.info(f"--- [MISSION COMPLETE] 記事 '{title}' の全工程が完了しやした！ ---")
            else:
                logging.error("【ミッション中断】デプロイに失敗しやした。")
        else:
            logging.error("【ミッション中断】ファイル生成に失敗しやした。")

if __name__ == "__main__":
    engine = ArkitecEngine()
    engine.run("エンジニア2年目が挑むPython自動化の壁")