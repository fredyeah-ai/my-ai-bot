import os
import requests
import xml.etree.ElementTree as ET

def get_summary(title, api_key):
    """呼叫 Cohere V2 官方接口，使用現行有效嘅 model ID（帶日期後綴）"""
    if not api_key:
        return "（未配置 AI 金鑰，無法提供簡介）"

    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"請根據以下新聞標題，用50字內、親切流暢嘅香港廣東話（口語化）簡介呢則新聞大概講咩，唔好講廢話：\n【{title}】"

    # 💡 更新：舊嘅 "command-r7b" / "command-r-plus"（冇日期後綴）已經 deprecated，
    # 而家一定要用帶日期後綴嘅 model ID
    v2_models = ["command-r7b-12-2024", "command-a-03-2025"]

    for model in v2_models:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()

                if 'message' in data and 'content' in data['message']:
                    content_list = data['message']['content']
                    if isinstance(content_list, list) and len(content_list) > 0 and 'text' in content_list[0]:
                        summary = content_list[0]['text'].strip()
                        return summary.replace('"', '').replace('「', '').replace('」', '')

                return "（模型回傳格式異常）"
            else:
                # 💡 加多咗 response.text，方便睇實際 error message（例如 key 無效、rate limit 等）
                print(f"ℹ️ Cohere V2 模型 {model} 無法使用 (狀態碼 {response.status_code}): {response.text}，嘗試下一個...")
        except Exception as e:
            print(f"ℹ️ 呼叫 Cohere V2 [{model}] 出錯: {e}，切換中...")
            continue

    return "（Cohere 所有現行模型均無法生成簡介）"


def fetch_and_send():
    bot_token = os.environ.get('TG_BOT_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    ai_key = os.environ.get('GEMINI_API_KEY')  # 這裡面裝的是你的 Cohere 鎖匙

    if not bot_token or not chat_id:
        print("錯誤：找不到環境變數")
        return

    rss_url = "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=zh-HK&gl=HK&ceid=HK:zh-hk"
    try:
        response = requests.get(rss_url, timeout=10)
        if response.status_code != 200:
            return

        root = ET.fromstring(response.content)
        items = root.findall('.//item')[:5]

        if not items:
            return

        message = "🤖 <b>今日 AI 科技頭條推送 (Cohere V2 頂配版)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"

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
