import yaml
import os
import random
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime
import tweepy
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# パス定義
SCRIPT_DIR = Path(__file__).resolve().parent
LOGS_DIR = SCRIPT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class PamichikiBot:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = SCRIPT_DIR / 'prompts' / 'pamichiki_identity.yaml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # API認証
            self.tw_client = tweepy.Client(
                bearer_token=os.getenv('X_BEARER_TOKEN'),
                consumer_key=os.getenv('X_API_KEY'),
                consumer_secret=os.getenv('X_API_SECRET'),
                access_token=os.getenv('X_ACCESS_TOKEN'),
                access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET')
            )
            auth = tweepy.OAuth1UserHandler(
                os.getenv('X_API_KEY'), os.getenv('X_API_SECRET'),
                os.getenv('X_ACCESS_TOKEN'), os.getenv('X_ACCESS_TOKEN_SECRET')
            )
            self.tw_api_v1 = tweepy.API(auth)
            logging.info("【システム】X API 認証完了でやんす。")
        except Exception as e:
            logging.error(f"【エラー】初期化失敗: {e}")
            raise

    def post_text(self, text, media_path=None):
        """外部から受け取ったテキストを投稿しやす（汎用メソッド）[cite: 4]"""
        try:
            media_ids = None
            if media_path and os.path.exists(media_path):
                media = self.tw_api_v1.media_upload(media_path)
                media_ids = [media.media_id]
            
            self.tw_client.create_tweet(text=text, media_ids=media_ids)
            logging.info(f"【投稿成功】内容: {text[:30]}...")
            return True
        except Exception as e:
            logging.error(f"【投稿失敗】{e}")
            return False

    def select_topic_and_generate(self):
        """（従来の自動運転用）ネタ選定と生成[cite: 4]"""
        # ... (中略: 以前の select_topic, run_openclaw_agent 等のロジック) ...
        # ※ ここは以前の run() 内のロジックを整理して格納しやす
        pass

    def run_routine(self):
        """（従来の自動運転用）定時ポスト実行[cite: 4]"""
        logging.info("--- 定時ポストルーチン開始 ---")
        # 以前の run() メソッドの中身を実行
        pass

# 直接実行された時だけ動くようにしやす[cite: 4]
if __name__ == "__main__":
    # 🌟 直接実行された時だけ、自分専用のログを吐くようにしやす
    logging.basicConfig(
        filename=LOGS_DIR / f'x_bot_{datetime.now().strftime("%Y%m")}.log',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        encoding='utf-8'
    )
    bot = PamichikiBot()
    bot.run_routine()