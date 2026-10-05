---
name: aiset-zlibrary
description: 自动从 Z-Library 下载书籍（优先 EPUB，备选 PDF），保存原始文件，不做自动转换。
---

# aiset-zlibrary Skill

让 Claude 帮你从 Z-Library 自动下载书籍，优先 EPUB、备选 PDF，下载后直接保存原文件。

## 🎯 核心功能

- 一键下载书籍（优先 EPUB，备选 PDF）
- 下载后直接保存原文件（不自动转换）
- 可选手动转换：EPUB → Markdown（大文件自动分块）

## 📋 激活条件（Triggers）

当用户提到以下需求时，使用此 Skill：

- 用户提供 Z-Library 书籍链接（包含 `zlib.li`、`z-lib.org`、`zh.zlib.li` 等域名）
- 用户说"帮我下载这本书"
- 用户说"自动下载并读这本书"
- 用户说"把这个 Z-Library 链接的书籍下载下来"
- 用户要求从特定 URL 下载书籍

## 🔧 核心指令

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
- 如果登录失败，提示用户运行 `python3 ~/.claude/skills/aiset-zlibrary/scripts/login.py`
- 如果下载失败，提供故障排查建议

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
- `~/.zlibrary/browser_profile/` - 浏览器数据

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

**操作：**
1. 询问："请问有 Z-Library 的链接吗？"
2. 如果有链接，执行标准流程
3. 如果没有链接，提示："请提供 Z-Library 书籍页面链接，我可以帮你自动下载"

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

第一次使用前，确保用户已完成登录：

```bash
cd ~/.claude/skills/aiset-zlibrary
python3 scripts/login.py
```

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
- [Playwright 文档](https://playwright.dev/)
- [项目 GitHub](https://github.com/zstmfhy/aiset-zlibrary)

---

**Skill Version:** 1.0.0
**Last Updated:** 2025-01-14
**Author:** zstmfhy
