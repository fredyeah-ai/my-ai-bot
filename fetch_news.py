import os
import requests
import xml.etree.ElementTree as ET

def get_summary(title, api_key):
    """呼叫 OpenRouter 免費 AI 模型（具備多模型自動備援機制）"""
    if not api_key:
        return "（未配置 AI 金鑰，無法提供簡介）"
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"請根據以下新聞標題，用50字內、親切流暢嘅香港廣東話（口語化）簡介呢則新聞大概講咩，唔好講廢話：\n【{title}】"
    
    # 💡 終極備援名單：如果名單內某個模型被官方下架，程式會自動秒速跳去試下一個！
    # 這裡選用了目前 OpenRouter 最熱門、文字生成效果最好的 4 個免費大模型
    models_to_try = [
        "qwen/qwen-2.5-7b-instruct:free",        # 1. 阿里開源旗艦（廣東話同中文理解力極強）
        "meta-llama/llama-3.2-3b-instruct:free", # 2. Llama 輕量最新版
        "google/gemma-2-9b-it:free",             # 3. Google 官方開源版
        "mistralai/mistral-7b-instruct:free"     # 4. 歐洲最強開源模型
    ]
    
    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                summary = data['choices'][0]['message']['content'].strip()
                # 順利拿到簡介，直接中斷循環並回傳
                return summary.replace('"', '').replace('「', '').replace('」', '')
            else:
                print(f"ℹ️ 模型 {model} 暫時無法使用 (狀態碼 {response.status_code})，正在自動嘗試下一個備援模型...")
        except Exception as e:
            print(f"ℹ️ 呼叫 {model} 時發生異常: {e}，切換下一個...")
            continue
            
    return "（所有免費 AI 備援模型均被拒絕連線）"

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

        message = "🤖 <b>今日 AI 科技頭條推送 (OpenRouter 終極防禦版)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
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
