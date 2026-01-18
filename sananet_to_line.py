import os
import requests
import json
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# --- 設定（GitHub環境変数または直接入力） ---
LINE_TOKEN = os.environ.get("LINE_TOKEN") or "あなたのトークン"
LINE_USER_ID = os.environ.get("LINE_USER_ID") or "あなたのユーザーID"
S_ID = "80009253"
S_PW = "kanae526"

def send_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, data=json.dumps(data))

def get_sananet_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.sana-net.jp/snet/")
        page.fill('#LoginForm_login_id', S_ID)
        page.fill('input[name="LoginForm[password]"]', S_PW)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        results = []
        try:
            page.get_by_role("link", name="戸田教室中1宿題").click()
            page.wait_for_timeout(3000)
            all_text = page.locator("body").inner_text()
            
            # 「■」で分割（最初の空要素を除外するため1番目から）
            parts = all_text.split("■")[1:]
            
            # 最新の4つだけをループで処理
            for part in parts[:4]:
                # 日付（例：1/17）を抽出
                date_match = re.search(r'(\d{1,2}/\d{1,2})', part)
                if date_match:
                    date_str = date_match.group(1)
                    hw_date = datetime.strptime(f"{datetime.now().year}/{date_str}", "%Y/%m/%d")
                    content = "■" + part.split("PAGE TOP")[0].strip()
                    results.append((hw_date, content))
                    
        except Exception as e:
            print(f"取得失敗: {e}")
        finally:
            browser.close()
    return results

if __name__ == "__main__":
    homework_list = get_sananet_data()
    
    today = datetime.now().date()
    any_sent = False

    for hw_date, hw_content in homework_list:
        diff = (today - hw_date.date()).days
        
        # 判定
        if diff == 5:
            send_line(f"【5日後リマインド】\n{hw_content}")
            any_sent = True
        elif diff == 7:
            send_line(f"【7日後(提出日前日)リマインド】\n{hw_content}")
            any_sent = True

    if not any_sent:
        print("今日が通知対象（5日後・7日後）の宿題はありませんでした。")
