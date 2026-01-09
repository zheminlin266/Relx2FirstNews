import requests
from bs4 import BeautifulSoup
import os

# 配置信息
SEARCH_URL = "https://www.2firsts.com/search/RELX"
DB_FILE = "sent_links.txt"
TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")

def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"发送消息失败: {e}")

def main():
    # 1. 读取已发送链接
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            sent_links = set(f.read().splitlines())
    else:
        sent_links = set()

    # 2. 请求网页
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(SEARCH_URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"抓取网页失败: {e}")
        return

    # 3. 解析文章链接
    soup = BeautifulSoup(response.text, 'html.parser')
    new_found_links = []
    
    # 查找包含文章链接的 a 标签
    # 2firsts 的文章通常包含 /article/ 路径
    for a in soup.find_all('a', href=True):
        href = a['href']
        if "/article/" in href:
            # 补全完整链接
            full_url = f"https://www.2firsts.com{href}" if href.startswith('/') else href
            
            if full_url not in sent_links:
                new_found_links.append(full_url)
                sent_links.add(full_url)

    # 4. 发送通知并持久化
    if new_found_links:
        # 翻转列表，按时间顺序从旧到新发送
        for link in reversed(new_found_links):
            send_tg_message(f"<b>[新文推送] RELX 相关文章</b>\n\n{link}")
        
        # 将所有链接存回文件
        with open(DB_FILE, "w") as f:
            f.write("\n".join(list(sent_links)))
        print(f"成功推送 {len(new_found_links)} 条新链接。")
    else:
        print("未检测到新文章。")

if __name__ == "__main__":
    main()
