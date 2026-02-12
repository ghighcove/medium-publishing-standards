#!/usr/bin/env python3
"""
Export markdown article to Medium-compatible HTML with unique timestamped filenames.

This script generates cache-busting filenames to avoid Medium's aggressive caching issue
where it serves old cached content when the same filename is reused.

Usage:
    python scripts/export_for_medium.py article/medium_draft.md
"""

import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

import markdown


def generate_unique_filename(article_name: str, html_content: str) -> str:
    """
    Generate unique timestamped filename to bypass Medium's aggressive caching.

    Format: {article_name}_{YYYYMMDD}_{HHMM}_{hash}.html
    Example: rating_inflation_20260212_0845_a3f2b1c4.html

    Args:
        article_name: Base name for the article (e.g., "rating_inflation")
        html_content: Full HTML content to hash

    Returns:
        Unique filename string
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    content_hash = hashlib.md5(html_content.encode()).hexdigest()[:8]
    return f"{article_name}_{timestamp}_{content_hash}.html"


def markdown_to_html(markdown_content: str, github_pages_base: str, repo_name: str) -> str:
    """
    Convert markdown to Medium-compatible HTML using the markdown library.

    Pre-processes image URLs to use GitHub Pages absolute URLs, then delegates
    all markdown→HTML conversion to the markdown library (handles lists, tables,
    headers, bold, italic, links, etc. correctly).

    Args:
        markdown_content: Raw markdown text
        github_pages_base: Base URL for GitHub Pages (e.g., "https://ghighcove.github.io")
        repo_name: Repository name (e.g., "movie-ratings-analysis")

    Returns:
        HTML body content ready for Medium import
    """
    md_text = markdown_content

    # Pre-process: rewrite image paths to GitHub Pages absolute URLs
    # Pattern: ![caption](../figures/fig.png) or ![caption](figures/fig.png)
    def replace_image_url(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        if img_path.startswith('../'):
            img_path = img_path[3:]
        github_url = f"{github_pages_base}/{repo_name}/{img_path}"
        return f'![{alt_text}]({github_url})'

    md_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image_url, md_text)

    # Convert markdown to HTML using the markdown library
    html = markdown.markdown(
        md_text,
        extensions=['tables', 'fenced_code'],
        output_format='html5'
    )

    # Post-process: ensure images are wrapped in <p> tags (Medium requirement)
    # The markdown library produces <p><img ...></p> by default for standalone images,
    # but verify and fix any bare <img> tags
    html = re.sub(
        r'(?<!<p>)(<img [^>]+>)(?!</p>)',
        r'<p>\1</p>',
        html
    )

    return html


def export_article_for_medium(
    markdown_path: str,
    output_dir: str,
    github_pages_base: str = "https://ghighcove.github.io",
    repo_name: str = "movie-ratings-analysis"
) -> Tuple[str, str]:
    """
    Export markdown article to Medium-compatible HTML with unique filename.

    Args:
        markdown_path: Path to source markdown file
        output_dir: Directory to write HTML file
        github_pages_base: Base URL for GitHub Pages
        repo_name: Repository name for constructing image URLs

    Returns:
        Tuple of (local_file_path, github_pages_url)
    """
    # Read markdown
    markdown_path = Path(markdown_path)
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Convert markdown body to HTML
    html_body = markdown_to_html(markdown_content, github_pages_base, repo_name)

    # Wrap in full HTML document structure (required by Medium importer)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Rating Inflation</title>
</head>
<body>
{html_body}
</body>
</html>"""

    # Generate unique filename
    article_name = markdown_path.stem  # e.g., "medium_draft"
    # Clean up the name if needed
    if article_name == "medium_draft":
        article_name = "rating_inflation"

    filename = generate_unique_filename(article_name, html_content)

    # Write HTML file
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Generate GitHub Pages URL
    github_url = f"{github_pages_base}/{repo_name}/article/{filename}"

    print(f"Exported to: {output_path}")
    print(f"File size: {output_path.stat().st_size:,} bytes")
    print(f"GitHub Pages URL: {github_url}")
    print()
    print("Next steps:")
    print(f"1. git add article/{filename}")
    print(f"2. git commit -m 'Add Medium export: {article_name}'")
    print("3. git push origin main")
    print("4. Wait 30 seconds for GitHub Pages rebuild")
    print("5. Import to Medium using the GitHub Pages URL above")

    return str(output_path), github_url


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/export_for_medium.py <markdown_file>")
        print("Example: python scripts/export_for_medium.py article/medium_draft.md")
        sys.exit(1)

    markdown_path = sys.argv[1]
    output_dir = "article"

    export_article_for_medium(markdown_path, output_dir)


if __name__ == '__main__':
    main()
