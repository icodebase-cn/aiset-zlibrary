# 安装指南

## 系统要求

- Python 3.8 或更高版本
- macOS / Linux / Windows
- 网络连接

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/icodebase-cn/aiset-zlibrary.git
cd aiset-zlibrary
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 4. 配置登录凭据（可选）

配置凭据后可自动登录（省去手动操作）。凭据按以下优先级读取：

1. 命令行参数: `--email` / `--password`
2. 环境变量: `ZLIBRARY_EMAIL` / `ZLIBRARY_PASSWORD`
3. 配置文件: `~/.zlibrary/config.json`（格式：`{"email": "...", "password": "..."}`）

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

未配置凭据时，登录脚本会在浏览器中打开页面，手动登录即可。

## 验证安装

```bash
# 测试登录脚本（不会实际登录）
python3 scripts/login.py --help

# 测试下载脚本（不会实际下载）
python3 scripts/download.py --help
```

## 故障排除

### Playwright 安装失败

```bash
# 手动下载浏览器
playwright install --with-deps chromium
```

### Python 版本问题

```bash
# 使用 pyenv 安装 Python 3.8+
pyenv install 3.11.0
pyenv global 3.11.0
```

### 权限问题

```bash
# macOS/Linux: 添加执行权限
chmod +x scripts/*.py
```

## 下一步

安装完成后，请查看 [快速开始](README.md#快速开始)
