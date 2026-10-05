#!/usr/bin/env python3
"""
Convert EPUB to Markdown.
Uses BeautifulSoup for robust HTML parsing.
Large files (>350k words) are automatically split into parts.
"""
import sys
import re
from ebooklib import epub
from pathlib import Path
from bs4 import BeautifulSoup

MAX_WORDS = 350000


def count_words(text):
    """Count words (CJK characters + English words)."""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    return chinese_chars + english_words


def split_markdown_file(file_path, max_words=MAX_WORDS):
    """Split a large Markdown file into smaller parts."""
    print(f"📊 File too large, splitting...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    total_words = count_words(content)
    print(f"   Total words: {total_words:,}")
    print(f"   Max per chunk: {max_words:,} words")

    # Split by chapters (## or ### headings)
    chapters = re.split(r'\n(?=#{1,3}\s)', content)

    chunks = []
    current_chunk = ""
    current_words = 0

    for chapter in chapters:
        chapter_words = count_words(chapter)

        # A single chapter exceeding the limit needs further splitting
        if chapter_words > max_words:
            # Save the current chunk first
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
                current_words = 0

            # Split the large chapter by paragraphs
            paragraphs = chapter.split('\n\n')
            temp_chunk = ""
            temp_words = 0

            for para in paragraphs:
                para_words = count_words(para)
                if temp_words + para_words > max_words and temp_chunk:
                    chunks.append(temp_chunk)
                    temp_chunk = para + "\n\n"
                    temp_words = para_words
                else:
                    temp_chunk += para + "\n\n"
                    temp_words += para_words

            if temp_chunk:
                current_chunk = temp_chunk
                current_words = temp_words

        elif current_words + chapter_words > max_words:
            # Current chunk is full, save and start a new one
            chunks.append(current_chunk)
            current_chunk = chapter + "\n\n"
            current_words = chapter_words
        else:
            # Add to the current chunk
            current_chunk += chapter + "\n\n"
            current_words += chapter_words

    # Save the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    # Write chunk files
    chunk_files = []
    stem = file_path.stem
    for i, chunk in enumerate(chunks, 1):
        chunk_file = file_path.parent / f"{stem}_part{i}.md"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        chunk_files.append(chunk_file)
        chunk_words = count_words(chunk)
        print(f"   ✅ Part {i}/{len(chunks)}: {chunk_words:,} words")

    return chunk_files


def html_to_markdown(soup):
    """Convert BeautifulSoup object to Markdown."""
    markdown_parts = []

    def process_element(element):
        """Recursively process HTML elements."""
        if element.name is None:
            # Text node
            text = str(element).strip()
            if text:
                return text
            return ""

        # Skip certain tags
        if element.name in ['script', 'style', 'nav', 'footer', 'svg']:
            return ""

        # Headings
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(element.name[1])
            text = element.get_text().strip()
            if text:
                return f"\n\n{'#' * level} {text}\n\n"
            return ""

        # Paragraphs
        if element.name == 'p':
            text = element.get_text().strip()
            if text:
                return f"\n\n{text}\n\n"
            return ""

        # Bold
        if element.name in ['b', 'strong']:
            text = element.get_text().strip()
            if text:
                return f"**{text}**"
            return ""

        # Italic
        if element.name in ['i', 'em']:
            text = element.get_text().strip()
            if text:
                return f"*{text}*"
            return ""

        # Code
        if element.name == 'code':
            text = element.get_text().strip()
            if text:
                return f"`{text}`"
            return ""

        # Links
        if element.name == 'a':
            href = element.get('href', '')
            text = element.get_text().strip()
            if href and text:
                return f"[{text}]({href})"
            return element.get_text().strip()

        # Lists
        if element.name == 'ul':
            items = element.find_all('li', recursive=False)
            result = "\n\n"
            for li in items:
                text = li.get_text().strip()
                if text:
                    result += f"- {text}\n"
            return result + "\n"

        if element.name == 'ol':
            items = element.find_all('li', recursive=False)
            result = "\n\n"
            for i, li in enumerate(items, 1):
                text = li.get_text().strip()
                if text:
                    result += f"{i}. {text}\n"
            return result + "\n"

        # Line breaks
        if element.name == 'br':
            return "\n"

        # Default: process children and concatenate
        if element.contents:
            result = ""
            for child in element.contents:
                result += process_element(child)
            return result

        return ""

    # Process body content
    body = soup.find('body')
    if body:
        markdown = process_element(body)
    else:
        markdown = process_element(soup)

    # Clean up whitespace
    markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
    markdown = re.sub(r' +', ' ', markdown)
    markdown = markdown.strip()

    return markdown


def epub_to_markdown(epub_path, output_path):
    """Convert EPUB to Markdown file."""
    print(f"📖 Reading EPUB: {epub_path}")

    try:
        book = epub.read_epub(epub_path)

        # Get metadata
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Unknown Title"
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown Author"

        print(f"📚 Title: {title}")
        print(f"✍️  Author: {author}")
        print(f"📄 Processing chapters...")

        # Start markdown with metadata
        markdown_content = f"# {title}\n\n"
        markdown_content += f"**Author:** {author}\n\n"
        markdown_content += "---\n\n"

        # Extract content from all items
        chapter_count = 0
        for item in book.get_items():
            if item.get_type() == 9:  # ITEM_DOCUMENT = 9
                try:
                    content = item.get_content().decode('utf-8')

                    # Parse HTML with BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    chapter_md = html_to_markdown(soup)

                    # Only add substantial content
                    if len(chapter_md.strip()) > 100:
                        markdown_content += chapter_md
                        markdown_content += "\n\n---\n\n"
                        chapter_count += 1

                except Exception as e:
                    print(f"⚠️  Error processing item: {e}")
                    continue

        # Write to file
        output_path = str(output_path).replace('.txt', '.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        file_size = len(markdown_content)
        print(f"\n✅ Conversion successful!")
        print(f"📁 Output: {output_path}")
        print(f"📊 Characters: {file_size:,}")
        print(f"📖 Chapters: {chapter_count}")
        print(f"📝 Format: Markdown")

        # Auto-split files exceeding the word limit
        word_count = count_words(markdown_content)
        print(f"📊 Word count: {word_count:,}")

        if word_count > MAX_WORDS:
            print(f"⚠️  File exceeds 350k words")
            chunk_files = split_markdown_file(Path(output_path))
            print(f"📦 Split into {len(chunk_files)} chunks")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_epub.py <epub_file> [output_md]")
        print("Note: Files exceeding 350k words are split into parts automatically.")
        sys.exit(1)

    epub_file = sys.argv[1]
    if len(sys.argv) >= 3:
        md_file = sys.argv[2]
    else:
        md_file = Path(epub_file).stem + ".md"

    success = epub_to_markdown(epub_file, md_file)
    sys.exit(0 if success else 1)
