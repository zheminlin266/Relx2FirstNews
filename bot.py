import requests
from bs4 import BeautifulSoup
import os

SEARCH_URL = "https://www.2firsts.com/search/RELX"
TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    print(f"正在请求页面: {SEARCH_URL}")
    try:
        response = requests.get(SEARCH_URL, headers=headers, timeout=15)
        print(f"HTTP 状态码: {response.status_code}")
        
        # 如果返回 403 或 503，基本确定是被 Cloudflare 拦截了
        if response.status_code != 200:
            print("错误：页面请求失败，可能是被拦截。")
            return

        # 打印网页内容的前 500 个字符，看看是不是正常的 HTML
        print("网页内容片段预览：")
        print(response.text[:500])

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        print(f"页面上一共发现了 {len(links)} 个链接。")

        # 打印前 5 个发现的链接，看看格式
        for a in links[:5]:
            print(f"发现链接样本: {a['href']}")

    except Exception as e:
        print(f"发生异常: {e}")

if __name__ == "__main__":
    main()
