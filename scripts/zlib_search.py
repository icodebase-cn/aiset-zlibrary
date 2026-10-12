#!/usr/bin/env python3
"""
Z-Library 站内搜索工具

复用 login.py 保存的登录会话（~/.zlibrary/browser_profile），在 Z-Library
站内搜索书籍，输出书籍页链接，可直接交给 download.py 下载（EPUB 优先、PDF 备选）。

用法:
  python3 scripts/zlib_search.py "纳瓦尔宝典"          # 搜索并列出结果
  python3 scripts/zlib_search.py "关键词" --limit 5    # 限制结果数
"""

import asyncio
import sys
import urllib.parse
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright 未安装")
    print("请运行: pip install playwright")
    sys.exit(1)

# Windows 管道/非控制台环境下默认 GBK 编码会导致 emoji 输出崩溃，统一切 UTF-8
for _stream in (sys.stdout, sys.stderr):
    if _stream and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

BASE_URL = "https://zh.zlib.li"
BLOCK_MARK = "Try again later"  # 站点风控 503 挑战页特征（与账号状态无关）


def config_dir() -> Path:
    return Path.home() / ".zlibrary"


async def search_zlibrary(query: str, limit: int = 10) -> list:
    """
    Z-Library 站内搜索，返回书籍列表（同步打印结果）

    每项字段: title/author/year/language/extension/filesize/publisher/url
    说明: 默认使用有头浏览器——站点对无头访问风控严格（实测 503 拦截），
    复用 ~/.zlibrary/browser_profile 登录会话，需先运行 login.py。
    """
    search_url = f"{BASE_URL}/s/{urllib.parse.quote(query)}"
    print("=" * 70)
    print(" Z-Library 站内搜索")
    print("=" * 70)
    print(f"🔍 关键词: {query}")

    if not (config_dir() / "storage_state.json").exists():
        print("❌ 未找到登录会话")
        print("💡 请先运行: python3 scripts/login.py")
        return []

    async with async_playwright() as p:
        print("🚀 启动浏览器（使用已保存会话）...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(config_dir() / "browser_profile"),
            headless=False,  # 无头模式会被站点风控拦截
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = browser.pages[0] if browser.pages else await browser.new_page()
            page.set_default_timeout(60000)
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)

            # 风控检测: 挑战页无标题且正文极短
            title = (await page.title()).strip()
            body = (await page.locator("body").inner_text()).strip()
            if not title or BLOCK_MARK in body:
                print("⚠️  触发站点风控（503 挑战页），请稍后重试或更换网络")
                print("   该响应与账号状态无关，详见 docs/TROUBLESHOOTING.md")
                return []

            # 批量解析 z-bookcard 元数据（新版站点结构）
            cards = await page.eval_on_selector_all(
                "z-bookcard",
                """els => els.map(el => ({
                    title: (el.querySelector('[slot="title"]')?.textContent || '').trim(),
                    author: (el.querySelector('[slot="author"]')?.textContent || '').trim(),
                    href: el.getAttribute('href') || '',
                    year: el.getAttribute('year') || '',
                    language: el.getAttribute('language') || '',
                    extension: el.getAttribute('extension') || '',
                    filesize: el.getAttribute('filesize') || '',
                    publisher: el.getAttribute('publisher') || '',
                    deleted: el.getAttribute('deleted') || '0',
                }))""",
            )
        finally:
            await browser.close()

    results = []
    for c in cards:
        if c["deleted"] != "0" or not c["href"]:
            continue
        c["url"] = BASE_URL + c["href"]
        results.append(c)

    if not results:
        print(f"❌ 未找到与「{query}」匹配的书籍")
        return []

    shown = results[:limit]
    print(f"✅ 找到 {len(results)} 条结果（显示前 {len(shown)} 条）:")
    for i, b in enumerate(shown, 1):
        meta = " | ".join(
            str(b[k]) for k in ("extension", "year", "language", "filesize") if b.get(k)
        )
        print(f"  [{i}] {b['title']}")
        print(f"      {b.get('author') or '未知作者'} | {meta}")
    return shown


def main(argv: list) -> int:
    """独立入口: python3 scripts/zlib_search.py <关键词> [--limit N]"""
    args = argv[1:]
    limit = 10
    if "--limit" in args:
        i = args.index("--limit")
        try:
            limit = int(args[i + 1])
        except (IndexError, ValueError):
            print("❌ --limit 参数必须为数字")
            return 1
    positional = [
        a for a in args
        if not a.startswith("--") and a != str(limit)
    ]

    if not positional:
        print(__doc__)
        return 1

    results = asyncio.run(search_zlibrary(positional[0], limit=limit))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
