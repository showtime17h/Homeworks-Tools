import os
import requests
import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- 設定（GitHubのSecretsとGASのURL） ---
GAS_URL = "https://script.google.com/macros/s/AKfycbwO48RpNBqGm6q2Tj7tBQhVM3lCZFVxBiMm8I19K6WxCiZYWfLi882kqocW7relVAIK/exec"
LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
S_ID = "80009253"
S_PW = "kanae526"

def check_if_completed():
    """GASに今日の宿題が終わっているか確認する"""
    try:
        # GASのdoGetが呼ばれる
        res = requests.get(GAS_URL, timeout=10)
        return res.json().get("completed", False)
    except Exception as e:
        print(f"GAS確認エラー: {e}")
        return False

def send_line_with_button(message):
    """完了ボタン付きでLINEを送る"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{
            "type": "text",
            "text": message,
            "quickReply": {
                "items": [{
                    "type": "action",
                    "action": {
                        "type": "message",
                        "label": "宿題完了！✅",
                        "text": "宿題終わったよ！"
                    }
                }]
            }
        }]
    }
    requests.post(url, headers=headers, json=data)

def get_sananet_data():
    """サナネットから最新4件の宿題を取得する"""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.sana-net.jp/snet/")
        
        # ログイン
        page.fill('#LoginForm_login_id', S_ID)
        page.fill('input[name="LoginForm[password]"]', S_PW)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        try:
            # 宿題ページへ移動
            page.get_by_role("link", name="戸田教室中1宿題").click()
            page.wait_for_timeout(3000)
            all_text = page.locator("body").inner_text()
            
            # 「■」で分割
            parts = all_text.split("■")[1:]
            for part in parts[:4]:
                date_match = re.search(r'(\d{1,2}/\d{1,2})', part)
                if date_match:
                    date_str = date_match.group(1)
                    # 今年の日付として解釈
                    hw_date = datetime.strptime(f"{datetime.now().year}/{date_str}", "%Y/%m/%d")
                    content = "■" + part.split("PAGE TOP")[0].strip()
                    results.append((hw_date, content))
        except Exception as e:
            print(f"サナネット取得失敗: {e}")
        finally:
            browser.close()
    return results

if __name__ == "__main__":
    print("実行開始...")
    
    # 1. すでに完了ボタンを押したか確認
    if check_if_completed():
        print("今日はすでに完了報告済みのため、通知をスキップします。")
    else:
        # 2. 宿題リストを取得
        homework_list = get_sananet_data()
        today = datetime.now().date()
        any_sent = False
        
        for hw_date, hw_content in homework_list:
            diff = (today - hw_date.date()).days
            # 5日後または7日後の場合のみ送信
            if diff in [5, 7]:
                print(f"{hw_date.strftime('%m/%d')}の宿題（{diff}日後）を通知します。")
                send_line_with_button(f"【{diff}日後リマインド】\n{hw_content}")
                any_sent = True
        
        if not any_sent:
            print("本日は通知対象の宿題がありませんでした。")
