#!/usr/bin/env python3
"""
Z-Library 全自动下载工具
"""

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

            async def handle_download(download):
                nonlocal download_path
                print("✅ 检测到下载开始...")
                suggested_filename = download.suggested_filename
                print(f"📄 文件名: {suggested_filename}")
                download_path = self.downloads_dir / suggested_filename
                await download.save_as(download_path)
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

                # 首先检查是否有三个点的菜单按钮（新界面）
                dots_button = await page.query_selector('button[aria-label="更多选项"], button[title="更多"], .more-options, [class*="dots"], [class*="more"]')

                download_link = None
                downloaded_format = None

                if dots_button:
                    print("📱 检测到新版界面（三点菜单）")
                    # 点击打开菜单
                    await dots_button.click()
                    await asyncio.sleep(2)

                    # 查找 EPUB 选项（优先）
                    print("🔍 查找 EPUB 选项...")
                    epub_options = await page.query_selector_all('a:has-text("EPUB"), button:has-text("EPUB")')
                    if epub_options:
                        # 选择第一个 EPUB
                        download_link = epub_options[0]
                        downloaded_format = 'epub'
                        print(f"✅ 找到 EPUB 选项")
                    else:
                        # 备选：查找 PDF
                        print("🔍 未找到 EPUB，查找 PDF 选项...")
                        pdf_options = await page.query_selector_all('a:has-text("PDF"), button:has-text("PDF")')
                        if pdf_options:
                            download_link = pdf_options[0]
                            downloaded_format = 'pdf'
                            print(f"✅ 找到 PDF 选项")

                else:
                    # 旧界面：检查转换按钮
                    print("📱 检测到旧版界面")
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
                    return None

                # 点击下载
                print("⬇️  步骤2: 点击下载链接...")

                try:
                    await download_link.evaluate('el => el.click()')
                    print("✅ 点击成功")
                except Exception as e:
                    print(f"❌ 点击失败: {e}")
                    await browser.close()
                    return None

                # 等待下载
                print("⏳ 步骤3: 等待下载完成...")
                await asyncio.sleep(20)

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


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Z-Library 全自动下载工具")
        print("")
        print("用法: python3 download.py <Z-Library URL>")
        sys.exit(1)

    url = sys.argv[1]
    downloader = ZLibraryDownloader()

    # 下载
    downloaded_file, file_format = await downloader.download_from_zlibrary(url)

    if not downloaded_file or not downloaded_file.exists():
        print("")
        print("="*70)
        print("❌ 下载失败")
        print("="*70)
        sys.exit(1)

    print("")
    print("="*70)
    print("🎉 下载完成！")
    print("="*70)
    print(f"📖 文件: {downloaded_file}")
    if file_format:
        print(f"📄 格式: {file_format.upper()}")
    print("")

    # 如果是 EPUB，提示可选手动转换
    if file_format == 'epub' or downloaded_file.suffix.lower() == '.epub':
        print("💡 如需转换为 Markdown（大文件自动分块）:")
        print(f'   python3 scripts/convert_epub.py "{downloaded_file}"')
        print("")


if __name__ == "__main__":
    asyncio.run(main())
