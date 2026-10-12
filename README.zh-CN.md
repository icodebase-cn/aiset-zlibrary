# 📚 aiset-zlibrary

[English](README.md) | [简体中文](README.zh-CN.md)

> 一键自动下载书籍：Z-Library + 电子书宝库（ebook-treasure-chest）双源支持

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-success.svg)](https://claude.ai/claude-code)

---

## ⚠️ 重要免责声明

**本项目仅供学习、研究和技术演示用途。请严格遵守当地法律法规及版权规定，仅用于：**

- ✅ 你拥有合法访问权限的资源
- ✅ 公共领域或开源许可的文档（如 arXiv、Project Gutenberg）
- ✅ 个人拥有版权或已获授权的内容

**作者不鼓励、不支持任何形式的版权侵权行为，不承担任何法律责任。使用风险自负。**

**请尊重知识产权，支持正版阅读！**

---

## ✨ 特性

- 🔐 **一次登录，永久使用** - 登录一次后自动复用会话（Z-Library 源）
- 📥 **智能下载** - 优先 EPUB（原文件直接保存），自动降级 PDF（保留排版）
- 🏮 **电子书宝库源** - 集成 [ebook-treasure-chest](https://github.com/jbiaojerry/ebook-treasure-chest) 目录（2.4万+ 中文书籍），支持关键词搜索，城通网盘免登录下载
- 🔎 **站内搜索兜底** - 宝库未收录时自动降级 Z-Library 站内搜索（复用登录会话），无需手动找链接
- 🛠️ **可选转换** - 独立 EPUB→Markdown 转换脚本，大文件自动分块（>350k 词）
- 🤖 **全自动化** - 一条命令完成整个流程
- 🎯 **格式自适应** - 自动检测并处理多种格式（PDF、EPUB、MOBI 等）
- 📊 **进度可视化** - 实时显示下载和转换进度

## 🎯 作为 Claude Skill 使用（推荐）

### 安装

```bash
# 1. 进入 Claude Skills 目录
cd ~/.claude/skills  # Windows: %APPDATA%\Claude\skills

# 2. 克隆仓库
git clone https://github.com/icodebase-cn/aiset-zlibrary.git aiset-zlibrary

# 3. 完成首次登录
cd aiset-zlibrary
python3 scripts/login.py
```

### 使用方式

安装后，在 Claude Code 中直接说：

```text
# 场景一：有 Z-Library 链接
用 aiset-zlibrary skill 处理这个链接：
https://zh.zlib.li/book/25314781/aa05a1/书的标题

# 场景二：只有书名（宝库优先，未收录自动降级 Z-Library 站内搜索）
用 aiset-zlibrary skill 帮我下载《流畅的Python》
```

Claude 会自动：

- 根据输入路由下载源（Z-Library 链接 → Z-Library；书名 → 宝库搜索 → 未收录自动降级站内搜索）
- 搜索命中多条时列出结果让你选择
- 下载并保存原文件到 ~/Downloads，返回文件路径

---

## 🛠️ 传统方式安装

### 1. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/icodebase-cn/aiset-zlibrary.git
cd aiset-zlibrary

# 安装 Python 依赖
pip install playwright ebooklib

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 登录 Z-Library（仅需一次）

```bash
python3 scripts/login.py
```

**操作步骤：**

1. 浏览器会自动打开并访问 Z-Library
2. 使用 `--email/--password` 参数、环境变量 `ZLIBRARY_EMAIL`/`ZLIBRARY_PASSWORD` 或 `~/.zlibrary/config.json` 中的凭据自动登录
3. 若未配置凭据或自动登录失败（如需要验证码），在浏览器中手动完成登录后按 **ENTER**
4. 会话状态已保存！

### 3. 下载书籍

```bash
# 方式一：Z-Library 链接下载（需先完成上面的登录）
python3 scripts/download.py "https://zh.zlib.li/book/..."

# 方式二：电子书宝库关键词搜索下载（免登录，无需 Z-Library 账号）
python3 scripts/download.py "书名关键词"
```

详细用法见下方[使用方法](#-使用方法)。

## 📖 使用方法

所有下载都通过 `scripts/download.py` 一个入口完成，脚本根据输入**自动路由下载源**：

| 你手里有什么 | 直接输入 | 下载源 | 需要登录？ |
| --- | --- | --- | --- |
| Z-Library 书籍页链接 | 完整 URL | Z-Library | ✅ 仅首次 |
| 书名或作者关键词 | 关键词文字 | 电子书宝库 → 未收录自动降级 Z-Library 站内搜索 | 宝库免登录 / 降级需登录 |
| 城通网盘链接 | `ctfile.com` URL | 电子书宝库 | ❌ 免登录 |

### 场景 1：有 Z-Library 链接

```bash
python3 scripts/download.py "https://zh.zlib.li/book/12345/..."
```

自动完成：会话登录 → 优先 EPUB（自动降级 PDF）→ 保存到 ~/Downloads。

### 场景 2：只有书名（推荐，免登录）

**第 1 步**，用关键词搜索宝库目录：

```bash
python3 scripts/download.py "流畅的Python"
```

输出匹配结果列表：

```text
✅ 使用本地缓存目录（共 24071 本，0 天前更新，--refresh 可刷新）
🔍 找到与「流畅的Python」匹配的书籍:
  [1] 流畅的Python | Luciano Ramalho | epub/mobi/azw3 | 编程
  [2] 流畅的Python | Luciano Ramalho | epub/mobi/azw3 | Python

💡 多个结果时使用 --pick 序号 选择下载，例如: python3 scripts/download.py "流畅的Python" --pick 1
```

**第 2 步**，选定序号下载：

```bash
python3 scripts/download.py "流畅的Python" --pick 1
```

下载过程（免费通道限速，脚本每 10 秒刷新进度）：

```text
📖 已选择: 流畅的Python
⬇️  已点击普通下载，页内下载任务启动（免费通道限速，请耐心等待）...
   ⏳ [10s] 1 个未完成 · 2%
   ⏳ [20s] 1 个未完成 · 5%
   ...
✅ 下载成功!
   文件: 2653-流畅的Python.zip
   路径: ~/Downloads/2653-流畅的Python.zip
   大小: 31.4 MB
💡 宝库文件为 zip 压缩包，解压后可得 epub/mobi/azw3。
```

> 💡 唯一匹配时自动开始下载，无需 `--pick`；交互终端下也可直接输入序号。

### 场景 2b：宝库未收录，自动降级 Z-Library 站内搜索

宝库未收录的书（如《纳瓦尔宝典》）无需手动找链接，脚本自动降级站内搜索：

```bash
python3 scripts/download.py "纳瓦尔宝典" --pick 1
```

实际输出：

```text
✅ 使用本地缓存目录（共 24071 本，0 天前更新，--refresh 可刷新）
ℹ️  宝库未收录「纳瓦尔宝典」，自动降级 Z-Library 站内搜索...
✅ 找到 39 条结果（显示前 10 条）:
  [1] 纳瓦尔宝典：财富与幸福指南 = The Almanack of Naval Ravikant...
      [美] 埃里克 · 乔根森 (Eric Jorgenson) 著; 赵灿 译 | epub | 2022 | 中文 | 636 KB
  ...
📖 已选择: 纳瓦尔宝典：财富与幸福指南 ...
📱 检测到新版界面（1 个直接下载按钮）
✅ 选择下载按钮: EPUB, 636 KB
✅ 下载成功!
   大小: 636.0 KB
```

> 💡 站内搜索复用登录会话（需先运行 `login.py`）；也可加 `--zlib` 跳过宝库直接站内搜索。站点对无头访问风控严格，脚本自动使用有头浏览器。

### 场景 3：有城通网盘链接（免登录直下）

```bash
python3 scripts/download.py "https://url89.ctfile.com/f/31084289-xxxx-xxxx?p=8866"
```

### 宝库源说明与参数

- 首次搜索会自动拉取宝库目录（约 2.4 万本）并缓存到 `~/.zlibrary/treasure_catalog.json`（7 天有效，`--refresh` 强制刷新）
- 多关键词用空格分隔（AND 关系），如 `python3 scripts/download.py "Python 数据分析"`
- 下载文件为 **zip 压缩包**，解压可得 epub/mobi/azw3；免费通道限速（约 60KB/s），大文件需数分钟到数十分钟

| 参数 | 说明 |
| --- | --- |
| `--pick N` | 非交互选择搜索结果序号 |
| `--limit N` | 搜索结果显示数量（默认 10） |
| `--zlib` | 跳过宝库，直接 Z-Library 站内搜索（默认宝库优先，未收录自动降级） |
| `--refresh` | 强制刷新目录缓存（默认缓存 7 天） |
| `--catalog <路径>` | 手动指定本地 `all-books.json`（无法访问 GitHub 时） |
| `--headed` | 有头模式运行浏览器（调试用） |

> ⚠️ 宝库 zip 解压出的 epub 如需转 Markdown，执行 `python3 scripts/convert_epub.py "<epub文件>"`（见下方手动转换）。

### 批量处理

```bash
# 批量下载多本书
for url in "url1" "url2" "url3"; do
    python3 scripts/download.py "$url"
done
```

## 🔄 工作流程

### Z-Library 源

```text
Z-Library URL
    ↓
1. 启动浏览器（使用已保存的会话）
    ↓
2. 访问书籍页面
    ↓
3. 智能选择格式：
   - 优先 EPUB（保存原文件）
   - 备选 PDF（保留排版）
   - 其他格式（直接保存）
    ↓
4. 下载文件到 ~/Downloads
    ↓
5. 返回文件路径 ✅
```

### 电子书宝库源

```text
关键词 或 ctfile 链接
    ↓
1. 加载目录（本地缓存 7 天，远端自动回退）
    ↓
2. 关键词搜索（书名/作者/分类）
    ↓
3. --pick 序号选择（或唯一结果自动选择）
    ↓
4. 无头浏览器打开城通网盘页面，点击「普通下载」
    ↓
5. 页内下载（限速，每 10 秒刷新进度）
    ↓
6. 保存 zip 到 ~/Downloads（内含 epub/mobi/azw3）✅
```

### Z-Library 站内搜索（宝库未收录自动降级 / `--zlib` 指定）

```text
宝库无结果（或 --zlib）
    ↓
1. 启动有头浏览器（复用登录会话，无头会被风控拦截）
    ↓
2. 访问站内搜索页，解析 z-bookcard 结果（过滤已删除）
    ↓
3. --pick 序号选择 → 打开书籍页
    ↓
4. 点击格式下载按钮（如 "EPUB, 636 KB"，EPUB 优先）
    ↓
5. 下载保存到 ~/Downloads ✅
```

## 📁 项目结构

```text
aiset-zlibrary/
├── SKILL.md              # Skill 核心定义（必需）
├── README.md             # 英文项目文档
├── README.zh-CN.md       # 中文项目文档
├── LICENSE               # MIT 许可证
├── package.json          # npm 配置（用于 Claude Code skill）
├── skill.yaml            # Skill 定义
├── requirements.txt      # Python 依赖
├── scripts/              # 可执行脚本（官方标准）
│   ├── download.py      # 下载入口（自动路由双源）
│   ├── treasure.py      # 电子书宝库源
│   ├── zlib_search.py   # Z-Library 站内搜索（降级兜底）
│   ├── login.py         # Z-Library 登录脚本
│   └── convert_epub.py  # EPUB 转换工具
├── docs/                 # 文档
│   ├── WORKFLOW.md      # 工作流程详解
│   └── TROUBLESHOOTING.md # 故障排除
└── INSTALL.md            # 安装指南
```

## 🔧 配置文件

配置保存在 `~/.zlibrary/` 目录；凭据也可通过环境变量提供（优先级: `--email/--password` 参数 > 环境变量 > `config.json`）：

```text
~/.zlibrary/
├── storage_state.json    # Z-Library 登录会话（cookies）
├── browser_profile/      # 浏览器数据
├── treasure_catalog.json # 宝库书籍目录缓存（7 天自动刷新）
└── config.json           # 可选登录凭据
```

```bash
# 环境变量（Linux / macOS）
export ZLIBRARY_EMAIL="your@email.com"
export ZLIBRARY_PASSWORD="your-password"
```

```powershell
# 环境变量（Windows PowerShell）
$env:ZLIBRARY_EMAIL = "your@email.com"
$env:ZLIBRARY_PASSWORD = "your-password"
```

## 🛠️ 依赖项

- **Python 3.8+**
- **playwright** - 浏览器自动化
- **ebooklib** - EPUB 文件处理（供可选手动转换使用）

## 📝 命令参考

### 登录

```bash
python3 scripts/login.py
```

### 下载

```bash
# Z-Library 源（需先登录）
python3 scripts/download.py <Z-Library URL>

# 电子书宝库源（免登录）
python3 scripts/download.py "<书名/作者关键词>" [--pick N]
python3 scripts/download.py <城通网盘 ctfile 链接>

# Z-Library 站内搜索（宝库未收录自动降级；--zlib 跳过宝库）
python3 scripts/download.py "纳瓦尔宝典" --pick 1
python3 scripts/download.py "<关键词>" --zlib [--pick N]
```

### 转换为 Markdown（可选）

```bash
python3 scripts/convert_epub.py <epub文件> [输出.md]
```

### 查看会话状态

```bash
ls -lh ~/.zlibrary/storage_state.json
```

### 重新登录

```bash
rm ~/.zlibrary/storage_state.json
python3 scripts/login.py
```

## 🛠️ 手动转换（可选）

将已下载的 EPUB 转换为 Markdown：

```bash
python3 scripts/convert_epub.py "~/Downloads/书名.epub"
```

✅ **自动文件分块**：
- 转换后脚本会自动检测词数
- 超过 350,000 词的文件会自动分割成多个小文件
- 按章节智能分割，保持内容完整性

**示例**：
```bash
📊 Word count: 2,700,000
⚠️  File exceeds 350k words
📊 File too large, splitting...
   Total words: 2,700,000
   Max per chunk: 350,000 words
   ✅ Part 1/8: 342,000 words
   ✅ Part 2/8: 338,000 words
   ...
📦 Split into 8 chunks
```

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Z-Library](https://zh.zlib.li/) - 世界上最大的数字图书馆
- [ebook-treasure-chest](https://github.com/jbiaojerry/ebook-treasure-chest) - 电子书宝库书籍目录
- [Playwright](https://playwright.dev/) - 强大的浏览器自动化工具

## 📮 联系方式

- GitHub Issues: [提交问题](https://github.com/icodebase-cn/aiset-zlibrary/issues)
- 讨论区: [GitHub Discussions](https://github.com/icodebase-cn/aiset-zlibrary/discussions)

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
