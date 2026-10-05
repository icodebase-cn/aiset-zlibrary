# 📚 aiset-zlibrary

[English](README.md) | [简体中文](README.zh-CN.md)

> Automatically download books from Z-Library with one command.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-success.svg)](https://claude.ai/claude-code)

---

## ⚠️ Important Disclaimer

**This project is for educational, research, and technical demonstration purposes only. Please strictly comply with local laws and copyright regulations. Use only for:**

- ✅ Resources you have legal access to
- ✅ Public domain or open-source licensed documents (e.g., arXiv, Project Gutenberg)
- ✅ Content you personally own or have authorization to use

**The author does not encourage or support any form of copyright infringement and assumes no legal liability. Use at your own risk.**

**Please respect intellectual property rights and support authorized reading!**

---

## ✨ Features

- 🔐 **One-time Login, Forever Use** - Log in once and reuse the saved session
- 📥 **Smart Download** - Prioritizes EPUB (original file), auto-fallback to PDF (preserves formatting)
- 🛠️ **Optional Converter** - Standalone EPUB → Markdown script with auto-chunking (>350k words)
- 🤖 **Fully Automated** - Complete workflow with a single command
- 🎯 **Format Adaptive** - Automatically detects and processes multiple formats (PDF, EPUB, MOBI, etc.)
- 📊 **Visual Progress** - Real-time display of download and conversion progress

## 🎯 Use as Claude Skill (Recommended)

### Installation

```bash
# 1. Navigate to Claude Skills directory
cd ~/.claude/skills  # Windows: %APPDATA%\Claude\skills

# 2. Clone the repository
git clone https://github.com/icodebase-cn/aiset-zlibrary.git aiset-zlibrary

# 3. Complete initial login
cd aiset-zlibrary
python3 scripts/login.py
```

### Usage

After installation, simply tell Claude Code:

```text
Use aiset-zlibrary skill to process this Z-Library link:
https://zh.zlib.li/book/25314781/aa05a1/book-title
```

Claude will automatically:

- Download the book (prioritizing EPUB)
- Save the original file to ~/Downloads
- Return the file path

---

## 🛠️ Traditional Installation

### 1. Install Dependencies

```bash
# Clone repository
git clone https://github.com/icodebase-cn/aiset-zlibrary.git
cd aiset-zlibrary

# Install Python dependencies
pip install playwright ebooklib

# Install Playwright browser
playwright install chromium
```

### 2. Login to Z-Library (One-time Only)

```bash
python3 scripts/login.py
```

**Steps:**
1. Browser will automatically open and visit Z-Library
2. Automatic login using credentials from `--email/--password`, env vars `ZLIBRARY_EMAIL`/`ZLIBRARY_PASSWORD`, or `~/.zlibrary/config.json`
3. If no credentials are configured or auto-login fails (e.g. captcha), log in manually in the browser and press **ENTER**
4. Session saved!

### 3. Download Books

```bash
python3 scripts/download.py "https://zh.zlib.li/book/..."
```

**Automatically completes:**

- ✅ Login using saved session
- ✅ Download EPUB (original file)
- ✅ Fallback to PDF (preserves formatting)
- ✅ Save files to ~/Downloads

## 📖 Usage Examples

### Basic Usage

```bash
# Download single book
python3 scripts/download.py "https://zh.zlib.li/book/12345/..."
```

### Batch Processing

```bash
# Batch download multiple books
for url in "url1" "url2" "url3"; do
    python3 scripts/download.py "$url"
done
```

## 🔄 Workflow

```text
Z-Library URL
    ↓
1. Launch browser (using saved session)
    ↓
2. Visit book page
    ↓
3. Smart format selection:
   - Priority: EPUB (original file)
   - Fallback: PDF (preserves formatting)
   - Other formats (save directly)
    ↓
4. Download to ~/Downloads
    ↓
5. Return file path ✅
```

## 📁 Project Structure

```text
aiset-zlibrary/
├── SKILL.md              # Core Skill definition (required)
├── README.md             # Project documentation
├── README.zh-CN.md       # Chinese documentation
├── LICENSE               # MIT License
├── package.json          # npm config (for Claude Code skill)
├── skill.yaml            # Skill configuration
├── requirements.txt      # Python dependencies
├── scripts/              # Executable scripts (official standard)
│   ├── login.py         # Login script
│   ├── download.py      # Download script
│   └── convert_epub.py  # EPUB conversion tool
├── docs/                 # Documentation
│   ├── WORKFLOW.md      # Workflow details
│   └── TROUBLESHOOTING.md # Troubleshooting guide
└── INSTALL.md            # Installation guide
```

## 🔧 Configuration

Configurations are saved in `~/.zlibrary/` directory; credentials can also be provided via environment variables (priority: `--email/--password` > env vars > `config.json`):

```text
~/.zlibrary/
├── storage_state.json    # Login session (cookies)
├── browser_profile/      # Browser data
└── config.json          # Optional login credentials
```

```bash
# Environment variables (Linux / macOS)
export ZLIBRARY_EMAIL="your@email.com"
export ZLIBRARY_PASSWORD="your-password"
```

```powershell
# Environment variables (Windows PowerShell)
$env:ZLIBRARY_EMAIL = "your@email.com"
$env:ZLIBRARY_PASSWORD = "your-password"
```

## 🛠️ Dependencies

- **Python 3.8+**
- **playwright** - Browser automation
- **ebooklib** - EPUB file processing (for the optional converter)

## 📝 Command Reference

### Login

```bash
python3 scripts/login.py
```

### Download

```bash
python3 scripts/download.py <Z-Library URL>
```

### Convert to Markdown (Optional)

```bash
python3 scripts/convert_epub.py <epub_file> [output.md]
```

### Check Session Status

```bash
ls -lh ~/.zlibrary/storage_state.json
```

### Re-login

```bash
rm ~/.zlibrary/storage_state.json
python3 scripts/login.py
```

## 🛠️ Manual Conversion (Optional)

Convert a downloaded EPUB to Markdown:

```bash
python3 scripts/convert_epub.py "~/Downloads/book.epub"
```

✅ **Automatic File Chunking**:
- After conversion, word count is detected automatically
- Files exceeding 350,000 words are automatically split into multiple smaller files
- Smart chapter-based splitting preserves content integrity

**Example**:
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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [Z-Library](https://zh.zlib.li/) - World's largest digital library
- [Playwright](https://playwright.dev/) - Powerful browser automation tool

## 📮 Contact

- GitHub Issues: [Submit issues](https://github.com/icodebase-cn/aiset-zlibrary/issues)
- Discussions: [GitHub Discussions](https://github.com/icodebase-cn/aiset-zlibrary/discussions)

---

**⭐ If this project helps you, please give it a Star!**
