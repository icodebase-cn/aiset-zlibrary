# 故障排查指南

本文档帮助您解决使用 aiset-zlibrary Skill 时可能遇到的常见问题。

---

## 🔐 登录问题

### 问题：未找到登录会话

**症状：**
```
❌ 未找到会话状态
💡 请先运行: python3 scripts/login.py
```

**解决方案：**

1. **首次使用需要登录**
   ```bash
   cd ~/.claude/skills/aiset-zlibrary
   python3 scripts/login.py
   ```

2. **登录步骤：**
   - 浏览器会自动打开 Z-Library
   - 自动使用已配置凭据登录（优先级: --email/--password > 环境变量 ZLIBRARY_EMAIL/ZLIBRARY_PASSWORD > config.json）
   - 如未配置凭据或自动登录失败（需要验证码等），在浏览器中手动完成登录，按 ENTER 键
   - 会话已保存！

3. **验证登录状态：**
   ```bash
   ls -lh ~/.zlibrary/storage_state.json
   ```
   应该显示一个约 2KB 的文件

### 问题：登录失败

**症状：**
- 浏览器打开但无法登录
- 提示"网络错误"

**解决方案：**

1. **检查网络连接**
   ```bash
   ping -c 3 zh.zlib.li
   ```

2. **尝试备用域名**
   - https://zh.zlib.li/
   - https://z-lib.org/
   - https://zlibrary.org/

3. **清除缓存重试**
   ```bash
   rm ~/.zlibrary/storage_state.json
   python3 scripts/login.py
   ```

---

## 📥 下载问题

### 问题：找不到下载按钮

**症状：**
```
❌ 未找到下载按钮
```

**可能原因：**
1. Z-Library 页面结构变化
2. 需要登录
3. 网络问题

**解决方案：**

1. **检查登录状态**
   ```bash
   ls ~/.zlibrary/storage_state.json
   ```

2. **手动打开页面确认**
   - 复制链接到浏览器打开
   - 确认能正常访问和下载

3. **使用备用方案**
   - 手动下载 PDF 到 `~/Downloads/`，直接阅读使用

### 问题：下载超时

**症状：**
```
⏳ 等待超时
❌ 下载失败
```

**解决方案：**

1. **检查网络稳定性**
   ```bash
   # 测试连接
   curl -I https://zh.zlib.li
   ```

2. **增加等待时间**
   - 脚本默认等待 60 秒
   - 如果网络慢，可能需要更长时间

3. **重试下载**
   ```bash
   # 重新运行
   python3 scripts/download.py "你的链接"
   ```

### 问题：转换超时

**症状：**
```
⚠️ 转换超时，尝试继续...
```

**解决方案：**

1. **这是正常现象**
   - Z-Library 需要时间转换格式
   - 最长可能需要 60 秒

2. **耐心等待**
   - 脚本会自动检测转换完成
   - 完成后会自动开始下载

3. **如果持续超时**
   - 尝试刷新页面重试
   - 选择其他格式（如直接 PDF）

---

## 🔧 技术问题

### 问题：Playwright 未安装

**症状：**
```
ModuleNotFoundError: No module named 'playwright'
```

**解决方案：**

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **安装浏览器**
   ```bash
   playwright install chromium
   ```

3. **验证安装**
   ```bash
   python3 -c "import playwright; print(playwright.__version__)"
   ```

### 问题：EPUB 转换失败（手动转换时）

**症状：**
```
❌ Error: ...
```

**解决方案：**

1. **检查 EPUB 文件**
   ```bash
   # 确认文件存在
   ls -lh ~/Downloads/*.epub
   ```

2. **重新执行转换**
   ```bash
   python3 scripts/convert_epub.py "EPUB路径" "输出路径.md"
   ```

3. **使用 PDF 代替**
   - PDF 格式兼容性更好
   - 无需转换，直接使用

### 问题：浏览器崩溃

**症状：**
```
Browser crashed: ...
```

**解决方案：**

1. **更新 Playwright**
   ```bash
   pip install --upgrade playwright
   playwright install chromium --force
   ```

2. **使用无头模式（可能更稳定）**
   - 修改脚本中的 `headless=False` 为 `headless=True`

3. **检查系统资源**
   ```bash
   # 检查内存使用
   top
   ```

---

## 📊 配置问题

### 问题：会话频繁失效

**症状：**
- 每次运行都需要重新登录
- 提示"未找到会话状态"

**解决方案：**

1. **检查文件权限**
   ```bash
   ls -l ~/.zlibrary/storage_state.json
   ```
   应该显示 `-rw-------` (600)

2. **修复权限**
   ```bash
   chmod 600 ~/.zlibrary/storage_state.json
   ```

3. **重新生成会话**
   ```bash
   rm ~/.zlibrary/storage_state.json
   python3 scripts/login.py
   ```

### 问题：下载目录不正确

**症状：**
- 文件下载到未知位置
- 找不到下载的文件

**解决方案：**

1. **默认下载目录**
   - macOS/Linux: `~/Downloads/`
   - Windows: `%USERPROFILE%/Downloads/`

2. **查找最近下载的文件**
   ```bash
   # 查找最近的 PDF/EPUB
   ls -lt ~/Downloads/*.{pdf,epub} 2>/dev/null | head -5
   ```

3. **自定义下载目录**
   - 修改脚本中的 `downloads_dir` 变量

---

## 🌐 网络问题

### 问题：无法访问 Z-Library

**症状：**
```
Failed to connect to github.com port 443
```

**解决方案：**

1. **检查 DNS**
   ```bash
   # 查看是否为 Z-Library 域名解析问题
   nslookup zh.zlib.li
   ```

2. **尝试备用域名**
   - https://zh.zlib.li/
   - https://z-lib.org/
   - https://zlibrary.org/

3. **检查代理设置**
   - 如果使用 VPN，尝试切换节点
   - 或暂时关闭 VPN

4. **使用镜像站点**（如果有）

---

## 📝 使用问题

### 问题：Claude 无法识别 Skill

**症状：**
- 在 Claude Code 中提到 Skill，但 Claude 不知道如何使用

**解决方案：**

1. **确认 SKILL.md 存在**
   ```bash
   ls -l ~/.claude/skills/aiset-zlibrary/SKILL.md
   ```

2. **检查文件权限**
   ```bash
   chmod 644 ~/.claude/skills/aiset-zlibrary/SKILL.md
   ```

3. **重启 Claude Code**
   - 完全退出 Claude Code
   - 重新打开
   - 让 Claude 重新加载 Skills

4. **使用完整触发词**
   - 提及 Z-Library 链接
   - 明确说"下载这本书"

---

## 🆘 仍然无法解决？

### 收集诊断信息

在寻求帮助前，请收集以下信息：

1. **系统信息**
   ```bash
   python3 --version
   uname -a  # macOS/Linux
   # 或 Windows: systeminfo
   ```

2. **依赖版本**
   ```bash
   pip list | grep -E "playwright|ebooklib"
   ```

3. **错误日志**
   - 运行时的完整错误信息
   - 截图（如果可能）

4. **复现步骤**
   - 你做了什么操作
   - 预期结果是什么
   - 实际结果是什么

### 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/icodebase-cn/aiset-zlibrary/issues)
- **查看文档**: [README.md](README.md)
- **检查 SKILL.md**: [SKILL.md](SKILL.md)

---

## 💡 最佳实践

### 避免常见问题

1. **定期检查登录状态**
   ```bash
   # 每周检查一次
   ls -lh ~/.zlibrary/storage_state.json
   ```

2. **保持依赖更新**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **使用合法资源**
   - 只下载你有权限的内容
   - 遵守当地法律法规

4. **批量处理时添加延迟**
   ```bash
   # 避免请求过快
   for url in "url1" "url2" "url3"; do
       python3 scripts/download.py "$url"
       sleep 5  # 等待 5 秒
   done
   ```

---

**文档版本**: 1.0.0
**最后更新**: 2025-01-14
