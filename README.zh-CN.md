# 📚 aiset-zlibrary

[English](README.md) | [简体中文](README.zh-CN.md)

> 一键从 Z-Library 自动下载书籍

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

- 🔐 **一次登录，永久使用** - 登录一次后自动复用会话
- 📥 **智能下载** - 优先 EPUB（原文件直接保存），自动降级 PDF（保留排版）
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
用 aiset-zlibrary skill 处理这个 Z-Library 链接：
https://zh.zlib.li/book/25314781/aa05a1/书的标题
```

Claude 会自动：

- 下载书籍（优先 EPUB）
- 保存原文件到 ~/Downloads
- 返回文件路径

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
python3 scripts/download.py "https://zh.zlib.li/book/..."
```

**自动完成：**

- ✅ 使用已保存的会话登录
- ✅ 优先下载 EPUB（原文件直接保存）
- ✅ 自动降级 PDF（保留排版）
- ✅ 文件保存到 ~/Downloads

## 📖 使用示例

### 基本用法

```bash
# 下载单本书籍
python3 scripts/download.py "https://zh.zlib.li/book/12345/..."
```

### 批量处理

```bash
# 批量下载多本书
for url in "url1" "url2" "url3"; do
    python3 scripts/download.py "$url"
done
```

## 🔄 工作流程

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
│   ├── login.py         # 登录脚本
│   ├── download.py      # 下载脚本
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
├── storage_state.json    # 登录会话（cookies）
├── browser_profile/      # 浏览器数据
└── config.json          # 可选登录凭据
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
python3 scripts/download.py <Z-Library URL>
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
- [Playwright](https://playwright.dev/) - 强大的浏览器自动化工具

## 📮 联系方式

- GitHub Issues: [提交问题](https://github.com/icodebase-cn/aiset-zlibrary/issues)
- 讨论区: [GitHub Discussions](https://github.com/icodebase-cn/aiset-zlibrary/discussions)

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
