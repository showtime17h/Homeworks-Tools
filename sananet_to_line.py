import os
import requests
import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- 設定 ---
GAS_URL = "ここに新しくデプロイしたGASのウェブアプリURLを貼る"
LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
S_ID = "80009253"
S_PW = "kanae526"

def check_if_completed():
    """GASに今日の宿題が終わっているか確認する"""
    try:
        res = requests.get(GAS_URL)
        return res.json().get("completed", False)
    except:
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

# --- (get_sananet_data 関数などは前回のものをそのまま使用) ---

if __name__ == "__main__":
    # 1. まず今日すでに「完了ボタン」を押したか確認
    if check_if_completed():
        print("今日はもう終わっているので何もしません。")
    else:
        # 2. 終わっていなければサナネットを確認
        homework_list = get_sananet_data()
        today = datetime.now().date()
        
        for hw_date, hw_content in homework_list:
            diff = (today - hw_date.date()).days
            if diff in [5, 7]:
                send_line_with_button(f"【{diff}日後リマインド】\n{hw_content}")
