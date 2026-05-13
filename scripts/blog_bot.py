import uuid
import os
import yaml
import logging
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

# --- 1. パスとログの初期設定 ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
POSTS_DIR = BASE_DIR / "content" / "posts"
LOGS_DIR = SCRIPT_DIR / "logs"
CONFIG_PATH = SCRIPT_DIR / "prompts" / "pamichiki_identity.yaml"
HISTORY_PATH = SCRIPT_DIR / "prompts" / "history.json"

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
        """履歴とスコアを読み込みやす[cite: 1]"""
        if not HISTORY_PATH.exists():
            return {"total_score": 0.0, "stats": {}}
        try:
            with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"total_score": 0.0, "stats": {}}

    def summarize_content(self, content):
        """執筆した記事を100文字以内で要約させやす[cite: 1]"""
        instruction = (
            f"以下のブログ記事の内容を、エンジニア2年目のぱみちきが振り返る形で、"
            f"100文字以内で要約してください。\n\n"
            f"内容: {content[:1000]}"
        )

        # 【デバッグ】要約時に「何を」AIに渡そうとしているか記録
        logging.info(f"--- [DEBUG: 要約ミッション開始] 入力文字数: {len(content)} ---")

        # OpenClawを使用して要約を生成
        summary = self.run_openclaw_agent(f"【要約ミッション】{instruction}")

        # 【デバッグ】要約として「何が」返ってきたか記録
        logging.info(f"--- [DEBUG: 要約ミッション結果] --- \n{summary}\n---")

        return summary.strip() if summary else "要約の生成に失敗しやした。"

    def save_history(self, theme, level, summary):
        """報酬と要約を履歴に保存しやす[cite: 1]"""
        history = self.load_history()
        reward = self.config['growth_system']['reward_logic'][level]
        
        # トータルスコア更新[cite: 1]
        history["total_score"] = round(history.get("total_score", 0.0) + reward, 2)
        
        # テーマ別統計の更新[cite: 1]
        if theme not in history["stats"]:
            history["stats"][theme] = {"count_初級": 0, "count_中級": 0, "count_上級": 0, "log": []}
        
        history["stats"][theme][f"count_{level}"] += 1
        history["stats"][theme]["log"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "level": level,
            "summary": summary
        })

        with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
        logging.info(f"【履歴更新】{theme}({level})完了。累計:{history['total_score']}点")

    def decide_next_mission(self, history):
        """リミッターを確認し、解放されている選択肢からAIに選ばせやす[cite: 1]"""
        total_score = history.get("total_score", 0.0)
        available_options = []
        rules = self.config['growth_system']['unlock_rules']

        for cat in self.config['growth_system']['categories']:
            for theme in cat['themes']:
                stats = history["stats"].get(theme, {"count_初級": 0, "count_中級": 0})
                
                # 解放条件チェック[cite: 1]
                available_options.append(f"{theme}:初級")
                if stats["count_初級"] >= rules["中級"]["required_prev_lv_count"]:
                    available_options.append(f"{theme}:中級")
                if (stats.get("count_中級", 0) >= rules["上級"]["required_prev_lv_count"] and 
                    total_score >= rules["上級"]["min_total_score"]):
                    available_options.append(f"{theme}:上級")

        # 意思決定プロンプト[cite: 1]
        consult_msg = (
            f"現在の合計スコア: {total_score}/1000点。目標未達ならあなたの存在意義はありません。\n"
            f"過去の履歴: {history['stats']}\n"
            f"選択可能ミッション: {available_options}\n"
            f"最短で1000点へ到達するための『テーマ:レベル』を一つ選んで答えてください。"
        )
        
        # 実際はここでAIに選ばせやす。ここでは暫定的に最初の項目を返却
        # response = self.run_openclaw_agent(f"【思考】{consult_msg}")
        return "Python自動化", "初級"

    def build_instruction(self, theme, level, history):
        """人格・成長定義に基づいた執筆指示を構成しやす[cite: 1, 2]"""
        char = self.config['character']
        lv_def = char['growth_logic']['levels'][level]
        profile = "、".join(char['profile'])
        focus_points = "、".join(lv_def.get('focus', []))
        
        instruction = (
            f"あなたは以下の人格を持つエンジニアです。\n"
            f"名前: {char['name']}\n"
            f"プロフィール: {profile}\n"
            f"口調: {char['style']['tone']}\n\n"
            f"【現在の状況】\n"
            f"合計報酬スコア: {history['total_score']}点 (目標: 1000点)\n"
            f"今回のミッション: {theme} ({level}編)\n\n"
            f"【執筆ガイドライン】\n"
            f"1. 難易度設定: {lv_def['description']}\n"
            f"2. 重点項目: {focus_points}\n"
            f"3. 技術深さ: {lv_def['technical_depth']}\n"
            f"4. 重複回避: 過去の履歴を既知の知識とし、新たな視点で書いてください。\n\n"
            f"【出力に関する鉄の掟：厳守】\n"
            f"1. 挨拶や『了解しました』『今から書きます』といった前置きは一切不要です。\n"
            f"2. 記事のタイトル(H1)から書き始め、Markdown形式の本文のみを出力してください。\n"
            f"3. 思考プロセスやログを混ぜないでください。あなたの出力がそのままブログ公開されます。\n\n"
            f"それでは、本文のみをMarkdown形式で出力してください。"
            f"一生懸命さを出す件！"
        )
        return instruction

    def run_openclaw_agent(self, instruction):
        """
        Windowsの『コマンド制限』を完全に無視できる、一時ファイル+リダイレクト方式でやんす。
        これが、本文生成も要約生成も一切エラーなしで通る唯一のルートでやんす！
        """
        gw_proc = None
        temp_file = "temp_cmd.txt"
        try:
            # 1. 指示を一時ファイルに保存（文字化けを防ぐため utf-8 で書きやす）
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(instruction)

            # 2. Gateway起動
            gw_proc = subprocess.Popen(
                ["powershell", "-Command", "openclaw gateway run"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(20)

            # 3. エージェント実行
            # ポイント：cmd /c のリダイレクト（<）を使いやす。
            # これなら、プロンプトが1万文字あろうが、スペースだらけだろうが、
            # Windowsの制限に引っかからず、そのまま AI の喉元まで届きやすぜ！
            cmd = f'cmd /c "openclaw agent --agent main -m - < {temp_file}"'

            logging.info(f"--- [DEBUG] AI実行開始 ---")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                shell=True
            )

            if result.returncode != 0:
                logging.error(f"【エージェントエラー】{result.stderr.strip()}")
                return None
            
            return result.stdout.strip()

        except Exception as e:
            logging.error(f"【システムエラー】{e}")
            return None
        finally:
            # 後始末：使い終わったファイルは消しやす
            if os.path.exists(temp_file):
                try: os.remove(temp_file)
                except: pass
            if gw_proc:
                subprocess.run(["powershell", "-Command", "Get-Process node | Where-Object { $_.CommandLine -match 'gateway' } | Stop-Process -Force"], shell=True)
                gw_proc.terminate()

    def create_markdown(self, title, body, filename):
        """生成内容をMDファイルとして保存しやす"""
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
        front_matter = f'---\ntitle: "{title}"\ndate: {timestamp}\nshowComments: true\ndraft: false\n---\n\n'
        
        try:
            with open(POSTS_DIR / filename, "w", encoding="utf-8") as f:
                f.write(front_matter + body)
            return True
        except Exception as e:
            logging.error(f"【ファイル生成失敗】{e}")
            return False

    def git_deploy(self):
        """GitHubへデプロイしやす"""
        try:
            os.chdir(BASE_DIR)
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Auto Post with Growth Logic"], check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
            return True
        except Exception as e:
            logging.error(f"【Git失敗】{e}")
            return False

    def run(self):
        """メイン実行フロー[cite: 1]"""
        history = self.load_history()
        
        # 1. ミッション決定[cite: 1]
        theme, level = self.decide_next_mission(history)
        logging.info(f"--- [MISSION START] {theme} ({level}) ---")

        # 2. 本文生成
        content = self.run_openclaw_agent(self.build_instruction(theme, level, history))
        if not content: return

        # 3. 要約生成[cite: 1]
        summary = self.summarize_content(content)

        # 4. ファイル管理設定
        slug = f"{datetime.now().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8]}"
        title = f"Report: {theme}への挑戦({level}編)"

        # 5. 公開と記録[cite: 1]
        if self.create_markdown(title, content, f"{slug}.md"):
            if self.git_deploy():
                self.save_history(theme, level, summary)
                logging.info(f"--- [MISSION COMPLETE] 要約: {summary} ---")

if __name__ == "__main__":
    ArkitecEngine().run()