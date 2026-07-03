import os
import time
import requests
import xml.etree.ElementTree as ET

def get_summary(title, api_key):
    """呼叫 Hugging Face API，內置 3 次網絡抽筋自動重試機制"""
    if not api_key:
        return "（未配置 AI 金鑰，無法提供簡介）"
        
    url = "https://api-inference.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"請根據以下新聞標題，用50字內、親切流暢嘅香港廣東話（口語化）簡介呢則新聞大概講咩，唔好講廢話：\n【{title}】"
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150
    }
    
    # 💡 應對 GitHub Actions 網絡抽筋的 3 次重試邏輯
    for attempt in range(3):
        try:
            print(f"正在為新聞嘗試生成 AI 簡介 (第 {attempt+1}/3 次嘗試)...")
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                summary = data['choices'][0]['message']['content'].strip()
                return summary.replace('"', '').replace('「', '').replace('」', '')
            
            print(f"⚠️ 伺服器回傳錯誤，狀態碼: {response.status_code}")
        except Exception as e:
            # 💡 捕捉包括 NameResolutionError 在內的所有網絡/DNS 異常
            print(f"⚠️ 網絡暫時性抽筋/DNS錯誤: {e}")
        
        # 如果不是最後一次嘗試，就等 2 秒再試
        if attempt < 2:
            print("⏳ 偵測到網絡異常，2 秒後自動重試...")
            time.sleep(2)
            
    return "（網絡連線不穩定，簡介生成失敗）"

def fetch_and_send():
    bot_token = os.environ.get('TG_BOT_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    ai_key = os.environ.get('GEMINI_API_KEY')

    if not bot_token or not chat_id:
        print("錯誤：找不到環境變數")
        return

    rss_url = "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=zh-HK&gl=HK&ceid=HK:zh-hk"

    try:
        response = requests.get(rss_url, timeout=10)
        if response.status_code != 200: return
        
        root = ET.fromstring(response.content)
        items = root.findall('.//item')[:5]
        
        if not items: return

        message = "🤖 <b>今日 AI 科技頭條推送 (Hugging Face 網絡加固版)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, item in enumerate(items, 1):
            title = item.find('title').text
            link = item.find('link').text
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            
            summary = get_summary(title, ai_key)
            
            message += f"{i}️⃣ <b>{title}</b>\n📝 <i>{summary}</i>\n🔗 <a href='{link}'>點擊閱讀全文</a>\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n\n"

        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(tg_url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
        print("成功發送升級版訊息！")
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    fetch_and_send()
