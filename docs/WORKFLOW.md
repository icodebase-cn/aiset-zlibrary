# 工作流程详解

## 下载源路由

`scripts/download.py` 根据输入自动路由下载源：

| 输入特征 | 下载源 | 脚本路径 |
| --- | --- | --- |
| URL 含 `ctfile.com` | 电子书宝库（城通网盘直链） | `treasure.download_ctfile` |
| 关键词（非 URL） | 电子书宝库搜索 → 未收录自动降级 Z-Library 站内搜索 | `keyword_flow`（宝库 `treasure.search_books` → `zlib_search.search_zlibrary`） |
| http(s) URL（zlib 域名） | Z-Library | `download_from_zlibrary` |

关键词流程说明：宝库优先（免登录）；未收录时打印降级提示后自动调 `zlib_search`（复用登录会话）；`--zlib` 可跳过宝库直接站内搜索；两段结果统一用 `--pick 序号` 选择下载。

## 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│                        aiset-zlibrary                        │
│                        完整工作流程                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  1. 用户输入 Z-Library 书籍链接       │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  2. 检查本地会话状态                   │
        │     ~/.zlibrary/storage_state.json     │
        └───────────────────────────────────────┘
                     ↙              ↘
              会话存在              会话不存在
                 ↓                      ↓
    ┌──────────────────┐      ┌─────────────────┐
    │  使用已保存的会话  │      │  提示用户先登录   │
    └──────────────────┘      │  python3 login.py│
                              └─────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  3. 启动浏览器（Playwright）           │
        │     - 使用持久化上下文                 │
        │     - 加载保存的 cookies               │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  4. 访问书籍页面                       │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  5. 检测页面类型                       │
        └───────────────────────────────────────┘
                     ↙              ↘
             新版界面              旧版界面
       (直接下载按钮)         (转换按钮)
                 ↓                   ↓
    ┌─────────────────┐   ┌──────────────────┐
    │ 点击格式下载按钮  │   │ 查找转换按钮      │
    │ 文字含格式与大小  │   │ 点击转换          │
    │ 如 EPUB, 636 KB │   │                  │
    └─────────────────┘   └──────────────────┘
                 ↘                   ↙
                  └─────────┬──────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  6. 智能选择格式                       │
        │     优先级: EPUB > PDF > 其他         │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  7. 等待转换完成（如需要）             │
        │     - 检测"转换已完成"消息             │
        │     - 最长等待 60 秒                  │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  8. 点击下载链接                      │
        │     - 优先真实鼠标点击                │
        │     - 失败时回退 JS 点击              │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  9. 等待下载完成                       │
        │     - 监听下载事件（最长 3 分钟）      │
        │     - 保存到 ~/Downloads/             │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  10. 保存原文件                       │
        │     - PDF: 直接使用                   │
        │     - EPUB: 直接保存                  │
        └───────────────────────────────────────┘
                            ↓
                      ✅ 完成！
```

## 宝库源流程（电子书宝库 / 城通网盘）

```text
关键词 或 ctfile 链接
    ↓
1. 加载目录（~/.zlibrary/treasure_catalog.json，7 天缓存，
   远端回退: raw.githubusercontent.com → jsdelivr CDN）
    ↓
2. 多关键词 AND 搜索（书名/作者/分类，不区分大小写）
    ↓
3. 列出匹配结果，--pick 序号 或 交互选择
    ↓
4. 启动 Chromium（headless）打开城通网盘页面
   （页面为 Vue SPA，必须浏览器渲染）
    ↓
5. 点击「普通下载」（链接自带公开访问码，免登录）
    ↓
6. 页内 JS 下载任务（免费通道限速约 60KB/s，
   脚本每 10 秒轮询进度）
    ↓
7. 完成后触发 Playwright download 事件
    ↓
8. 保存到 ~/Downloads/（zip 压缩包，内含 epub/mobi/azw3）
    ↓
✅ 完成！解压后可用 convert_epub.py 转换 epub
```

## Z-Library 站内搜索降级流程（宝库未收录时自动触发）

```text
宝库搜索无结果（或 --zlib 指定）
    ↓
1. 启动 Chromium（有头，无头会被站点风控 503 拦截）
   复用 ~/.zlibrary/browser_profile 登录会话，需先运行 login.py
    ↓
2. 访问 https://zh.zlib.li/s/<关键词>
   （挑战页检测: 无标题或正文含 "Try again later" → 提示后返回）
    ↓
3. 解析 z-bookcard 自定义元素（含 title/author/year/extension/filesize），
   过滤已删除（deleted!="0"），列出结果
    ↓
4. --pick 序号选择 → 打开书籍页
    ↓
5. 点击格式下载按钮 a.dlButton.addDownloadedBook[href^='/dl/']
   （文字如 "EPUB, 636 KB"，EPUB 优先、PDF 备选）
    ↓
6. 等待下载事件（最长 3 分钟）保存到 ~/Downloads/
    ↓
✅ 完成！epub 可用 convert_epub.py 转 Markdown
```

## 详细步骤说明

### 步骤 1-2: 初始化和会话检查

**检测会话状态：**
- 位置：`~/.zlibrary/storage_state.json`
- 内容：cookies、localStorage、sessionStorage
- 权限：600（仅所有者可读写）

**如果没有会话：**
```bash
python3 scripts/login.py
```

### 步骤 3-4: 浏览器启动和页面访问

**使用 Playwright 持久化上下文：**
```python
browser = await p.chromium.launch_persistent_context(
    user_data_dir="~/.zlibrary/browser_profile",
    headless=False,
    accept_downloads=True
)
```

**优势：**
- 保留所有 cookies
- 保留浏览器缓存
- 无需重复登录

### 步骤 5-6: 页面类型检测和格式选择

**新版界面（直接下载按钮，书籍页初始即有）：**
```python
dl_buttons = await page.query_selector_all(
    "a.dlButton[href^='/dl/'], a.addDownloadedBook[href^='/dl/']"
)
if dl_buttons:
    # 按钮文字含格式与大小（如 "EPUB, 636 KB"），EPUB 优先、PDF 备选
```

**旧版界面（转换按钮）：**
```python
convert_button = await page.query_selector('a[data-convert_to="pdf"]')
if convert_button:
    # 点击转换按钮
```

**格式优先级：**
1. **EPUB** ⭐ - 转换为 Markdown（便于阅读与检索）
2. **PDF** - 保留排版，无需转换
3. **其他** - 根据情况处理

### 步骤 7-8: 转换和下载

**等待转换完成：**
```python
for i in range(60):
    message = await page.query_selector('.message:has-text("转换为")')
    if '完成' in await message.inner_text():
        break
    await asyncio.sleep(1)
```

**真实点击（优先）与 JS 点击（回退）：**
```python
try:
    await download_link.click(timeout=15000)  # 真实鼠标点击
except Exception:
    await download_link.evaluate('el => el.click()')  # 部分站点忽略 JS 合成事件
```

### 步骤 9-10: 下载和保存

**监听下载事件：**
```python
async def handle_download(download):
    file_path = downloads_dir / download.suggested_filename
    await download.save_as(file_path)

page.on('download', handle_download)
```

**保存原文件：**
- **PDF** → 直接使用（保留排版）
- **EPUB** → 直接保存原文件；如需 Markdown，可手动运行 `python3 scripts/convert_epub.py`

## 可选: 手动转换 EPUB → Markdown

```bash
python3 scripts/convert_epub.py "书籍.epub" [输出.md]
```

- 使用 ebooklib + BeautifulSoup 转换为 Markdown
- 超过 350k 词的大文件自动分块（`书籍_part1.md`、`书籍_part2.md` 等）

## 故障排除

### 问题 1: 会话过期

**症状：** 提示未登录

**解决：**
```bash
rm ~/.zlibrary/storage_state.json
python3 scripts/login.py
```

### 问题 2: 找不到下载按钮

**症状：** "未找到下载链接"

**可能原因：**
- 页面结构变化
- 需要登录
- 网络问题

**解决：**
- 检查浏览器窗口
- 手动完成操作
- 截图保存用于调试

### 问题 3: 转换超时

**症状：** "转换超时"

**解决：**
- 检查网络连接
- 尝试手动点击转换
- 增加等待时间

## 最佳实践

1. **定期检查会话状态**
   ```bash
   ls -lh ~/.zlibrary/storage_state.json
   ```

2. **批量处理时添加延迟**
   ```bash
   for url in "url1" "url2" "url3"; do
       python3 scripts/download.py "$url"
       sleep 5  # 避免请求过快
   done
   ```

3. **按需转换**
   - 所有下载文件保存在 `~/Downloads/`
   - 如需 Markdown，使用 `python3 scripts/convert_epub.py` 手动转换
   - 可以随时备份或重新处理

## 性能优化

- 使用持久化浏览器上下文（减少启动时间）
- 并发下载（批量处理时）
- 智能格式选择（优先 EPUB，备选 PDF）

---

**需要帮助？** 查看 [故障排除指南](TROUBLESHOOTING.md)
