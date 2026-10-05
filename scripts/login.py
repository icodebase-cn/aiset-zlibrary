#!/usr/bin/env python3
"""
Z-Library Login - 一次性登录，保存会话状态

凭据优先级: 命令行参数 > 环境变量 > ~/.zlibrary/config.json
未配置凭据或自动登录失败时回退到手动登录。
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright 未安装")
    print("请运行: pip install playwright")
    sys.exit(1)

# 登录凭据环境变量（当用户未通过其他方式提供登录信息时使用）
ENV_EMAIL = "ZLIBRARY_EMAIL"
ENV_PASSWORD = "ZLIBRARY_PASSWORD"

HOME_URL = "https://zh.zlib.li/"


def load_credentials(cli_email=None, cli_password=None):
    """加载登录凭据（优先级: 命令行参数 > 环境变量 > config.json）

    返回 (email, password)；无任何可用来源时返回 (None, None)。
    """
    config_email = config_password = None
    config_file = Path.home() / ".zlibrary" / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            config_email = data.get('email')
            config_password = data.get('password')
        except Exception:
            pass

    email = cli_email or os.environ.get(ENV_EMAIL) or config_email
    password = cli_password or os.environ.get(ENV_PASSWORD) or config_password

    if email and password:
        return email, password
    return None, None


def is_logged_in(page):
    """检测当前页面是否处于已登录状态"""
    try:
        if page.query_selector('a[href*="logout"]'):
            return True
        return "logout" in page.content().lower()
    except Exception:
        return False


def try_auto_login(page, email, password):
    """使用给定凭据自动登录，成功返回 True"""
    try:
        # 打开登录对话框
        modal = page.query_selector('#zlibrary-modal-auth')
        if not modal:
            login_button = page.query_selector('a:has-text("Log in"), a:has-text("登录")')
            if not login_button:
                print("⚠️  未找到登录按钮")
                return False
            login_button.click()
            page.wait_for_timeout(2000)

        # 填写邮箱
        email_input = page.wait_for_selector(
            '#modal-auth input[type="email"], #modal-auth input[name="email"], '
            'input[type="email"], input[name="email"]',
            timeout=10000
        )
        email_input.fill(email)

        # 填写密码
        password_input = page.wait_for_selector(
            '#modal-auth input[type="password"], #modal-auth input[name="password"], '
            'input[type="password"]',
            timeout=10000
        )
        password_input.fill(password)

        # 提交登录
        submit_button = page.wait_for_selector(
            '#modal-auth button[type="submit"], '
            'button[type="submit"], button:has-text("Log in"), button:has-text("登录")',
            timeout=10000
        )
        submit_button.click()

        page.wait_for_timeout(5000)
        return is_logged_in(page)

    except Exception as e:
        print(f"⚠️  自动登录出错: {e}")
        return False


def zlibrary_login(email=None, password=None):
    """Z-Library 登录并保存会话"""
    config_dir = Path.home() / ".zlibrary"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_dir.chmod(0o700)

    storage_state = config_dir / "storage_state.json"
    cred_email, cred_password = load_credentials(email, password)

    print("="*70)
    print("🔐 Z-Library 登录")
    print("="*70)
    print("")
    print("说明:")
    print("  1. 凭据优先级: --email/--password > 环境变量 > ~/.zlibrary/config.json")
    print(f"  2. 环境变量: {ENV_EMAIL} / {ENV_PASSWORD}")
    print("  3. 未配置凭据或自动登录失败时，可在浏览器中手动完成登录")
    print("")

    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(config_dir / "browser_profile"),
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            print("📖 访问 Z-Library...")
            page.goto(HOME_URL, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)

            if is_logged_in(page):
                print("✅ 检测到已登录的会话，无需重新登录")
            else:
                logged_in = False
                if cred_email and cred_password:
                    print(f"🔐 使用已配置账号自动登录: {cred_email}")
                    if try_auto_login(page, cred_email, cred_password):
                        print("✅ 自动登录成功")
                        logged_in = True
                    else:
                        print("")
                        print("⚠️  自动登录失败（可能需要验证码或账号信息有误）")
                else:
                    print("⚠️  未找到登录凭据，需要手动登录")
                    print("")
                    print("💡 配置凭据后可自动登录:")
                    print(f"   - 环境变量: {ENV_EMAIL} / {ENV_PASSWORD}")
                    print("   - 配置文件: ~/.zlibrary/config.json (email/password)")
                    print("   - 命令行参数: --email / --password")

                if not logged_in:
                    print("")
                    print("="*70)
                    print("📋 请在浏览器中手动完成登录，然后回到终端")
                    print("="*70)
                    input("✅ 已完成登录？按 ENTER 保存会话... ")

            # 保存会话状态
            browser.storage_state(path=str(storage_state))
            storage_state.chmod(0o600)

            print("")
            print("✅ 会话已保存！")
            print(f"📁 位置: {storage_state}")
            print("")
            print("💡 现在可以运行自动化脚本了：")
            print("   python3 scripts/download.py <Z-Library URL>")
            print("")

        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            browser.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Z-Library 登录（凭据来自命令行参数 / 环境变量 / config.json）"
    )
    parser.add_argument("--email", help=f"登录邮箱（可选，优先于环境变量 {ENV_EMAIL} 和 config.json）")
    parser.add_argument("--password", help=f"登录密码（可选，优先于环境变量 {ENV_PASSWORD} 和 config.json）")
    args = parser.parse_args()

    zlibrary_login(args.email, args.password)


if __name__ == "__main__":
    main()
