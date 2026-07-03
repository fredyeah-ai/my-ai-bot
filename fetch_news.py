import os
import requests
import xml.etree.ElementTree as ET

def get_summary(title, api_key):
    """呼叫 Cohere API 使用 command-r 模型生成 50 字內廣東話簡介"""
    if not api_key:
        return "（未配置 AI 金鑰，無法提供簡介）"
        
    # 💡 呼叫高穩定性的 Cohere 官方接口（走全球一線 CDN，絕不出現 DNS 錯誤）
    url = "https://api.cohere.com/v1/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"請根據以下新聞標題，用50字內、親切流暢嘅香港廣東話（口語化）簡介呢則新聞大概講咩，唔好講廢話：\n【{title}】"
    
    # 💡 使用 Cohere 旗艦級 command-r 模型，對廣東話理解極佳
    payload = {
        "model": "command-r",
        "message": prompt
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            summary = data['text'].strip()
            # 清理可能生成的引號
            return summary.replace('"', '').replace('「', '').replace('」', '')
        
        print(f"⚠️ Cohere API 拒絕連線！狀態碼: {response.status_code}")
        print(f"⚠️ 錯誤原因: {response.text}")
        return "（簡介生成失敗）"
    except Exception as e:
        return f"（暫無簡介: {e}）"

def fetch_and_send():
    bot_token = os.environ.get('TG_BOT_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    ai_key = os.environ.get('GEMINI_API_KEY') # 這裡面現在裝的是 Cohere 的 Token

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

        message = "🤖 <b>今日 AI 科技頭條推送 (Cohere 終極穩定版)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, item in enumerate(items, 1):
            title = item.find('title').text
            link = item.find('link').text
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            
            print(f"正在為第 {i} 條新聞生成 AI 簡介...")
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
