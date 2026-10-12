#!/usr/bin/env python3
"""
多源电子书下载工具

下载源（自动路由）:
- 电子书宝库: 书名/作者关键词搜索（目录来自 ebook-treasure-chest，免登录），
  或城通网盘直链（ctfile.com）；未收录时自动降级 Z-Library 站内搜索
- Z-Library: 传入书籍页 URL（含 zlib 域名）使用已保存会话下载；
  关键词加 --zlib 可直接走站内搜索（需已登录）
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright 未安装")
    print("请运行: pip install playwright")
    sys.exit(1)

try:
    import treasure
except ImportError:
    treasure = None  # 宝库源不可用时不影响 Z-Library 流程

try:
    import zlib_search
except ImportError:
    zlib_search = None


class ZLibraryDownloader:
    """Z-Library 自动下载器"""

    def __init__(self):
        self.downloads_dir = Path.home() / "Downloads"
        self.config_dir = Path.home() / ".zlibrary"
        self.config_file = self.config_dir / "config.json"

    def load_credentials(self) -> dict | None:
        """加载 Z-Library 凭据（优先级: 环境变量 > config.json）"""
        config_data = {}
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
            except Exception:
                config_data = {}

        email = os.environ.get("ZLIBRARY_EMAIL") or config_data.get('email')
        password = os.environ.get("ZLIBRARY_PASSWORD") or config_data.get('password')

        if email and password:
            return {'email': email, 'password': password}
        return None

    async def login_to_zlibrary(self, page):
        """登录 Z-Library"""
        credentials = self.load_credentials()

        if not credentials:
            print("⚠️  未找到 Z-Library 配置")
            print("💡 请先运行: python3 scripts/login.py")
            return False

        print("🔐 登录 Z-Library...")
        print(f"📧 使用账号: {credentials['email']}")

        try:
            # 检查是否已经有登录对话框
            modal = await page.query_selector('#zlibrary-modal-auth')
            if modal:
                print("📝 检测到登录对话框")
                # 直接在对话框中输入
                email_input = await page.wait_for_selector('#modal-auth input[type="email"], #modal-auth input[name="email"]', timeout=5000)
                await email_input.fill(credentials['email'])

                password_input = await page.wait_for_selector('#modal-auth input[type="password"], #modal-auth input[name="password"]', timeout=5000)
                await password_input.fill(credentials['password'])

                # 点击登录
                submit_button = await page.wait_for_selector('#modal-auth button[type="submit"]', timeout=5000)
                await submit_button.click()
            else:
                # 点击登录按钮
                login_button = await page.wait_for_selector('a:has-text("Log in"), a:has-text("登录")', timeout=5000)
                await login_button.click()
                await asyncio.sleep(2)

                # 输入邮箱
                email_input = await page.wait_for_selector('input[type="email"], input[name="email"]', timeout=5000)
                await email_input.fill(credentials['email'])

                # 输入密码
                password_input = await page.wait_for_selector('input[type="password"], input[name="password"]', timeout=5000)
                await password_input.fill(credentials['password'])

                # 点击登录
                submit_button = await page.wait_for_selector('button[type="submit"], button:has-text("Log in"), button:has-text("登录")', timeout=5000)
                await submit_button.click()

            # 等待登录完成
            await asyncio.sleep(5)

            # 检查是否登录成功
            current_url = page.url
            page_content = await page.content()

            if "logout" in page_content.lower() or "登录" not in page_content:
                print("✅ 登录成功")
                return True
            else:
                print("❌ 登录可能失败，请检查账号密码")
                return False

        except Exception as e:
            print(f"❌ 登录过程出错: {e}")
            return False

    async def download_from_zlibrary(self, url: str) -> Path | None:
        """从 Z-Library 下载书籍"""
        print("="*70)
        print("🌐 启动浏览器自动化下载")
        print("="*70)

        # 检查是否有保存的会话
        storage_state = self.config_dir / "storage_state.json"

        if not storage_state.exists():
            print("❌ 未找到会话状态")
            print("💡 请先运行: python3 scripts/login.py")
            return None

        print(f"✅ 使用已保存的会话")

        async with async_playwright() as p:
            # 启动浏览器（使用持久化上下文）
            print("🚀 启动浏览器...")

            browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.config_dir / "browser_profile"),
                headless=False,
                accept_downloads=True,
                args=['--disable-blink-features=AutomationControlled']
            )

            page = browser.pages[0] if browser.pages else await browser.new_page()
            page.set_default_timeout(60000)

            # 设置下载处理
            download_path = None
            download_done = asyncio.Event()

            async def handle_download(download):
                nonlocal download_path
                print("✅ 检测到下载开始...")
                suggested_filename = download.suggested_filename
                print(f"📄 文件名: {suggested_filename}")
                download_path = self.downloads_dir / suggested_filename
                await download.save_as(download_path)
                download_done.set()
                print(f"💾 已保存: {download_path}")

            page.on('download', handle_download)

            try:
                # 访问目标页面
                print(f"📖 访问书籍页面...")
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)

                print("⏳ 等待页面加载...")
                await asyncio.sleep(5)

                # 步骤1: 查找下载方式（优先 EPUB，然后 PDF）
                print("🔍 步骤1: 查找下载方式...")

                download_link = None
                downloaded_format = None

                # 新版界面: 书籍页自带格式下载按钮（文字如 "EPUB, 636 KB"，href 为 /dl/ 直链）
                dl_buttons = await page.query_selector_all(
                    "a.dlButton[href^='/dl/'], a.addDownloadedBook[href^='/dl/']"
                )

                if dl_buttons:
                    print(f"📱 检测到新版界面（{len(dl_buttons)} 个直接下载按钮）")
                    # 从按钮文字解析格式，EPUB 优先、PDF 备选
                    for want_fmt in ("epub", "pdf"):
                        for btn in dl_buttons:
                            btn_text_lower = (await btn.inner_text()).strip().lower()
                            if want_fmt in btn_text_lower:
                                download_link = btn
                                downloaded_format = want_fmt
                                break
                        if download_link:
                            break
                    if not download_link:
                        download_link = dl_buttons[0]
                    chosen_text = (await download_link.inner_text()).strip()
                    print(f"✅ 选择下载按钮: {chosen_text or '(未知格式)'}")

                else:
                    # 旧版界面：检查转换按钮
                    print("📱 未检测到直接下载按钮，尝试旧版转换按钮...")
                    convert_selector_epub = 'a[data-convert_to="epub"]'
                    convert_selector_pdf = 'a[data-convert_to="pdf"]'

                    # 优先尝试 EPUB
                    convert_button = await page.query_selector(convert_selector_epub)

                    if convert_button:
                        print("📝 检测到 EPUB 转换按钮")
                        downloaded_format = 'epub'
                        await convert_button.evaluate('el => el.click()')
                        print("✅ 已点击 EPUB 转换按钮")

                        # 等待转换完成
                        print("⏳ 等待 EPUB 转换完成...")
                        for i in range(60):
                            await asyncio.sleep(1)
                            try:
                                message = await page.query_selector('.message:has-text("转换为")')
                                if message:
                                    message_text = await message.inner_text()
                                    if 'epub' in message_text.lower() and '完成' in message_text:
                                        print("✅ EPUB 转换已完成!")
                                        break
                            except:
                                pass
                            if i % 10 == 0 and i > 0:
                                print(f"   ⏳ 等待中... {i}秒")

                        # 查找下载链接
                        download_link = await page.query_selector('a[href*="/dl/"][href*="convertedTo=epub"]')

                        if not download_link:
                            all_links = await page.query_selector_all('a[href*="/dl/"]')
                            if all_links:
                                download_link = all_links[0]
                                href = await download_link.get_attribute('href')
                                print(f"✅ 找到下载链接: {href}")

                    else:
                        # 备选：尝试 PDF
                        convert_button = await page.query_selector(convert_selector_pdf)

                        if convert_button:
                            print("📝 检测到 PDF 转换按钮")
                            downloaded_format = 'pdf'
                            await convert_button.evaluate('el => el.click()')
                            print("✅ 已点击 PDF 转换按钮")

                            # 等待转换完成
                            print("⏳ 等待 PDF 转换完成...")
                            for i in range(60):
                                await asyncio.sleep(1)
                                try:
                                    message = await page.query_selector('.message:has-text("转换为")')
                                    if message:
                                        message_text = await message.inner_text()
                                        if 'pdf' in message_text.lower() and '完成' in message_text:
                                            print("✅ PDF 转换已完成!")
                                            break
                                except:
                                    pass
                                if i % 10 == 0 and i > 0:
                                    print(f"   ⏳ 等待中... {i}秒")

                            # 查找下载链接
                            download_link = await page.query_selector('a[href*="/dl/"][href*="convertedTo=pdf"]')

                            if not download_link:
                                all_links = await page.query_selector_all('a[href*="/dl/"]')
                                if all_links:
                                    download_link = all_links[0]
                                    href = await download_link.get_attribute('href')
                                    print(f"✅ 找到下载链接: {href}")

                # 如果还是没找到，尝试直接下载链接
                if not download_link:
                    print("🔍 未检测到转换按钮，查找直接下载链接...")

                    selectors = [
                        'a[href*="/dl/"]',
                        'a:has-text("下载")',
                        'a:has-text("Download")',
                        'button:has-text("下载")',
                    ]

                    for selector in selectors:
                        try:
                            links = await page.query_selector_all(selector)
                            if links:
                                for link in links:
                                    href = await link.get_attribute('href')
                                    if href and '/dl/' in href:
                                        download_link = link
                                        # 从 URL 判断格式
                                        if 'pdf' in href.lower():
                                            downloaded_format = 'pdf'
                                        elif 'epub' in href.lower():
                                            downloaded_format = 'epub'
                                        print(f"✅ 找到下载链接: {href} (格式: {downloaded_format})")
                                        break
                                if download_link:
                                    break
                        except:
                            continue

                if not download_link:
                    print("❌ 未找到下载链接")
                    await browser.close()
                    return None, None

                # 点击下载（优先真实鼠标点击；部分站点忽略 JS 合成事件）
                print("⬇️  步骤2: 点击下载链接...")

                try:
                    await download_link.click(timeout=15000)
                    print("✅ 点击成功")
                except Exception as e:
                    print(f"⚠️  真实点击失败，改用 JS 点击: {e}")
                    try:
                        await download_link.evaluate('el => el.click()')
                        print("✅ 点击成功（JS）")
                    except Exception as e2:
                        print(f"❌ 点击失败: {e2}")
                        await browser.close()
                        return None, None

                # 等待下载完成（下载事件回调里 save_as 完成后置位）
                print("⏳ 步骤3: 等待下载完成（最长 3 分钟）...")
                try:
                    await asyncio.wait_for(download_done.wait(), timeout=180)
                except asyncio.TimeoutError:
                    pass

                # 检查结果
                if download_path and download_path.exists():
                    file_size = download_path.stat().st_size / 1024
                    print(f"✅ 下载成功!")
                    print(f"   格式: {downloaded_format.upper() if downloaded_format else '未知'}")
                    print(f"   文件: {download_path.name}")
                    print(f"   路径: {download_path}")
                    print(f"   大小: {file_size:.1f} KB")
                    await browser.close()
                    return download_path, downloaded_format

                # 备选：检查下载目录
                print("🔍 检查下载目录...")

                # 根据格式查找文件
                if downloaded_format == 'pdf':
                    pattern = "*.pdf"
                else:
                    pattern = "*.epub"

                downloaded_files = list(self.downloads_dir.glob(pattern))

                if downloaded_files:
                    latest_file = max(downloaded_files, key=lambda p: p.stat().st_mtime)
                    file_age = time.time() - latest_file.stat().st_mtime

                    if file_age < 120:
                        file_size = latest_file.stat().st_size / 1024
                        print(f"✅ 下载成功!")
                        print(f"   格式: {downloaded_format.upper() if downloaded_format else '未知'}")
                        print(f"   文件: {latest_file.name}")
                        print(f"   路径: {latest_file}")
                        print(f"   大小: {file_size:.1f} KB")
                        await browser.close()
                        return latest_file, downloaded_format

                print("❌ 未找到下载的文件")
                await browser.close()
                return None, None

            except Exception as e:
                print(f"❌ 下载失败: {e}")
                import traceback
                traceback.print_exc()
                await browser.close()
                return None, None


def route_source(arg: str) -> str:
    """根据输入判断下载源: treasure（直链）/ zlibrary（URL）/ keyword（关键词）"""
    if treasure and treasure.is_ctfile_url(arg):
        return "treasure"
    if arg.lower().startswith(("http://", "https://")):
        return "zlibrary"
    return "keyword"


def print_download_success(downloaded_file, file_format):
    """打印成功结果与后续提示"""
    print("")
    print("=" * 70)
    print("🎉 下载完成！")
    print("=" * 70)
    print(f"📖 文件: {downloaded_file}")
    if file_format:
        print(f"📄 格式: {file_format.upper()}")
    print("")

    if file_format == 'epub' or downloaded_file.suffix.lower() == '.epub':
        print("💡 如需转换为 Markdown（大文件自动分块）:")
        print(f'   python3 scripts/convert_epub.py "{downloaded_file}"')
        print("")


async def choose(results, pick):
    """按 --pick / 唯一结果自动 / 交互输入 选择候选，返回 (选中项, 退出码)"""
    if pick is not None:
        if 1 <= pick <= len(results):
            return results[pick - 1], 0
        print(f"❌ --pick {pick} 超出范围（1-{len(results)}）")
        return None, 1
    if len(results) == 1:
        return results[0], 0
    print("\n💡 使用 --pick 序号 选择下载")
    if not sys.stdin.isatty():
        return None, 0  # 非交互环境（Skill 调用），仅列出结果供上层选择
    try:
        idx = input("请输入序号下载（直接回车取消）: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None, 0
    if not idx:
        return None, 0
    try:
        return results[int(idx) - 1], 0
    except (ValueError, IndexError):
        print(f"❌ 无效序号: {idx}")
        return None, 1


async def keyword_flow(args) -> int:
    """关键词下载流程: 宝库优先 → 未收录自动降级 Z-Library 站内搜索"""
    query = args.query

    # 1. 宝库搜索（--zlib 跳过）
    treasure_results = []
    if args.zlib:
        print("🔍 已指定 --zlib，直接使用 Z-Library 站内搜索")
    elif treasure is None:
        print("⚠️  treasure 模块不可用，改用 Z-Library 站内搜索")
    else:
        catalog = treasure.load_catalog(refresh=args.refresh, catalog_path=args.catalog)
        if catalog:
            treasure_results = treasure.search_books(catalog, query, limit=args.limit)

    # 2. 宝库命中 → 选择 → 城通网盘下载
    if treasure_results:
        print(f"\n🔍 找到与「{query}」匹配的书籍:")
        for i, b in enumerate(treasure_results, 1):
            fmt = "/".join(b.get("formats", []))
            print(f"  [{i}] {b.get('title')} | {b.get('author', '未知')} | {fmt} | {b.get('category', '')}")

        chosen, code = await choose(treasure_results, args.pick)
        if chosen is None:
            return code
        print(f"\n📖 已选择: {chosen.get('title')}")
        path = await treasure.download_ctfile(chosen["link"], headless=not args.headed)
        if path and path.suffix.lower() == ".zip":
            print("\n💡 宝库文件为 zip 压缩包，解压后可得 epub/mobi/azw3。")
            print('   如需 Markdown，可对解压出的 epub 执行: python3 scripts/convert_epub.py "<epub文件>"')
        return 0 if path else 1

    # 3. 宝库未命中 → Z-Library 站内搜索
    if not args.zlib:
        print(f"ℹ️  宝库未收录「{query}」，自动降级 Z-Library 站内搜索...")

    if zlib_search is None:
        print("❌ zlib_search 模块缺失，无法站内搜索")
        return 1

    zlib_results = await zlib_search.search_zlibrary(query, limit=args.limit)
    if not zlib_results:
        print("\n💡 也可以提供 Z-Library 书籍页链接重试，或换关键词搜索")
        return 1

    chosen, code = await choose(zlib_results, args.pick)
    if chosen is None:
        return code

    print(f"\n📖 已选择: {chosen['title']}")
    downloader = ZLibraryDownloader()
    downloaded_file, file_format = await downloader.download_from_zlibrary(chosen["url"])

    if not downloaded_file or not downloaded_file.exists():
        print("")
        print("=" * 70)
        print("❌ 下载失败")
        print("=" * 70)
        return 1

    print_download_success(downloaded_file, file_format)
    return 0


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="多源电子书下载工具（电子书宝库 / Z-Library）",
        epilog="示例:\n"
               '  python3 scripts/download.py "书名关键词"            # 宝库优先，未收录自动降级站内搜索\n'
               '  python3 scripts/download.py "书名关键词" --zlib     # 直接 Z-Library 站内搜索\n'
               "  python3 scripts/download.py <Z-Library 书籍页 URL>\n"
               "  python3 scripts/download.py <城通网盘 ctfile 链接>\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="关键词 / Z-Library URL / 城通网盘链接")
    parser.add_argument("--pick", type=int, default=None, help="搜索结果序号（非交互选择）")
    parser.add_argument("--limit", type=int, default=10, help="搜索结果显示数量（默认 10）")
    parser.add_argument("--zlib", action="store_true", help="关键词改用 Z-Library 站内搜索（默认宝库优先，未收录自动降级）")
    parser.add_argument("--refresh", action="store_true", help="强制刷新宝库目录缓存")
    parser.add_argument("--catalog", default=None, help="手动指定宝库目录 JSON 文件（all-books.json）")
    parser.add_argument("--headed", action="store_true", help="宝库下载使用有头浏览器（调试用）")
    args = parser.parse_args()

    source = route_source(args.query)

    if source == "treasure":
        sys.exit(await treasure.run_treasure(args.query, headed=args.headed))

    if source == "keyword":
        sys.exit(await keyword_flow(args))

    # Z-Library URL 流程
    downloader = ZLibraryDownloader()

    downloaded_file, file_format = await downloader.download_from_zlibrary(args.query)

    if not downloaded_file or not downloaded_file.exists():
        print("")
        print("="*70)
        print("❌ 下载失败")
        print("="*70)
        sys.exit(1)

    print_download_success(downloaded_file, file_format)


if __name__ == "__main__":
    asyncio.run(main())
