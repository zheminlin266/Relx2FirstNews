#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版 bot.py：
- 检查环境变量 TOKEN/CHAT_ID
- 更严格检查 Telegram API 返回值并打印详细错误
- 打印抓取页的 HTTP 状态和简短片段用于调试
- 使用脚本目录下的 sent_links.txt（绝对路径）
- 对 URL 做标准化（去掉 query/fragment）以避免重复推送
- 更好的日志输出
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse

# 配置
SEARCH_URL = "https://www.2firsts.com/search/RELX"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "sent_links.txt")
TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
DEBUG = os.environ.get("DEBUG", "0") in ("1", "true", "True")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def normalize_url(url, base=SEARCH_URL):
    """将相对 URL 转为绝对，并移除 query 与 fragment，用于去重比较。"""
    if url.startswith("//"):
        url = "https:" + url
    full = urljoin(base, url)
    p = urlparse(full)
    # 去掉 query 和 fragment
    p = p._replace(query="", fragment="")
    return urlunparse(p)

def send_tg_message(text):
    if not TOKEN or not CHAT_ID:
        print("ERROR: TG_BOT_TOKEN 或 TG_CHAT_ID 未配置。请设置 repository secrets 或环境变量。")
        return False, {"error": "missing token/chat_id"}
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        r = requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"发送消息请求异常: {e}")
        return False, {"error": str(e)}
    # 检查 HTTP 状态码
    try:
        data = r.json()
    except ValueError:
        print("发送消息：无法解析 Telegram 返回（非 JSON）", r.status_code, r.text[:500])
        return False, {"status_code": r.status_code, "text": r.text}
    if r.status_code != 200 or not data.get("ok"):
        print("Telegram API 返回错误:", r.status_code, data)
        return False, data
    return True, data

def read_sent_links():
    s = set()
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # 过滤垃圾行（rudimentary）只保留以 http 开头的
                    if line.startswith("http://") or line.startswith("https://"):
                        s.add(line)
        except Exception as e:
            print("读取 sent_links 文件失败:", e)
    return s

def write_sent_links(links_set):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            for l in sorted(links_set):
                f.write(l + "\n")
    except Exception as e:
        print("写入 sent_links 文件失败:", e)

def fetch_search_page():
    try:
        r = requests.get(SEARCH_URL, headers=HEADERS, timeout=20)
        print("抓取页面状态码:", r.status_code)
        if DEBUG:
            print("页面片段:\n", r.text[:2000])
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("抓取网页失败:", e)
        return None

def main():
    # 环境变量基本检查
    if not TOKEN or not CHAT_ID:
        print("ERROR: TG_BOT_TOKEN 或 TG_CHAT_ID 未设置。中止。")
        sys.exit(1)

    sent_links = read_sent_links()

    html = fetch_search_page()
    if not html:
        print("未获取到页面内容，退出。")
        return

    soup = BeautifulSoup(html, 'html.parser')
    new_found = []
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        # 过滤：包含 /news/ 并排除列表/搜索页
        if ("/news/" in href) and ("/news/list/" not in href) and ("/search/" not in href):
            full = normalize_url(href, base=SEARCH_URL)
            if full not in sent_links:
                new_found.append(full)
                sent_links.add(full)
        else:
            # 有些链接可能是绝对链接且包含域名
            if "2firsts.com" in href and "/news/" in href and "/news/list/" not in href:
                full = normalize_url(href, base=SEARCH_URL)
                if full not in sent_links:
                    new_found.append(full)
                    sent_links.add(full)

    if new_found:
        # 按时间顺序发送（假设页面顺序是从最新到最旧）
        for link in reversed(new_found):
            text = f"<b>[新文推送] RELX 相关文章</b>\n\n{link}"
            ok, resp = send_tg_message(text)
            print("send_tg_message ->", ok, resp)
        write_sent_links(sent_links)
        print(f"成功推送 {len(new_found)} 条新链接。")
    else:
        print("未检测到新的文章链接。")

if __name__ == "__main__":
    main()
