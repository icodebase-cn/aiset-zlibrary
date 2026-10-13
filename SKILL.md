---
name: aiset-zlibrary
description: 自动下载书籍。支持双源：电子书宝库 ebook-treasure-chest（关键词搜索/城通网盘链接，免登录）与 Z-Library（书籍页链接，优先 EPUB 备选 PDF）；宝库未收录时自动降级 Z-Library 站内搜索。保存原始文件，不做自动转换。
---

# aiset-zlibrary Skill

让 Claude 帮你自动下载书籍，支持两个下载源：

- **电子书宝库**（[ebook-treasure-chest](https://github.com/jbiaojerry/ebook-treasure-chest)）：2.4万+ 中文书籍目录，书名/作者关键词搜索，城通网盘免登录下载（默认首选）
- **Z-Library**：书籍页链接下载，优先 EPUB、备选 PDF，需已保存登录会话；宝库未收录时自动降级为 Z-Library 站内搜索（需已登录）

下载后直接保存原文件，不做自动转换。

## 🎯 核心功能

- 一键下载书籍（优先 EPUB，备选 PDF）
- 关键词搜索电子书宝库目录（免登录），未收录时自动降级 Z-Library 站内搜索
- 下载后直接保存原文件（不自动转换）
- 可选手动转换：EPUB → Markdown（大文件自动分块）

## 🌐 运行环境适配（触发后第一步判断）

本 Skill 的下载能力依赖**本地终端与文件系统**（Python3、Playwright、~/Downloads 目录），只能在电脑端 AI 客户端（Claude Code / AISet 桌面端）真正执行。

**若当前环境没有本地终端**（微信小程序、手机 App、纯网页对话等）：
- 🚫 禁止输出任何终端命令（`python3 ...` 类命令对用户毫无意义）
- 直接友好告知用户：
  > 「这个下载技能需要在**电脑端**使用。请在电脑上打开 AISet 客户端（或 Claude Code），安装「aiset-zlibrary」技能后，直接发送书名（如：帮我下载《人工智能简史》）即可自动下载，文件保存在电脑 `~/Downloads` 目录。支持电子书宝库（2.4万+ 中文书，免登录）和 Z-Library 双源搜索。」
- 可一句话简述支持的下载源，但不要展开终端教程

**若当前环境具备本地终端**：按下方流程正常执行。

## 📋 激活条件（Triggers）

当用户提到以下需求时，使用此 Skill：

- 用户提供 Z-Library 书籍链接（包含 `zlib.li`、`z-lib.org`、`zh.zlib.li` 等域名）
- 用户提供城通网盘链接（包含 `ctfile.com`）
- 用户说"帮我下载这本书"（无论有无链接）
- 用户说"自动下载并读这本书"
- 用户说"把这个 Z-Library 链接的书籍下载下来"
- 用户要求从特定 URL 下载书籍
- 用户只有书名/作者，希望搜索并下载（优先用电子书宝库搜索）

## 🔧 核心指令

### 源路由规则

| 输入特征 | 下载源 | 是否需要登录 |
| --- | --- | --- |
| URL 含 `ctfile.com` | 电子书宝库（直链） | 否 |
| 非_URL 的关键词 | 电子书宝库（搜索）→ 未收录自动降级 Z-Library 站内搜索 | 宝库否 / 降级是 |
| URL 含 zlib 域名 | Z-Library | 是（已保存会话） |

### 流程 A: Z-Library 链接（用户提供 Z-Library 链接时）

当用户提供 Z-Library 链接时，按以下流程执行：

### Step 1: 提取信息

从用户提供的 URL 中提取：
- 书名
- 作者（如果有）
- 完整 URL
- 格式选项（PDF/EPUB/MOBI 等）

### Step 2: 自动下载

使用已保存的会话（`~/.zlibrary/storage_state.json`）自动登录 Z-Library：

1. **优先下载 EPUB**（保存原文件，适合阅读器阅读）
2. **自动降级**：如果没有 EPUB，下载 PDF（保留排版）
3. **直接保存**：不做自动转换，文件保存到 ~/Downloads

### Step 3: 返回结果

向用户返回：
- ✅ 下载成功确认
- 📖 文件保存路径
- 💡 如需 Markdown，可提示手动转换：`python3 scripts/convert_epub.py`

### Step 4: 错误处理

如果遇到错误：
- 尝试重试最多 3 次
- 如果登录失败，提示用户运行 `python3 ~/.claude/skills/aiset-zlibrary/scripts/login.py`（自动使用已配置凭据登录）
- 如果下载失败，提供故障排查建议

### 流程 B: 电子书宝库（关键词或城通网盘链接时）

> 🚨 **强制规则：用户只给书名/作者（未给链接）时，必须首先执行宝库搜索**，这是默认且首选路径。禁止跳过宝库直接去寻找其他下载地址。

**Step 1: 搜索目录**（关键词输入时）

```bash
python3 scripts/download.py "书名关键词"
```

- 首次运行会自动拉取目录（约 2.4 万本）并缓存到 `~/.zlibrary/treasure_catalog.json`（7 天有效）
- 输出匹配结果列表：序号、书名、作者、格式（epub/mobi/azw3）、分类
- 将列表展示给用户，让用户选择序号（或直接 `--pick <序号>`）
- **搜索无结果时脚本自动降级 Z-Library 站内搜索**（无需人工干预），站内结果同样列出供 `--pick` 选择

**Step 2: 选择并下载**

```bash
python3 scripts/download.py "书名关键词" --pick <序号>
```

- 也可直接传城通网盘链接（`ctfile.com`）跳过搜索
- 免费通道限速（约 60KB/s），大文件需数分钟到数十分钟，向用户说明进度
- 完成后文件为 zip 压缩包（内含 epub/mobi/azw3），保存到 ~/Downloads

**Step 3: 返回结果**

- ✅ 下载成功确认 + 文件路径
- 💡 提示：解压 zip 可得 epub/mobi/azw3；如需 Markdown 可用 `python3 scripts/convert_epub.py` 转换解压出的 epub

### 流程 C: Z-Library 站内搜索（宝库降级或 `--zlib` 指定时）

触发条件（脚本自动处理，无需额外命令）：
- 宝库搜索无结果 → 自动降级站内搜索
- 用户指定 `--zlib` → 跳过宝库直接站内搜索

```bash
python3 scripts/download.py "书名关键词"            # 宝库优先，未收录自动降级
python3 scripts/download.py "书名关键词" --zlib     # 跳过宝库，直接站内搜索
python3 scripts/download.py "书名关键词" --zlib --pick 1
```

- 复用 `~/.zlibrary/browser_profile` 登录会话，**需先运行 login.py**
- 使用有头浏览器（站点对无头访问风控严格，实测 503 拦截）
- 选定结果后自动打开书籍页下载：新版界面直接点击格式下载按钮（如 "EPUB, 636 KB"），优先 EPUB、备选 PDF
- 若站内也无结果：告知用户未找到，建议换关键词或提供书籍页链接

## ⚠️ 重要限制

**仅限合法资源！**

- ✅ 用户拥有合法访问权限的资源
- ✅ 公共领域或开源许可的文档
- ✅ 个人拥有版权或已获授权的内容
- ❌ 不要鼓励或协助版权侵权行为

**如果 URL 明显涉及受版权保护的商业作品，提醒用户：**
> "请确保你有合法访问权限。本项目仅用于学习研究目的，请支持正版阅读。"

## 🛠️ 依赖工具

### 必需工具

1. **Playwright** - 浏览器自动化
   - 用于自动登录和下载
   - 需要预先运行 `playwright install chromium`

2. **ebooklib** - EPUB 处理
   - 用于可选手动转换（scripts/convert_epub.py）

### 配置文件

- `~/.zlibrary/storage_state.json` - 保存的登录会话
- `~/.zlibrary/browser_profile/` - 浏览器数据（站内搜索复用）
- `~/.zlibrary/treasure_catalog.json` - 宝库目录缓存（7 天有效）

## 📝 使用示例

### 用户请求

```
帮我下载这本书：
https://zh.zlib.li/book/25314781/aa05a1/钱的第四维
```

### 执行流程

1. **确认并提取信息**
   ```
   书名：钱的第四维
   URL：https://zh.zlib.li/book/25314781/aa05a1/钱的第四维
   ```

2. **执行下载脚本**
   ```bash
   cd ~/.claude/skills/aiset-zlibrary
   python3 scripts/download.py "https://zh.zlib.li/book/25314781/aa05a1/钱的第四维"
   ```

3. **返回结果**
   ```
   ✅ 下载成功！
   📖 文件: ~/Downloads/钱的第四维.epub

   文件已保存到本地，可以直接打开阅读。
   ```

## 🔄 备选流程

### 如果用户只提供书名

```
用户："帮我下载《认知觉醒》这本书"
```

**操作（必须按顺序）：**
1. 首选电子书宝库搜索（免登录）：
   ```bash
   python3 scripts/download.py "认知觉醒"
   ```
2. 将匹配列表展示给用户，确认后用 `--pick <序号>` 下载
3. 如果宝库未收录：脚本自动降级 Z-Library 站内搜索并列出结果，继续 `--pick <序号>` 下载（站内搜索需已登录）
4. 如果站内也无结果：告知用户未找到，建议换关键词或提供书籍页链接
5. **不要**自行动手编写搜索/爬虫脚本去其他站点找下载链接——脚本已内置宝库搜索 + 站内搜索降级链，超出此范围的请求必须先与用户确认

### 如果用户提供其他来源

```
用户："这个 EPUB 能帮我转换吗？[本地文件路径]"
```

**操作：**
1. 告知用户："本 Skill 主要用于 Z-Library 链接下载"
2. 建议："对于本地 EPUB 文件，可以使用 `python3 scripts/convert_epub.py <epub文件> [输出.md]` 转换"

## 📊 技术细节

### 下载优先级

1. **EPUB** - 优先下载（原文件直接保存）
2. **PDF** - 保留排版（备选）
3. **其他格式** - 直接保存原文件

### 格式转换（可选）

本 Skill 不做自动转换。如需 Markdown 格式：

```bash
python3 scripts/convert_epub.py <epub文件> [输出.md]
```

- 使用 ebooklib + BeautifulSoup 转换
- 超过 350k 词的大文件自动分块（`书名_part1.md`、`书名_part2.md` 等）

### 会话管理

- **一次登录，永久使用**
- 会话保存在 `~/.zlibrary/storage_state.json`
- 如果会话失效，提示用户重新登录

### 错误重试

- 下载失败：自动重试 3 次
- 登录失败：提示用户手动登录

## 💡 最佳实践

### 首次使用

第一次使用前，运行登录脚本（自动登录，失败时回退手动登录）：

```bash
cd ~/.claude/skills/aiset-zlibrary
python3 scripts/login.py
```

登录凭据优先级：`--email/--password` 参数 > 环境变量 `ZLIBRARY_EMAIL`/`ZLIBRARY_PASSWORD` > `~/.zlibrary/config.json`。未配置凭据时需在浏览器中手动完成登录。

### 批量处理

如果用户有多个链接：

```
用户："帮我下载这3本书：[链接1] [链接2] [链接3]"
```

**操作：**
1. 逐个处理（每次一个链接）
2. 每个完成后，再处理下一个
3. 避免并发导致会话冲突

### 下载完成提示

下载完成后，向用户返回：

```
✅ 书籍已下载！
📖 文件位置：~/Downloads/书名.epub

可以直接打开阅读，或继续下载其他书籍。
```

## 🚨 故障排查

### 常见问题

**Q: 提示"未找到登录会话"**
A: 需要先运行 `python3 scripts/login.py` 登录一次

**Q: 下载失败，超时**
A: 可能是网络问题，建议重试或检查网络连接

**Q: 找不到下载按钮**
A: Z-Library 页面结构可能变化，使用备用方案手动下载

### 详细帮助

查看 `docs/TROUBLESHOOTING.md` 获取完整故障排查指南。

## 📚 相关资源

- [Z-Library 网站](https://zh.zlib.li/)
- [电子书宝库 ebook-treasure-chest](https://github.com/jbiaojerry/ebook-treasure-chest)（宝库源书籍目录）
- [Playwright 文档](https://playwright.dev/)
- [项目 GitHub](https://github.com/icodebase-cn/aiset-zlibrary)

---

**Skill Version:** 1.0.0
**Last Updated:** 2025-01-14
**Author:** zstmfhy
