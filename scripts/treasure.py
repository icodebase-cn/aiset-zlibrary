#!/usr/bin/env python3
"""
电子书宝库下载源（ebook-treasure-chest）

目录来源: https://github.com/jbiaojerry/ebook-treasure-chest
- 书籍目录: data/treasure/all-books.json（项目内置离线快照，24071 本，无需联网）
- 分类文档: data/treasure/md/*.md（1000 个分类书目，本地直读）
- 下载托管: 城通网盘（ctfile.com），页面为 SPA，需真实浏览器渲染后点击"普通下载"
- 免登录: 链接自带公开访问码（p=8866），无需账号

用法:
  python3 scripts/treasure.py "书名或作者关键词"     # 搜索并下载（离线目录）
  python3 scripts/treasure.py <ctfile 链接>          # 直接下载
  python3 scripts/treasure.py --categories           # 列出全部内置分类
  python3 scripts/treasure.py --categories AI        # 按关键词筛选分类
  python3 scripts/treasure.py --cat-md AI            # 离线查看某分类的书目文档
  python3 scripts/treasure.py "关键词" --refresh     # 联网更新目录（回写内置快照）
"""

import asyncio
import json
import re
import sys
import time
import urllib.request
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

# 目录数据源（依次回退）
CATALOG_URLS = [
    "https://raw.githubusercontent.com/jbiaojerry/ebook-treasure-chest/main/docs/all-books.json",
    "https://cdn.jsdelivr.net/gh/jbiaojerry/ebook-treasure-chest@main/docs/all-books.json",
]
# 城通网盘公开分享访问码（内嵌于目录链接的 p= 参数，仅作缺省兜底）
DEFAULT_ACCESS_CODE = "8866"

DOWNLOAD_TIMEOUT = 1800  # 免费下载限速，单个文件最长等待 30 分钟

# 项目内置离线数据（ebook-treasure-chest 快照，随仓库分发，无需联网）
BUILTIN_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "treasure"
BUILTIN_CATALOG = BUILTIN_DATA_DIR / "all-books.json"
BUILTIN_MD_DIR = BUILTIN_DATA_DIR / "md"


def config_dir() -> Path:
    return Path.home() / ".zlibrary"


def catalog_cache_file() -> Path:
    return config_dir() / "treasure_catalog.json"


def builtin_catalog_file() -> Path | None:
    """返回项目内置目录文件路径（不存在则 None）"""
    return BUILTIN_CATALOG if BUILTIN_CATALOG.exists() else None


def _read_catalog_json(path: Path) -> list | None:
    """安全读取目录 JSON，失败返回 None"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return None


def _fetch_remote_catalog() -> list | None:
    """从远端获取目录 JSON，多源依次回退"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for url in CATALOG_URLS:
        try:
            print(f"📥 拉取目录: {url.split('/')[2]} ...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data:
                print(f"✅ 获取成功，共 {len(data)} 本书籍")
                return data
        except Exception as e:
            print(f"⚠️  获取失败: {e}")
    return None


def _save_catalog(data: list) -> None:
    """把最新目录写回用户缓存与项目内置快照（失败仅告警）"""
    cache = catalog_cache_file()
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"💾 目录已缓存: {cache}")
    except Exception as e:
        print(f"⚠️  缓存写入失败: {e}")
    try:
        BUILTIN_CATALOG.parent.mkdir(parents=True, exist_ok=True)
        with open(BUILTIN_CATALOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"💾 内置目录已更新: {BUILTIN_CATALOG}")
    except Exception as e:
        print(f"⚠️  内置目录更新失败（不影响使用）: {e}")


def load_catalog(refresh: bool = False, catalog_path: str | None = None) -> list | None:
    """
    加载书籍目录（离线优先）

    优先级: --catalog 指定文件 > 项目内置快照 > 用户缓存 > 远端 > 兜底
    - 项目内置快照: data/treasure/all-books.json（随仓库分发，默认离线可用，不联网）
    - refresh=True: 跳过所有本地文件，强制拉取远端并回写内置快照 + 缓存
    """
    cache = catalog_cache_file()

    # 1) 用户显式指定目录文件
    if catalog_path:
        data = _read_catalog_json(Path(catalog_path))
        if data:
            print(f"✅ 使用本地目录文件: {catalog_path}（共 {len(data)} 本）")
            return data
        print(f"❌ 读取目录文件失败: {catalog_path}")
        return None

    # 2) 项目内置离线快照（默认走这里，零联网）
    if not refresh:
        builtin = builtin_catalog_file()
        if builtin:
            data = _read_catalog_json(builtin)
            if data:
                print(f"✅ 使用项目内置离线目录（共 {len(data)} 本，--refresh 可联网更新）")
                return data

        # 3) 用户缓存（历史遗留路径，7 天内有效）
        if cache.exists() and (time.time() - cache.stat().st_mtime) < 7 * 24 * 3600:
            data = _read_catalog_json(cache)
            if data:
                print(f"✅ 使用本地缓存目录（共 {len(data)} 本，--refresh 可刷新）")
                return data

    # 4) 远端拉取（仅 --refresh 或本地全部缺失时触发）
    data = _fetch_remote_catalog()
    if data:
        _save_catalog(data)
        return data

    # 5) 远端失败，依次回退到任何可用的本地副本
    for label, path in (("项目内置离线目录", builtin_catalog_file()), ("过期本地缓存", cache if cache.exists() else None)):
        if not path:
            continue
        data = _read_catalog_json(path)
        if data:
            print(f"⚠️  远端不可用，回退{label}（共 {len(data)} 本）")
            return data
    return None


def search_books(catalog: list, query: str, limit: int = 10) -> list:
    """多关键词（空格分隔）AND 搜索书名/作者/分类，不区分大小写"""
    keywords = [k.lower() for k in query.split() if k.strip()]
    if not keywords:
        return []

    results = []
    for book in catalog:
        haystack = " ".join(
            str(book.get(field, "")).lower()
            for field in ("title", "author", "category")
        )
        if all(k in haystack for k in keywords):
            results.append(book)
            if len(results) >= 50:  # 搜索上限，避免全量遍历过长
                break
    return results[:limit] if limit else results


def sanitize_filename(name: str) -> str:
    """移除 Windows 文件名非法字符"""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


# ─────────────────────────────────────────────────────────────
# 离线分类 md 文档（data/treasure/md/*.md，共 1000 个分类）
# ─────────────────────────────────────────────────────────────

def list_categories() -> list:
    """列出所有内置分类名（去 .md 后缀，排序返回）"""
    if not BUILTIN_MD_DIR.exists():
        return []
    return sorted(p.stem for p in BUILTIN_MD_DIR.glob("*.md"))


def find_category_files(name: str) -> list:
    """按关键词匹配分类文件名：精确优先，其余为模糊命中"""
    if not BUILTIN_MD_DIR.exists():
        return []
    kw = (name or "").strip().lower()
    if not kw:
        return []
    exact = BUILTIN_MD_DIR / f"{name.strip()}.md"
    hits = [exact] if exact.exists() else []
    hits += sorted(
        p for p in BUILTIN_MD_DIR.glob("*.md")
        if kw in p.stem.lower() and p != exact
    )
    return hits


def read_category_md(name: str) -> tuple:
    """
    读取分类 md 原文（完全离线，不走网络）。
    返回 (文件名, 内容)；未找到返回 (None, None)。
    """
    files = find_category_files(name)
    if not files:
        return None, None
    target = files[0]
    try:
        return target.name, target.read_text(encoding="utf-8")
    except Exception:
        return None, None


async def download_ctfile(
    ctfile_url: str,
    downloads_dir: Path | None = None,
    headless: bool = True,
    timeout: int = DOWNLOAD_TIMEOUT,
) -> Path | None:
    """
    从城通网盘（ctfile.com）下载文件

    流程（已实测验证）:
    1. 页面为 Vue SPA，静态请求无法拿到按钮，必须浏览器渲染
    2. 等待渲染后点击"普通下载"（免费，页内 JS 任务，约 1%/秒）
    3. 下载在页内进行，完成后触发 Playwright download 事件
    """
    downloads_dir = downloads_dir or Path.home() / "Downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" treasure 源 · 城通网盘下载")
    print("=" * 70)
    print(f"🔗 链接: {ctfile_url}")

    async with async_playwright() as p:
        print("🚀 启动浏览器...")
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        page.set_default_timeout(30000)

        saved_path = None
        done = asyncio.Event()

        async def handle_download(download):
            nonlocal saved_path
            filename = sanitize_filename(download.suggested_filename)
            target = downloads_dir / filename
            # 重名去重: 追加 (1)、(2)...
            counter = 1
            while target.exists():
                target = downloads_dir / f"{Path(filename).stem} ({counter}){Path(filename).suffix}"
                counter += 1
            print(f"✅ 下载开始: {filename}")
            await download.save_as(target)
            saved_path = target
            done.set()

        page.on("download", handle_download)

        try:
            print("📖 打开网盘页面（SPA 渲染约需数秒）...")
            await page.goto(ctfile_url, wait_until="domcontentloaded", timeout=60000)

            # 等待 SPA 渲染出下载按钮
            try:
                await page.wait_for_selector(
                    "button.ct-button-primary, button:has-text('普通下载')",
                    timeout=30000,
                )
            except Exception:
                print(f"❌ 页面加载异常（未出现下载按钮）: {page.title()}")
                await browser.close()
                return None

            # 访问码兜底: 链接缺 p= 参数时页面会要求输入
            code_input = page.locator("input[placeholder*='访问码'], input[type='password']").first
            if await code_input.count() > 0 and await code_input.is_visible():
                print("🔑 检测到访问码输入框，自动填充分享码...")
                await code_input.fill(DEFAULT_ACCESS_CODE)
                confirm = page.locator("button:has-text('确定'), button:has-text('提交'), button:has-text('访问')").first
                if await confirm.count() > 0:
                    await confirm.click()
                    await asyncio.sleep(3)

            # 显示文件信息
            try:
                info = await page.locator("text=/\\d+(\\.\\d+)?\\s*[KMG]?B/").first.inner_text()
                print(f"📄 文件信息: {info.strip()}")
            except Exception:
                pass

            # 点击"普通下载"（文本可能渲染为"普 通下载"）
            btn = page.locator("button", has_text=re.compile(r"普\s*通下载"))
            if await btn.count() == 0:
                print("❌ 未找到「普通下载」按钮")
                await browser.close()
                return None
            await btn.first.click()
            print("⬇️  已点击普通下载，页内下载任务启动（免费通道限速，请耐心等待）...")

            # 轮询进度直到 download 事件触发
            start = time.time()
            last_progress = ""
            while not done.is_set() and time.time() - start < timeout:
                await asyncio.sleep(10)
                elapsed = int(time.time() - start)
                try:
                    progress = (await page.locator("text=/个未完成/").first.inner_text()).strip()
                    if progress != last_progress:
                        print(f"   ⏳ [{elapsed}s] {progress}")
                        last_progress = progress
                except Exception:
                    pass
                # 失败状态提前退出
                body_text = ""
                try:
                    body_text = await page.locator("body").inner_text()
                except Exception:
                    pass
                if any(kw in body_text for kw in ("任务失败", "下载失败", "文件已删除", "文件不存在")):
                    print("❌ 网盘任务失败或文件已失效")
                    break

            await browser.close()

        except Exception as e:
            print(f"❌ 下载失败: {e}")
            import traceback
            traceback.print_exc()
            try:
                await browser.close()
            except Exception:
                pass
            return None

    if saved_path and saved_path.exists():
        size_mb = saved_path.stat().st_size / 1024 / 1024
        print("")
        print("✅ 下载成功!")
        print(f"   文件: {saved_path.name}")
        print(f"   路径: {saved_path}")
        print(f"   大小: {size_mb:.1f} MB")
        return saved_path

    print("❌ 未获取到下载文件（超时或任务失败）")
    return None


def is_ctfile_url(arg: str) -> bool:
    return "ctfile.com" in arg.lower()


async def run_treasure(
    arg: str,
    pick: int | None = None,
    limit: int = 10,
    refresh: bool = False,
    catalog_path: str | None = None,
    headed: bool = False,
) -> int:
    """宝库源统一入口：ctfile 直链下载 或 关键词搜索后下载"""
    if is_ctfile_url(arg):
        path = await download_ctfile(arg, headless=not headed)
        return 0 if path else 1

    catalog = load_catalog(refresh=refresh, catalog_path=catalog_path)
    if not catalog:
        print("❌ 无法加载书籍目录（可尝试 --refresh 或 --catalog 指定本地 all-books.json）")
        return 1

    results = search_books(catalog, arg, limit=limit)
    if not results:
        print(f"❌ 未找到与「{arg}」匹配的书籍")
        return 1

    print(f"\n🔍 找到与「{arg}」匹配的书籍:")
    for i, book in enumerate(results, 1):
        fmt = "/".join(book.get("formats", []))
        print(f"  [{i}] {book.get('title')} | {book.get('author', '未知')} | {fmt} | {book.get('category', '')}")

    chosen = None
    if pick is not None:
        if 1 <= pick <= len(results):
            chosen = results[pick - 1]
        else:
            print(f"❌ --pick {pick} 超出范围（1-{len(results)}）")
            return 1
    elif len(results) == 1:
        chosen = results[0]
    else:
        print("\n💡 多个结果时使用 --pick 序号 选择下载，例如: python3 scripts/download.py \"关键词\" --pick 1")
        if not sys.stdin.isatty():
            return 0  # 非交互环境（Skill 调用），仅列出结果供上层选择
        try:
            idx = input("\n请输入序号下载（直接回车取消）: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if not idx:
            return 0
        try:
            chosen = results[int(idx) - 1]
        except (ValueError, IndexError):
            print(f"❌ 无效序号: {idx}")
            return 1

    print(f"\n📖 已选择: {chosen.get('title')}")
    path = await download_ctfile(chosen["link"], headless=not headed)

    if path and path.suffix.lower() == ".zip":
        print("\n💡 宝库文件为 zip 压缩包，解压后可得 epub/mobi/azw3。")
        print('   如需 Markdown，可对解压出的 epub 执行: python3 scripts/convert_epub.py "<epub文件>"')
    return 0 if path else 1


def treasure_main(argv: list) -> int:
    """treasure 模块独立入口: python3 scripts/treasure.py <关键词|ctfile链接> [--pick N]"""
    args = argv[1:]
    refresh = "--refresh" in args
    headed = "--headed" in args

    # ── 离线分类浏览（不联网、不下载）────────────────────
    if "--categories" in args:
        cats = list_categories()
        if not cats:
            print("❌ 未找到内置分类文档（data/treasure/md/ 为空或缺失）")
            return 1
        kw = None
        if "--categories" in args:
            i = args.index("--categories")
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                kw = args[i + 1]
        if kw:
            cats = [c for c in cats if kw.lower() in c.lower()]
            print(f"🗂  匹配「{kw}」的分类（{len(cats)} 个）:")
        else:
            print(f"🗂  内置分类共 {len(cats)} 个:")
        for c in cats:
            print(f"  {c}")
        if not kw:
            print("\n💡 用法: python3 scripts/treasure.py --categories <关键词>  筛选分类")
            print("        python3 scripts/treasure.py --cat-md <分类名>        查看该分类书目")
        return 0

    if "--cat-md" in args:
        i = args.index("--cat-md")
        name = args[i + 1] if i + 1 < len(args) else ""
        if not name:
            print("❌ 用法: python3 scripts/treasure.py --cat-md <分类名>")
            return 1
        fname, content = read_category_md(name)
        if not content:
            hits = [p.stem for p in find_category_files(name)]
            print(f"❌ 未找到分类「{name}」的本地文档")
            if hits:
                print(f"💡 相近分类: {', '.join(hits[:20])}")
            print("   可先运行: python3 scripts/treasure.py --categories <关键词>")
            return 1
        src = BUILTIN_MD_DIR / fname
        print(f"📄 {src}")
        print("─" * 70)
        print(content.rstrip())
        return 0
    # ──────────────────────────────────────────────────────

    catalog_path = None
    if "--catalog" in args:
        i = args.index("--catalog")
        catalog_path = args[i + 1] if i + 1 < len(args) else None
    pick = None
    if "--pick" in args:
        i = args.index("--pick")
        try:
            pick = int(args[i + 1]) if i + 1 < len(args) else None
        except ValueError:
            print("❌ --pick 参数必须为数字序号")
            return 1
    positional = [
        a for a in args
        if not a.startswith("--") and a != catalog_path and a != (str(pick) if pick else "")
    ]

    if not positional:
        print(__doc__)
        return 1

    return asyncio.run(
        run_treasure(
            positional[0],
            pick=pick,
            refresh=refresh,
            catalog_path=catalog_path,
            headed=headed,
        )
    )


if __name__ == "__main__":
    sys.exit(treasure_main(sys.argv))
