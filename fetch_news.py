import os
import requests
import xml.etree.ElementTree as ET

def get_summary(title, api_key):
    """呼叫 Gemini API 根據標題生成 50 字內的廣東話簡介（除錯加強版）"""
    if not api_key:
        return "（未配置 AI 金鑰，無法提供簡介）"
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"請根據以下新聞標題，用50字內、親切流暢嘅香港廣東話（口語化）簡介呢則新聞大概講咩，唔好講廢話：\n【{title}】"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            summary = data['candidates'][0]['content']['parts'][0]['text'].strip()
            return summary.replace('"', '').replace('「', '').replace('」', '')
        
        # 💡 核心改動：如果失敗，直接將錯誤碼同原因印喺 GitHub Log 入面！
        print(f"⚠️ Google API 拒絕連線！狀態碼: {response.status_code}")
        print(f"⚠️ 錯誤原因: {response.text}")
        return "（簡介生成失敗）"
    except Exception as e:
        return f"（暫無簡介: {e}）"

def fetch_and_send():
    bot_token = os.environ.get('TG_BOT_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    gemini_key = os.environ.get('GEMINI_API_KEY')

    if not bot_token or not chat_id:
        print("錯誤：找不到環境變數")
        return

    rss_url = "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=zh-HK&gl=HK&ceid=HK:zh-hk"

    try:
        response = requests.get(rss_url, timeout=10)
        if response.status_code != 200: return
        
        root = ET.fromstring(response.content)
        # 💡 這裡原本是 [:3]，依家修改為 [:5] 抓取 5 條新聞！
        items = root.findall('.//item')[:5]
        
        if not items: return

        message = "🤖 <b>今日 AI 科技頭條推送 (Gemini 2.0 升級版)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, item in enumerate(items, 1):
            title = item.find('title').text
            link = item.find('link').text
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            
            print(f"正在為第 {i} 條新聞生成 AI 簡介...")
            # 💡 呼叫 Gemini 生成 50 字廣東話簡介
            summary = get_summary(title, gemini_key)
            
            # 組裝全新訊息格式：包含標題、📝AI簡介、🔗連結
            message += f"{i}️⃣ <b>{title}</b>\n📝 <i>{summary}</i>\n🔗 <a href='{link}'>點擊閱讀全文</a>\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n\n"

        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(tg_url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
        print("成功發送升級版訊息！")
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    fetch_and_send()
